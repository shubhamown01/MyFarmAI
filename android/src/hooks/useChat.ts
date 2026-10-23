import { useState, useCallback } from 'react';
import { apiClient, ApiError } from '../lib/api/client';
import { ChatMessage, ChatContext } from '../../types/chat';

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (text: string, context?: ChatContext) => {
      if (!text.trim()) return;

      const userMessage = {
        id: crypto.randomUUID(),
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
          id: crypto.randomUUID(),
          role: 'assistant' as const,
          content: response.response,
          timestamp: new Date(),
          conversationId: response.conversation_id,
        };

        setMessages((prev) => [...prev, assistantMessage]);
        setConversationId(response.conversation_id);
      } catch (error) {
        if (error instanceof ApiError) {
          setError(`${error.code}: ${error.message}`);
        } else {
          setError('Failed to send message');
        }
        // Remove user message on error
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setIsLoading(false);
      }
    },
    [conversationId]
  );

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
    sendMessage,
    clearConversation,
  };
}