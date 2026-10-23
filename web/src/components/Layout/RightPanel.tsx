'use client';

import Link from 'next/link';
import {
  ArrowRight,
  ChevronRight,
  Leaf,
  MapPin,
  RefreshCw,
} from 'lucide-react';
import { WeatherScene } from '@/components/Icons/FarmIcons';
import { QUICK_TOOLS, SAMPLE_TIP } from '@/lib/dashboard-data';
import { useProfile } from '@/hooks/useProfile';
import { useWeather } from '@/hooks/useWeather';
import { formatDataAge, getWeatherDescription } from '@/lib/utils';
import { cn } from '@/lib/utils';

const TOOL_TINT = {
  red: 'bg-tint-red',
  green: 'bg-tint-green',
  orange: 'bg-tint-orange',
  purple: 'bg-tint-purple',
} as const;

function WeatherSummary() {
  const { profile } = useProfile();
  const { currentWeather, forecast, isLoading, error, refetch, dataUpdatedAt } = useWeather(
    profile.latitude,
    profile.longitude,
  );
  const today = forecast?.[0];

  return (
    <section
      className="rounded-2xl border border-outline bg-surface p-5 shadow-elev-1"
      aria-labelledby="weather-summary-heading"
    >
      <div className="flex items-center justify-between gap-3">
        <h2
          id="weather-summary-heading"
          className="flex min-w-0 items-center gap-1.5 text-[14px] font-semibold text-on-surface"
        >
          <MapPin className="h-4 w-4 flex-none text-on-surface-variant" aria-hidden="true" />
          <span className="truncate">{profile.locationLabel}</span>
        </h2>
        <Link
          href="/weather"
          className="inline-flex h-8 w-8 flex-none items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          aria-label="Open full weather"
        >
          <ChevronRight className="h-5 w-5" aria-hidden="true" />
        </Link>
      </div>

      {isLoading ? (
        <div className="mt-4 animate-pulse" aria-label="Loading weather">
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-full bg-surface-container-high" />
            <div className="flex-1 space-y-2">
              <div className="h-8 w-24 rounded bg-surface-container-high" />
              <div className="h-4 w-28 rounded bg-surface-container-high" />
            </div>
          </div>
        </div>
      ) : error ? (
        <div className="mt-4">
          <p className="text-[13px] leading-5 text-on-surface-variant">
            Weather is unavailable right now.
          </p>
          <button
            type="button"
            onClick={() => void refetch()}
            className="mt-2 inline-flex min-h-9 items-center gap-1.5 rounded-lg border border-outline px-3 text-[13px] font-semibold text-on-surface transition-colors hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
            Try again
          </button>
        </div>
      ) : currentWeather ? (
        <>
          <div className="mt-3 flex items-center gap-4">
            <WeatherScene code={currentWeather.weathercode} className="h-[70px] w-[76px] flex-none" />
            <div className="min-w-0">
              <p className="text-[36px] font-bold leading-none tracking-[-0.04em] text-on-surface">
                {Math.round(currentWeather.temperature)}°C
              </p>
              <p className="mt-1.5 text-[14px] font-medium text-on-surface">
                {getWeatherDescription(currentWeather.weathercode)}
              </p>
              {today && (
                <p className="mt-0.5 text-[13px] text-on-surface-variant">
                  H: {Math.round(today.temperature_2m_max)}° L:{' '}
                  {Math.round(today.temperature_2m_min)}°
                </p>
              )}
            </div>
          </div>

          <p className="mt-3 text-[11px] text-on-surface-variant" aria-live="polite">
            {formatDataAge(dataUpdatedAt)}
          </p>

          <Link
            href="/weather"
            className="mt-4 inline-flex items-center gap-2 text-[14px] font-semibold text-primary transition-colors hover:text-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          >
            View Full Weather
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </>
      ) : (
        <p className="mt-4 text-[13px] leading-5 text-on-surface-variant">
          No weather data was returned for this location.
        </p>
      )}
    </section>
  );
}

function TodayTips() {
  return (
    <section aria-labelledby="today-tips-heading">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 id="today-tips-heading" className="text-[18px] font-bold tracking-[-0.01em] text-on-surface">
          Today&apos;s Tips
        </h2>
        <Link
          href="/knowledge?category=advisory"
          className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-primary transition-colors hover:text-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          More guides
          <ArrowRight className="h-4 w-4" aria-hidden="true" />
        </Link>
      </div>

      <div className="rounded-2xl border border-outline bg-surface p-4">
        <div className="flex items-start gap-3">
          <span className="flex h-9 w-9 flex-none items-center justify-center rounded-full bg-primary-container">
            <Leaf className="h-[18px] w-[18px] text-primary" aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <span className="inline-flex rounded-full bg-surface-container-high px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-on-surface-variant">
              {SAMPLE_TIP.label}
            </span>
            <p className="mt-1.5 text-[14px] leading-5 text-on-surface">{SAMPLE_TIP.text}</p>
            <p className="mt-1.5 text-[11px] leading-4 text-on-surface-variant">
              Example content. Live farm advice is not connected.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function QuickTools() {
  return (
    <section aria-labelledby="quick-tools-heading">
      <h2
        id="quick-tools-heading"
        className="mb-3 text-[18px] font-bold tracking-[-0.01em] text-on-surface"
      >
        Quick Tools
      </h2>
      <ul className="space-y-2.5" role="list">
        {QUICK_TOOLS.map((tool) => {
          const Icon = tool.icon;
          return (
            <li key={tool.id}>
              <Link
                href={tool.href}
                className="group flex items-center gap-3 rounded-xl border border-outline bg-surface px-3.5 py-3 transition-colors hover:border-outline-strong hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              >
                <span
                  className={cn(
                    'flex h-10 w-10 flex-none items-center justify-center rounded-lg',
                    TOOL_TINT[tool.tint],
                  )}
                >
                  <Icon className="h-6 w-6" aria-hidden="true" />
                </span>
                <span className="flex-1 text-[14px] font-medium text-on-surface">{tool.label}</span>
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
  );
}

export function RightPanel() {
  return (
    <aside className="min-w-0 space-y-7 xl:sticky xl:top-[112px] xl:self-start" aria-label="Farm context">
      <WeatherSummary />
      <TodayTips />
      <QuickTools />
    </aside>
  );
}
