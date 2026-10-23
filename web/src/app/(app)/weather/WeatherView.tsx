'use client';

import Link from 'next/link';
import { Droplets, MapPin, RefreshCw, Wind } from 'lucide-react';
import { WeatherScene } from '@/components/Icons/FarmIcons';
import { useProfile } from '@/hooks/useProfile';
import { useWeather } from '@/hooks/useWeather';
import { formatDataAge, getWeatherDescription } from '@/lib/utils';

function windDirection(degrees: number) {
  const points = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
  return points[Math.round(degrees / 45) % 8];
}

function dayLabel(date: string, index: number) {
  if (index === 0) return 'Today';
  const parsed = new Date(`${date}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return date;
  return parsed.toLocaleDateString('en-IN', { weekday: 'short' });
}

export function WeatherView() {
  const { profile } = useProfile();
  const { currentWeather, forecast, isLoading, isFetching, error, refetch, dataUpdatedAt } =
    useWeather(profile.latitude, profile.longitude);
  const today = forecast?.[0];

  return (
    <div className="mx-auto w-full max-w-[1100px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <img
        src="/images/weather-irrigation.svg"
        alt="Farmland under realistic weather conditions with irrigation systems and water management"
        className="w-full h-auto max-w-[600px] mx-auto mb-6"
        width={1000}
        height={750}
        loading="lazy"
        decoding="async"
      />
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-[28px] font-bold tracking-[-0.025em] text-on-surface sm:text-[32px]">
            Weather
          </h1>
          <p className="mt-1 flex items-center gap-1.5 text-[14px] text-on-surface-variant">
            <MapPin className="h-4 w-4" aria-hidden="true" />
            {profile.locationLabel}
            <span className="text-outline-strong" aria-hidden="true">·</span>
            <Link
              href="/settings"
              className="font-medium text-primary underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            >
              Change location
            </Link>
          </p>
        </div>

        <button
          type="button"
          onClick={() => void refetch()}
          disabled={isFetching}
          className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-outline bg-surface px-3.5 text-[13px] font-semibold text-on-surface transition-colors hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-60"
        >
          <RefreshCw className={isFetching ? 'h-4 w-4 animate-spin' : 'h-4 w-4'} aria-hidden="true" />
          {isFetching ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-4" aria-label="Loading weather">
          <div className="h-56 animate-pulse rounded-2xl border border-outline bg-surface-container-low" />
          <div className="h-72 animate-pulse rounded-2xl border border-outline bg-surface-container-low" />
        </div>
      ) : error ? (
        <div className="rounded-2xl border border-outline bg-surface p-8 text-center">
          <p className="text-[15px] font-semibold text-on-surface">Weather is unavailable right now.</p>
          <p className="mx-auto mt-1.5 max-w-md text-[13px] leading-5 text-on-surface-variant">
            The weather service could not be reached. Check your connection, then try again.
          </p>
          <button
            type="button"
            onClick={() => void refetch()}
            className="mt-4 inline-flex min-h-10 items-center gap-2 rounded-xl border border-outline px-4 text-[13px] font-semibold text-on-surface transition-colors hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            Try again
          </button>
        </div>
      ) : currentWeather ? (
        <div className="space-y-5">
          <section
            className="rounded-2xl border border-outline bg-surface p-5 shadow-elev-1 sm:p-7"
            aria-labelledby="current-weather-heading"
          >
            <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 id="current-weather-heading" className="text-[13px] font-semibold uppercase tracking-wide text-on-surface-variant">
                  Current conditions
                </h2>
                <div className="mt-3 flex items-center gap-4">
                  <WeatherScene
                    code={currentWeather.weathercode}
                    className="h-20 w-24 flex-none"
                  />
                  <div>
                    <p className="text-[48px] font-bold leading-none tracking-[-0.045em] text-on-surface">
                      {Math.round(currentWeather.temperature)}°C
                    </p>
                    <p className="mt-2 text-[15px] font-medium text-on-surface">
                      {getWeatherDescription(currentWeather.weathercode)}
                    </p>
                    {today && (
                      <p className="mt-0.5 text-[13px] text-on-surface-variant">
                        High {Math.round(today.temperature_2m_max)}° · Low{' '}
                        {Math.round(today.temperature_2m_min)}°
                      </p>
                    )}
                  </div>
                </div>
              </div>

              <dl className="grid grid-cols-2 gap-3 sm:w-[320px]">
                <div className="rounded-xl bg-surface-container-low p-3.5">
                  <dt className="flex items-center gap-1.5 text-[12px] text-on-surface-variant">
                    <Wind className="h-4 w-4" aria-hidden="true" />
                    Wind
                  </dt>
                  <dd className="mt-1 text-[15px] font-semibold text-on-surface">
                    {Math.round(currentWeather.windspeed)} km/h{' '}
                    <span className="font-normal text-on-surface-variant">
                      {windDirection(currentWeather.winddirection)}
                    </span>
                  </dd>
                </div>
                <div className="rounded-xl bg-surface-container-low p-3.5">
                  <dt className="flex items-center gap-1.5 text-[12px] text-on-surface-variant">
                    <Droplets className="h-4 w-4" aria-hidden="true" />
                    Rain today
                  </dt>
                  <dd className="mt-1 text-[15px] font-semibold text-on-surface">
                    {today ? `${today.precipitation_probability_max}%` : '—'}
                  </dd>
                </div>
                <div className="col-span-2 rounded-xl bg-surface-container-low p-3.5">
                  <dt className="text-[12px] text-on-surface-variant">Expected rainfall</dt>
                  <dd className="mt-1 text-[15px] font-semibold text-on-surface">
                    {today ? `${today.precipitation_sum.toFixed(1)} mm` : 'No forecast available'}
                  </dd>
                </div>
              </dl>
            </div>

            <p className="mt-5 text-[11px] text-on-surface-variant" aria-live="polite">
              {formatDataAge(dataUpdatedAt)}
            </p>
          </section>

          <section aria-labelledby="forecast-heading">
            <h2 id="forecast-heading" className="mb-3 text-[20px] font-bold tracking-[-0.015em] text-on-surface">
              Daily forecast
            </h2>
            {forecast?.length ? (
              <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" role="list">
                {forecast.slice(0, 7).map((day, index) => (
                  <li
                    key={day.date}
                    className="rounded-xl border border-outline bg-surface p-4"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-[14px] font-semibold text-on-surface">
                          {dayLabel(day.date, index)}
                        </p>
                        <p className="text-[12px] text-on-surface-variant">
                          {new Date(`${day.date}T00:00:00`).toLocaleDateString('en-IN', {
                            day: 'numeric',
                            month: 'short',
                          })}
                        </p>
                      </div>
                      <WeatherScene code={day.weathercode} className="h-10 w-11" />
                    </div>
                    <p className="mt-2 text-[13px] text-on-surface">
                      {getWeatherDescription(day.weathercode)}
                    </p>
                    <div className="mt-3 flex items-center justify-between text-[13px]">
                      <span className="font-semibold text-on-surface">
                        {Math.round(day.temperature_2m_max)}°{' '}
                        <span className="font-normal text-on-surface-variant">
                          / {Math.round(day.temperature_2m_min)}°
                        </span>
                      </span>
                      <span className="text-on-surface-variant">
                        {day.precipitation_probability_max}% rain
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="rounded-xl border border-outline bg-surface p-5 text-[14px] text-on-surface-variant">
                No daily forecast was returned for this location.
              </p>
            )}
          </section>
        </div>
      ) : (
        <div className="rounded-2xl border border-outline bg-surface p-8 text-center">
          <p className="text-[15px] font-semibold text-on-surface">No weather data yet.</p>
          <p className="mt-1.5 text-[13px] text-on-surface-variant">
            The weather service returned an empty response for this location.
          </p>
        </div>
      )}
    </div>
  );
}
