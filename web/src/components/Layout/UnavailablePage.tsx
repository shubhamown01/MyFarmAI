import Link from 'next/link';
import { ArrowRight } from 'lucide-react';

export interface UnavailablePageProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  primaryAction: { href: string; label: string };
  secondaryAction?: { href: string; label: string };
}

export function UnavailablePage({
  title,
  description,
  icon,
  primaryAction,
  secondaryAction,
}: UnavailablePageProps) {
  return (
    <div className="mx-auto w-full max-w-[900px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <h1 className="text-[28px] font-bold tracking-[-0.025em] text-on-surface sm:text-[32px]">
        {title}
      </h1>

      <section className="mt-5 rounded-2xl border border-outline bg-surface p-6 sm:p-8">
        <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-container">
          {icon}
        </span>
        <h2 className="mt-5 text-[20px] font-bold tracking-[-0.015em] text-on-surface">
          This section is not connected yet
        </h2>
        <p className="mt-2 max-w-2xl text-[14px] leading-6 text-on-surface-variant">
          {description}
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href={primaryAction.href}
            className="inline-flex min-h-10 items-center gap-2 rounded-xl bg-primary px-4 text-[14px] font-semibold text-on-primary transition-colors hover:bg-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          >
            {primaryAction.label}
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
          {secondaryAction && (
            <Link
              href={secondaryAction.href}
              className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-outline px-4 text-[14px] font-semibold text-on-surface transition-colors hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            >
              {secondaryAction.label}
            </Link>
          )}
        </div>
      </section>
    </div>
  );
}
