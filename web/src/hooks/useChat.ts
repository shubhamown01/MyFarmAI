'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, ApiError } from '@/lib/api/client';
import { ChatResponse, ChatMessage } from '@/lib/api/types';

const CHAT_STORAGE_KEY = 'myfarmai_chat_v1';
const MAX_PERSISTED_MESSAGES = 60;

interface StoredConversation {
  messages: ChatMessage[];
  conversationId: string | null;
}

interface SendContext {
  tempId: string;
}

function createId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function readStoredConversation(): StoredConversation {
  if (typeof window === 'undefined') {
    return { messages: [], conversationId: null };
  }

  try {
    const raw = window.sessionStorage.getItem(CHAT_STORAGE_KEY);
    if (!raw) return { messages: [], conversationId: null };

    const parsed = JSON.parse(raw) as {
      messages?: Array<Omit<ChatMessage, 'timestamp'> & { timestamp: string }>;
      conversationId?: string | null;
    };

    const messages = Array.isArray(parsed.messages)
      ? parsed.messages
          .filter(
            (message) =>
              message &&
              typeof message.id === 'string' &&
              (message.role === 'user' || message.role === 'assistant') &&
              typeof message.content === 'string'
          )
          .map((message) => ({ ...message, timestamp: new Date(message.timestamp) }))
          .slice(-MAX_PERSISTED_MESSAGES)
      : [];

    return {
      messages,
      conversationId: typeof parsed.conversationId === 'string' ? parsed.conversationId : null,
    };
  } catch {
    return { messages: [], conversationId: null };
  }
}

function formatChatError(error: unknown) {
  if (error instanceof ApiError) {
    if (error.code === 'NETWORK_ERROR') {
      return 'The assistant could not be reached. Check your connection and try again.';
    }
    if (error.code === 'TIMEOUT') {
      return 'The assistant took too long to respond. Try a shorter question.';
    }
    return error.message;
  }
  return 'The assistant could not answer that question. Please try again.';
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);
  const inFlightRef = useRef(false);
  const hydratedRef = useRef(false);
  const queryClient = useQueryClient();

  // Restore the short-lived conversation after navigation. We deliberately use
  // sessionStorage instead of localStorage: conversations shouldn't linger
  // indefinitely on a shared device.
  useEffect(() => {
    if (hydratedRef.current) return;
    hydratedRef.current = true;
    const stored = readStoredConversation();
    setMessages(stored.messages);
    setConversationId(stored.conversationId);
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (!isHydrated || typeof window === 'undefined') return;

    const payload: StoredConversation = {
      messages: messages.slice(-MAX_PERSISTED_MESSAGES),
      conversationId,
    };
    window.sessionStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(payload));
  }, [messages, conversationId, isHydrated]);

  const sendMessageMutation = useMutation<ChatResponse, Error, { message: string; conversationId?: string; context?: { language?: string; crop?: string; location?: string } }, SendContext>({
    mutationFn: (variables) =>
      apiClient.sendMessage(variables.message, variables.conversationId, variables.context),
    onMutate: (variables) => {
      inFlightRef.current = true;
      setError(null);
      const tempId = `temp-${createId()}`;
      const optimisticMessage: ChatMessage = {
        id: tempId,
        role: 'user',
        content: variables.message,
        timestamp: new Date(),
        conversationId: variables.conversationId || conversationId || '',
      };
      setMessages((previous) => [...previous, optimisticMessage]);
      return { tempId };
    },
    onSuccess: (response, _variables, context) => {
      setMessages((previous) => {
        const withoutOptimistic = previous.filter((message) => message.id !== context?.tempId);
        return [
          ...withoutOptimistic,
          ...previous
            .filter((message) => message.id === context?.tempId)
            .map((message) => ({ ...message, conversationId: response.conversation_id })),
          {
            id: createId(),
            role: 'assistant',
            content: response.response,
            timestamp: new Date(),
            conversationId: response.conversation_id,
          },
        ];
      });
      setConversationId(response.conversation_id);
      setError(null);
    },
    onError: (mutationError, _variables, context) => {
      setMessages((previous) => previous.filter((message) => message.id !== context?.tempId));
      setError(formatChatError(mutationError));
      if (mutationError instanceof ApiError && mutationError.status === 404) {
        setConversationId(null);
        queryClient.removeQueries({ queryKey: ['chat'] });
      }
    },
    onSettled: () => {
      inFlightRef.current = false;
    },
  });

  const sendMessage = useCallback(
    async (message: string, context?: { language?: string; crop?: string; location?: string }) => {
      const clean = message.trim();
      if (!clean || inFlightRef.current) return null;

      try {
        return await sendMessageMutation.mutateAsync({
          message: clean,
          conversationId: conversationId ?? undefined,
          context,
        });
      } catch {
        // The mutation's onError handler stores a user-facing message.
        return null;
      }
    },
    [conversationId, sendMessageMutation]
  );

  const clearConversation = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setError(null);
    inFlightRef.current = false;
    if (typeof window !== 'undefined') {
      window.sessionStorage.removeItem(CHAT_STORAGE_KEY);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return {
    messages,
    conversationId,
    isLoading: sendMessageMutation.isPending,
    error,
    clearError,
    sendMessage,
    clearConversation,
  };
}
