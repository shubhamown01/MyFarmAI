'use client';

import Link from 'next/link';
import { ChevronRight, Trash2 } from 'lucide-react';
import {
  EXAMPLE_QUESTIONS,
  QUESTION_THEME_ICONS,
  getQuestionTheme,
} from '@/lib/dashboard-data';
import { useRecentQuestions } from '@/hooks/useRecentQuestions';
import { formatQuestionDate } from '@/lib/utils';

export default function HistoryPage() {
  const { questions, clearQuestions } = useRecentQuestions();

  const handleClear = () => {
    if (window.confirm('Clear your local question history?')) {
      clearQuestions();
    }
  };

  return (
    <div className="mx-auto w-full max-w-[900px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-[28px] font-bold tracking-[-0.025em] text-on-surface sm:text-[32px]">
            Question History
          </h1>
          <p className="mt-1 text-[15px] text-on-surface-variant">
            Questions you ask on this device are saved here.
          </p>
        </div>
        {questions.length > 0 && (
          <button
            type="button"
            onClick={handleClear}
            className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-outline px-3.5 text-[13px] font-semibold text-on-surface transition-colors hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            Clear history
          </button>
        )}
      </div>

      {questions.length ? (
        <ul className="space-y-2.5" role="list">
          {questions.map((item) => {
            const Icon = QUESTION_THEME_ICONS[getQuestionTheme(item.text)];
            return (
              <li key={item.id}>
                <Link
                  href={`/assistant?q=${encodeURIComponent(item.text)}`}
                  className="group flex min-h-[56px] items-center gap-3 rounded-xl border border-outline bg-surface px-4 py-3 transition-colors hover:border-outline-strong hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                >
                  <Icon className="h-5 w-5 flex-none" aria-hidden="true" />
                  <span className="min-w-0 flex-1 text-[14px] font-medium text-on-surface">
                    {item.text}
                  </span>
                  <span className="flex-none text-[12px] text-on-surface-variant">
                    {formatQuestionDate(item.createdAt)}
                  </span>
                  <ChevronRight className="h-4 w-4 flex-none text-on-surface-variant" aria-hidden="true" />
                </Link>
              </li>
            );
          })}
        </ul>
      ) : (
        <div>
          <div className="rounded-2xl border border-dashed border-outline-strong bg-surface p-6">
            <p className="text-[15px] font-semibold text-on-surface">Nothing saved yet.</p>
            <p className="mt-1.5 text-[13px] leading-5 text-on-surface-variant">
              Ask a question from the dashboard or assistant and it will appear here.
              These labelled examples are not history.
            </p>
          </div>

          <h2 className="mb-3 mt-7 text-[18px] font-bold text-on-surface">Example questions</h2>
          <ul className="space-y-2.5" role="list">
            {EXAMPLE_QUESTIONS.map((item) => {
              const Icon = QUESTION_THEME_ICONS[item.theme];
              return (
                <li key={item.id}>
                  <Link
                    href={`/assistant?q=${encodeURIComponent(item.question)}`}
                    className="group flex min-h-[56px] items-center gap-3 rounded-xl border border-outline bg-surface px-4 py-3 transition-colors hover:border-outline-strong hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                  >
                    <Icon className="h-5 w-5 flex-none" aria-hidden="true" />
                    <span className="min-w-0 flex-1 text-[14px] font-medium text-on-surface">
                      {item.question}
                    </span>
                    <span className="flex-none rounded-full bg-surface-container-high px-2 py-0.5 text-[11px] font-medium text-on-surface-variant">
                      Example
                    </span>
                    <ChevronRight className="h-4 w-4 flex-none text-on-surface-variant" aria-hidden="true" />
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
