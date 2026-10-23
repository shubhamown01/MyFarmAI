'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  ArrowRight,
  ChevronRight,
  Leaf,
  Loader2,
  MessageSquare,
  RotateCcw,
} from 'lucide-react';
import { QuestionComposer } from './QuestionComposer';
import { FormattedText } from '@/components/Chat/FormattedText';
import { SeedlingIllustration } from '@/components/Icons/FarmIcons';
import {
  EXAMPLE_QUESTIONS,
  QUICK_ACTIONS,
  QUESTION_THEME_ICONS,
  getQuestionTheme,
} from '@/lib/dashboard-data';
import { useProfile } from '@/hooks/useProfile';
import { useRecentQuestions } from '@/hooks/useRecentQuestions';
import { useChat } from '@/hooks/useChat';
import { cn, formatQuestionDate } from '@/lib/utils';

const QUICK_ACTION_TINT = {
  green: {
    card: 'bg-tint-green hover:border-icon-green/30',
    arrow: 'text-icon-green',
  },
  blue: {
    card: 'bg-tint-blue hover:border-icon-blue/30',
    arrow: 'text-icon-blue',
  },
  orange: {
    card: 'bg-tint-orange hover:border-icon-orange/30',
    arrow: 'text-icon-orange',
  },
  purple: {
    card: 'bg-tint-purple hover:border-icon-purple/30',
    arrow: 'text-icon-purple',
  },
} as const;

function SectionHeading({
  id,
  title,
  action,
}: {
  id: string;
  title: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
      <h2 id={id} className="text-[20px] font-bold tracking-[-0.015em] text-on-surface">
        {title}
      </h2>
      {action}
    </div>
  );
}

export function HomeDashboard() {
  const { profile } = useProfile();
  const { questions, addQuestion } = useRecentQuestions();
  const { messages, isLoading, error, sendMessage } = useChat();
  const [question, setQuestion] = useState('');
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);
  const [hasAsked, setHasAsked] = useState(false);

  const ask = (text: string) =>
    sendMessage(text, { location: profile.locationLabel });

  const handleSubmit = async (text: string) => {
    setQuestion('');
    setLastQuestion(text);
    setHasAsked(true);
    addQuestion(text);
    await ask(text);
  };

  const handleRetry = () => {
    if (lastQuestion) void ask(lastQuestion);
  };

  const latestAnswer = hasAsked
    ? [...messages].reverse().find((message) => message.role === 'assistant')
    : undefined;

  const recentItems = questions.length
    ? questions.slice(0, 4).map((item) => ({
        id: item.id,
        text: item.text,
        meta: formatQuestionDate(item.createdAt),
        example: false,
        theme: getQuestionTheme(item.text),
      }))
    : EXAMPLE_QUESTIONS.map((item) => ({
        id: item.id,
        text: item.question,
        meta: 'Example',
        example: true,
        theme: item.theme,
      }));

  return (
    <div className="min-w-0">
      <section className="flex items-start justify-between gap-6" aria-labelledby="welcome-heading">
        <div className="min-w-0 pt-1">
          <h1
            id="welcome-heading"
            className="text-balance text-[34px] font-bold leading-[1.12] tracking-[-0.035em] text-on-surface sm:text-[40px] lg:text-[44px]"
          >
            Hello, <span className="text-primary">{profile.name}</span>
          </h1>
          <p className="mt-2 text-[17px] leading-7 text-on-surface-variant sm:text-[19px]">
            Ask farming questions, check crop health, and get weather guidance — all in one place.
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <Link
              href="/assistant"
              className="inline-flex min-h-[44px] items-center gap-2 rounded-lg bg-primary px-4 text-[14px] font-semibold text-on-primary transition-colors hover:bg-primary-hover active:bg-primary-active focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            >
              <MessageSquare className="h-4 w-4" aria-hidden="true" />
              Ask the AI Assistant
            </Link>
            <Link
              href="/pest-disease"
              className="inline-flex min-h-[44px] items-center gap-2 rounded-lg border border-outline bg-surface px-4 text-[14px] font-semibold text-on-surface transition-colors hover:bg-surface-container-high focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            >
              <Leaf className="h-4 w-4" aria-hidden="true" />
              Check Crop Health
            </Link>
          </div>
        </div>
        <SeedlingIllustration className="hidden h-auto w-[150px] flex-none sm:block lg:w-[188px]" />
      </section>

      <div className="mt-7">
        <QuestionComposer
          value={question}
          onChange={setQuestion}
          onSubmit={handleSubmit}
          isSubmitting={isLoading}
          placeholder="Ask your farming question..."
          inputId="dashboard-question"
        />
      </div>

      <section className="mt-8" aria-labelledby="quick-actions-heading">
        <SectionHeading id="quick-actions-heading" title="Quick Actions" />
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-2 min-[1400px]:grid-cols-4">
          {QUICK_ACTIONS.map((action) => {
            const Icon = action.icon;
            const tint = QUICK_ACTION_TINT[action.tint];

            return (
              <Link
                key={action.id}
                href={action.href}
                className={cn(
                  'group relative flex min-h-[140px] flex-col justify-between rounded-2xl border border-transparent p-3.5',
                  'transition-all duration-fast hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
                  tint.card,
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-surface/70 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.55)]">
                    <Icon className="h-8 w-8" aria-hidden="true" />
                  </span>
                  <ArrowRight
                    className={cn('mt-1 h-[18px] w-[18px]', tint.arrow)}
                    aria-hidden="true"
                  />
                </div>
                <div className="mt-4">
                  <h3 className="text-[15px] font-semibold leading-5 text-on-surface">
                    {action.title}
                  </h3>
                  <p className="mt-0.5 text-[12px] leading-5 text-on-surface-variant">
                    {action.description}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      <section className="mt-8" aria-labelledby="recent-heading">
        <SectionHeading
          id="recent-heading"
          title="Recent Questions"
          action={
            <Link
              href="/history"
              className="inline-flex items-center gap-1.5 text-[14px] font-semibold text-primary transition-colors hover:text-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            >
              View All
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          }
        />
        {!questions.length && (
          <p className="mb-3 -mt-1 text-[13px] text-on-surface-variant">
            No saved questions yet. These labelled examples show what you can ask.
          </p>
        )}

        <ul className="space-y-2.5" role="list">
          {recentItems.map((item) => {
            const Icon = QUESTION_THEME_ICONS[item.theme];
            return (
              <li key={item.id}>
                <Link
                  href={`/assistant?q=${encodeURIComponent(item.text)}`}
                  className="group flex min-h-[52px] items-center gap-3 rounded-xl border border-outline bg-surface px-4 py-3 transition-colors hover:border-outline-strong hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                >
                  <Icon className="h-5 w-5 flex-none" aria-hidden="true" />
                  <span className="line-clamp-2 min-w-0 flex-1 text-[14px] font-medium text-on-surface sm:line-clamp-1 sm:text-[15px]">
                    {item.text}
                  </span>
                  <span
                    className={cn(
                      'flex-none text-[12px]',
                      item.example
                        ? 'inline-flex rounded-full bg-surface-container-high px-2 py-0.5 font-medium text-on-surface-variant'
                        : 'hidden text-on-surface-variant sm:inline',
                    )}
                  >
                    {item.meta}
                  </span>
                  <ChevronRight
                    className="h-4 w-4 flex-none text-on-surface-variant transition-transform group-hover:translate-x-0.5"
                    aria-hidden="true"
                  />
                </Link>
              </li>
            );
          })}
        </ul>
      </section>

      {hasAsked && (
        <section className="mt-8" aria-labelledby="assistant-answer-heading">
          <SectionHeading
            id="assistant-answer-heading"
            title="Assistant Answer"
            action={
              <Link
                href="/assistant"
                className="inline-flex items-center gap-1.5 text-[14px] font-semibold text-primary transition-colors hover:text-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              >
                Open full conversation
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>
            }
          />

          <div className="rounded-2xl border border-outline bg-surface p-4 sm:p-5" aria-live="polite">
            {isLoading ? (
              <div className="flex items-center gap-2.5 text-[14px] text-on-surface-variant">
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                Asking the assistant…
              </div>
            ) : error ? (
              <div>
                <p className="text-[14px] leading-6 text-error">{error}</p>
                <button
                  type="button"
                  onClick={handleRetry}
                  className="mt-3 inline-flex min-h-9 items-center gap-1.5 rounded-lg border border-outline px-3 text-[13px] font-semibold text-on-surface transition-colors hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                >
                  <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
                  Try again
                </button>
              </div>
            ) : latestAnswer ? (
              <FormattedText
                text={latestAnswer.content}
                className="whitespace-pre-wrap break-words text-[14px] leading-6 text-on-surface sm:text-[15px]"
              />
            ) : (
              <p className="text-[14px] text-on-surface-variant">
                The assistant returned an empty answer. Try asking again.
              </p>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
