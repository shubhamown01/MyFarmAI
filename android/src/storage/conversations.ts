import * as SecureStore from 'expo-secure-store';

const STORAGE_KEY = 'myfarmai_conversations';

export interface StoredConversation {
  id: string;
  messages: Array<{
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    conversationId: string;
  }>;
  updatedAt: number;
}

export async function saveConversation(conversation: StoredConversation) {
  const existing = await getConversations();
  const updated = existing.filter((c) => c.id !== conversation.id);
  updated.unshift(conversation);
  await SecureStore.setItemAsync(
    STORAGE_KEY,
    JSON.stringify(updated.slice(0, 50)) // Keep last 50
  );
}

export async function getConversations(): Promise<StoredConversation[]> {
  const data = await SecureStore.getItemAsync(STORAGE_KEY);
  return data ? JSON.parse(data) : [];
}

export async function deleteConversation(id: string) {
  const existing = await getConversations();
  const updated = existing.filter((c) => c.id !== id);
  await SecureStore.setItemAsync(STORAGE_KEY, JSON.stringify(updated));
}