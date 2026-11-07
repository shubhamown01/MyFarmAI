import { useState, useEffect, useCallback } from 'react';
import { makeId } from '../utils/id';
import {
  saveConversation,
  getConversations,
  StoredConversation,
} from '../storage/conversations';
import { apiClient, ApiError } from '../lib/api/client';
import { ChatMessage, ChatContext } from '../types/chat';


// Chat error mapping (TEST-AUDIT High-5): codes observed on the deployed
// API (staging verification 2026-11) plus defensive fall-through. Farmer
// language, no internal jargon. Exported for unit testing.
export const friendlyChatError = (error: unknown): string => {
  if (error instanceof ApiError) {
    switch (error.code) {
      case 'NETWORK_ERROR':
        return 'You appear to be offline. Check your connection and try again.';
      case 'NOT_AUTHENTICATED':
      case 'UNAUTHORIZED':
        return 'Your session has expired. Sign in again from the dashboard.';
      case 'RATE_LIMIT_EXCEEDED':
        return 'Too many requests — please wait a minute and try again.';
      case 'AI_QUOTA_EXCEEDED':
        return 'Daily AI question limit reached. Try again after the quota resets.';
      case 'AI_BUSY':
      case 'AI_UNAVAILABLE':
        return 'The AI service is busy. Please try again shortly.';
      case 'AI_QUOTA_UNAVAILABLE':
        return 'The AI service is temporarily unavailable (quota check failed). Try again shortly.';
    }
    if (error.message) return error.message;
  }
  return 'Failed to send message. Please try again.';
};

// Per-conversation message cap (TEST-AUDIT High-6): SecureStore is a
// single-key store with a ~2 MB per-value ceiling; without a bound one
// long-running thread eventually fails all persistence.
const MESSAGES_PER_CONVERSATION_CAP = 200;

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (text: string, context?: ChatContext) => {
      if (!text.trim()) return;

      const userMessage = {
        id: makeId(),
        role: 'user' as const,
        content: text,
        timestamp: new Date(),
        conversationId: conversationId || '',
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      try {
        const response = await apiClient.sendMessage(
          text,
          conversationId || undefined,
          context
        );

        const assistantMessage = {
          id: makeId(),
          role: 'assistant' as const,
          content: response.response,
          timestamp: new Date(),
          conversationId: response.conversation_id,
        };

        setMessages((prev) => [...prev, assistantMessage]);
        setConversationId(response.conversation_id);
      } catch (error) {
        if (error instanceof ApiError) {
          setError(friendlyChatError(error));
        } else {
          setError(friendlyChatError(error));
        }
        // Remove user message on error
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setIsLoading(false);
      }
    },
    [conversationId]
  );

  // Restore the most recent cached conversation once on mount so farmers
  // continue from previous context after an app restart (journey step 12).
  useEffect(() => {
    let cancelled = false;
    getConversations()
      .then((conversations) => {
        if (cancelled || !conversations.length) return;
        const latest = conversations[0];
        setMessages(
          latest.messages.slice(-MESSAGES_PER_CONVERSATION_CAP).map((m) => ({
            ...m,
            timestamp: new Date(m.timestamp),
          })),
        );
        setConversationId(latest.id);
      })
      .catch(() => {
        // Cache is a convenience: restore failures must never block chat.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Persist after every exchange. Storage failures are swallowed — chat
  // itself always works over the network, the cache is best-effort.
  useEffect(() => {
    if (!messages.length || !conversationId) return;
    const toStore: StoredConversation = {
      id: conversationId,
      messages: messages.slice(-MESSAGES_PER_CONVERSATION_CAP).map((m) => ({
        ...m,
        timestamp: m.timestamp.toISOString(),
      })),
      updatedAt: Date.now(),
    };
    saveConversation(toStore).catch(() => {});
  }, [messages, conversationId]);

  const clearError = useCallback(() => setError(null), []);

  const clearConversation = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setError(null);
  }, []);

  return {
    messages,
    conversationId,
    isLoading,
    error,
    clearError,
    sendMessage,
    clearConversation,
  };
}