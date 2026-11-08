'use client';

import Link from 'next/link';
import {
  Cloud,
  MessageCircle,
  ShieldCheck,
  Smartphone,
} from 'lucide-react';

const FEATURES = [
  {
    icon: MessageCircle,
    title: 'AI agricultural assistant',
    body: 'Ask crop, pest and weather questions in plain language and get grounded answers with sources.',
  },
  {
    icon: Cloud,
    title: 'Weather and crop info',
    body: 'Location-aware weather plus crop-cycle plans to organise sowing, feeding and harvest.',
  },
  {
    icon: ShieldCheck,
    title: 'Your data stays yours',
    body: 'Farms and plots are stored privately. Test with synthetic data; no admin access without approval.',
  },
] as const;

export default function LandingPage() {
  return (
    <div className="min-h-dvh bg-surface text-on-surface">
      <header className="mx-auto flex max-w-5xl items-center justify-between px-4 py-5 sm:px-6">
        <span className="flex items-center gap-2 text-[17px] font-semibold">
          <span aria-hidden="true" className="text-primary">🌱</span>
          MyFarm AI
        </span>
        <nav aria-label="Primary" className="flex items-center gap-3 text-[14px]">
          <Link
            href="/auth/login"
            className="rounded-xl px-4 py-2 font-medium transition-colors hover:bg-surface-container-low"
          >
            Log in
          </Link>
          <Link
            href="/auth/register"
            className="rounded-xl bg-primary px-4 py-2 font-semibold text-on-primary transition-colors hover:bg-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          >
            Create account
          </Link>
        </nav>
      </header>

      <main>
        <section className="mx-auto max-w-5xl px-4 pb-14 pt-8 sm:px-6">
          <h1 className="max-w-2xl text-3xl font-semibold leading-tight sm:text-4xl">
            A farming assistant for real questions
          </h1>
          <p className="mt-3 max-w-xl text-[15px] leading-6 text-on-surface-variant">
            MyFarm AI helps you plan crops, watch the weather and ask agricultural
            questions — on your phone, from anywhere with an internet connection.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Link
              href="/auth/register"
              className="inline-flex min-h-11 items-center rounded-xl bg-primary px-5 text-[14px] font-semibold text-on-primary transition-colors hover:bg-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            >
              Start testing — create an account
            </Link>
            <a
              href="/api/v1/downloads/app-release.apk"
              className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-outline px-5 text-[14px] font-semibold transition-colors hover:bg-surface-container-low"
              download
            >
              <Smartphone className="h-4 w-4" aria-hidden="true" />
              Download Android app
            </a>
          </div>
          <p className="mt-2 text-[12px] text-on-surface-variant" role="note">
            Test release. Registration needs a verified email; reaches you with a one-time code.
          </p>
        </section>

        <section
          aria-label="Features"
          className="mx-auto grid max-w-5xl gap-4 px-4 pb-16 sm:grid-cols-3 sm:px-6"
        >
          {FEATURES.map(({ icon: Icon, title, body }) => (
            <div
              key={title}
              className="rounded-2xl border border-outline bg-surface-container-low p-5"
            >
              <Icon className="h-5 w-5 text-primary" aria-hidden="true" />
              <h2 className="mt-3 text-[15px] font-semibold">{title}</h2>
              <p className="mt-1 text-[13px] leading-5 text-on-surface-variant">{body}</p>
            </div>
          ))}
        </section>
      </main>

      <footer className="border-t border-outline">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-4 px-4 py-6 text-[13px] text-on-surface-variant sm:px-6">
          <span>© 2026 MyFarm AI — test deployment.</span>
          <Link href="/legal/privacy" className="hover:text-on-surface hover:underline">
            Privacy
          </Link>
          <Link href="/legal/terms" className="hover:text-on-surface hover:underline">
            Terms
          </Link>
        </div>
      </footer>
    </div>
  );
}
