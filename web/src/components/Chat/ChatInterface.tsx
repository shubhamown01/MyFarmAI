'use client';

import { useEffect, useRef, useState } from 'react';
import { Loader2, RotateCcw, Sparkles, Trash2 } from 'lucide-react';
import { QuestionComposer } from '@/components/Dashboard/QuestionComposer';
import { FormattedText } from '@/components/Chat/FormattedText';
import { BrandMark } from '@/components/Icons/FarmIcons';
import { EXAMPLE_QUESTIONS } from '@/lib/dashboard-data';
import { useChat } from '@/hooks/useChat';
import { useProfile } from '@/hooks/useProfile';
import { useRecentQuestions } from '@/hooks/useRecentQuestions';
import { cn } from '@/lib/utils';

export interface ChatInterfaceProps {
  initialQuestion?: string;
}

export function ChatInterface({ initialQuestion = '' }: ChatInterfaceProps) {
  const { profile } = useProfile();
  const { addQuestion } = useRecentQuestions();
  const { messages, isLoading, error, sendMessage, clearConversation } = useChat();
  const [input, setInput] = useState(initialQuestion);
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (initialQuestion.trim()) {
      setInput(initialQuestion.trim());
    }
  }, [initialQuestion]);

  useEffect(() => {
    const element = scrollRef.current;
    if (element) {
      element.scrollTop = element.scrollHeight;
    }
  }, [messages.length, isLoading, error]);

  const ask = (text: string) =>
    sendMessage(text, { location: profile.locationLabel });

  const handleSubmit = async (text: string) => {
    setInput('');
    setLastQuestion(text);
    addQuestion(text);
    await ask(text);
  };

  const handleSuggestion = (text: string) => {
    setInput(text);
    document.getElementById('assistant-question')?.focus();
  };

  const handleRetry = () => {
    if (lastQuestion) void ask(lastQuestion);
  };

  const handleClear = () => {
    clearConversation();
    setLastQuestion(null);
    setInput('');
  };

  return (
    <div className="flex h-[calc(100dvh-14rem)] min-h-[470px] flex-col overflow-hidden rounded-2xl border border-outline bg-surface shadow-elev-1">
      <div className="flex flex-none items-center justify-between gap-3 border-b border-outline px-4 py-3 sm:px-5">
        <p className="text-[13px] font-semibold text-on-surface">
          {messages.length ? `${messages.length} messages` : 'New conversation'}
        </p>
        <button
          type="button"
          onClick={handleClear}
          disabled={!messages.length && !error}
          className="inline-flex min-h-9 items-center gap-1.5 rounded-lg px-2.5 text-[13px] font-medium text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Trash2 className="h-4 w-4" aria-hidden="true" />
          Clear chat
        </button>
      </div>

      <div
        ref={scrollRef}
        role="log"
        aria-label="Conversation"
        aria-live="polite"
        aria-relevant="additions"
        className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-6"
      >
        {!messages.length && !error && !isLoading ? (
          <div className="flex min-h-full flex-col items-center justify-center py-6 text-center">
            <span className="flex h-14 w-14 items-center justify-center rounded-full bg-primary-container">
              <Sparkles className="h-6 w-6 text-primary" aria-hidden="true" />
            </span>
            <h2 className="mt-4 text-[22px] font-bold tracking-[-0.02em] text-on-surface">
              Ask about your farm
            </h2>
            <p className="mt-2 max-w-md text-[14px] leading-6 text-on-surface-variant">
              Questions go to the connected AI assistant. You can ask about crops, pests,
              weather, or farming practices.
            </p>

            <div className="mt-6 w-full max-w-lg">
              <p className="text-[12px] font-medium uppercase tracking-wide text-on-surface-variant">
                Example questions
              </p>
              <div className="mt-2.5 flex flex-col gap-2">
                {EXAMPLE_QUESTIONS.map((example) => (
                  <button
                    key={example.id}
                    type="button"
                    onClick={() => handleSuggestion(example.question)}
                    className="min-h-11 rounded-xl border border-outline bg-surface px-4 py-2.5 text-left text-[14px] text-on-surface transition-colors hover:border-outline-strong hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                  >
                    {example.question}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-5">
            {messages.map((message) => {
              const isUser = message.role === 'user';
              return (
                <article
                  key={message.id}
                  className={cn('flex gap-2.5', isUser ? 'justify-end' : 'justify-start')}
                >
                  {!isUser && (
                    <span className="mt-1 flex h-8 w-8 flex-none items-center justify-center rounded-full bg-primary-container">
                      <BrandMark className="h-5 w-5" />
                    </span>
                  )}
                  <div
                    className={cn(
                      'max-w-[86%] rounded-2xl px-4 py-3 text-[14px] leading-6 sm:max-w-[78%]',
                      isUser
                        ? 'rounded-br-md bg-primary text-on-primary'
                        : 'rounded-bl-md border border-outline bg-surface-container-low text-on-surface',
                    )}
                  >
                    <span className="sr-only">
                      {isUser ? 'You asked: ' : 'Assistant answered: '}
                    </span>
                    <FormattedText
                      text={message.content}
                      className="whitespace-pre-wrap break-words"
                    />
                  </div>
                </article>
              );
            })}

            {isLoading && (
              <div className="flex items-center gap-2.5 text-[14px] text-on-surface-variant" aria-live="polite">
                <span className="flex h-8 w-8 flex-none items-center justify-center rounded-full bg-primary-container">
                  <BrandMark className="h-5 w-5" />
                </span>
                <span className="inline-flex items-center gap-2 rounded-2xl rounded-bl-md border border-outline bg-surface-container-low px-4 py-3">
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  Thinking…
                </span>
              </div>
            )}

            {error && !isLoading && (
              <div role="alert" className="rounded-xl border border-error/25 bg-error-container px-4 py-3 text-on-error-container">
                <p className="text-[13px] leading-5">{error}</p>
                {lastQuestion && (
                  <button
                    type="button"
                    onClick={handleRetry}
                    className="mt-2 inline-flex min-h-9 items-center gap-1.5 rounded-lg border border-error/25 bg-surface/60 px-3 text-[13px] font-semibold transition-colors hover:bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  >
                    <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
                    Try again
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex-none border-t border-outline p-3 sm:p-4">
        <QuestionComposer
          value={input}
          onChange={setInput}
          onSubmit={handleSubmit}
          isSubmitting={isLoading}
          placeholder="Ask about crops, pests, weather, or farming practices..."
          inputId="assistant-question"
          compact
        />
      </div>
    </div>
  );
}
