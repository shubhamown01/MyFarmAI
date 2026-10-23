import type { Metadata } from 'next';
import { Suspense } from 'react';
import { AssistantChat } from './AssistantChat';

export const metadata: Metadata = {
  title: 'AI Assistant',
};

export default function AssistantPage() {
  return (
    <div className="mx-auto w-full max-w-[1040px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <div className="mb-5">
        <h1 className="text-[28px] font-bold tracking-[-0.025em] text-on-surface sm:text-[32px]">
          AI Assistant
        </h1>
        <p className="mt-1 text-[15px] text-on-surface-variant">
          Ask farming questions and get answers from the connected assistant.
        </p>
      </div>

      <Suspense
        fallback={
          <div
            className="h-[calc(100dvh-14rem)] min-h-[470px] animate-pulse rounded-2xl border border-outline bg-surface"
            aria-label="Loading assistant"
          />
        }
      >
        <AssistantChat />
      </Suspense>
    </div>
  );
}
