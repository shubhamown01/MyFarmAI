'use client';

import { useSearchParams } from 'next/navigation';
import { ChatInterface } from '@/components/Chat/ChatInterface';

export function AssistantChat() {
  const searchParams = useSearchParams();
  const initialQuestion = searchParams.get('q') ?? '';

  return <ChatInterface initialQuestion={initialQuestion} />;
}
