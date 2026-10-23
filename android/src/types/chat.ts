export interface ChatContext {
  language?: 'en' | 'hi';
  crop?: string;
  location?: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  language?: string;
  crop?: string;
  location?: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  model: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  conversationId: string;
}