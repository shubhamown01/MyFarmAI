'use client';

import { useState } from 'react';
import { AlertTriangle, Info, RotateCcw, Sprout } from 'lucide-react';
import { Badge, Card, CardContent, CardHeader, CardTitle, OfflineIndicator, Spinner } from '@/components/ui';
import type {
  AlertsBlock,
  ActivityBlock,
  CropItem,
  CropsBlock,
  DashboardResponse,
  FarmBlock,
  TasksBlock,
  WeatherBlock,
} from '@/lib/api/types';
import { useDashboard } from './useDashboard';

const dateTimeFormat = new Intl.DateTimeFormat('en-IN', {
  dateStyle: 'medium',
  timeStyle: 'short',
});

const dateFormat = new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' });

function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : dateTimeFormat.format(date);
}

function formatDate(iso: string | null): string {
  if (!iso) return 'Not set';
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : dateFormat.format(date);
}

function UnavailableNotice({ reason }: { reason: string }) {
  return (
    <p className="flex items-start gap-2 text-[14px] leading-6 text-on-surface-variant">
      <Info className="mt-0.5 h-4 w-4 flex-none text-warning" aria-hidden="true" />
      <span>{reason}</span>
    </p>
  );
}

interface BlockCardProps {
  title: string;
  available: boolean;
  reason?: string | null;
  updatedAt?: string;
  children: React.ReactNode;
}

function BlockCard({ title, available, reason, updatedAt, children }: BlockCardProps) {
  return (
    <Card variant="outlined">
      <CardHeader className="px-4 py-3 sm:px-5">
        <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
          <CardTitle className="text-[15px]">{title}</CardTitle>
          {available && updatedAt && (
            <span className="text-[12px] text-on-surface-variant">
              Last updated {formatTimestamp(updatedAt)}
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent className="px-4 py-4 sm:px-5">
        {available ? children : <UnavailableNotice reason={reason || 'This data is currently unavailable.'} />}
      </CardContent>
    </Card>
  );
}

function FarmCardContent({ farm }: { farm: FarmBlock }) {
  const coordinates =
    farm.latitude !== null && farm.longitude !== null
      ? `${farm.latitude.toFixed(4)}, ${farm.longitude.toFixed(4)}`
      : null;
  return (
    <div>
      <p className="text-[20px] font-bold tracking-[-0.015em] text-on-surface">{farm.name}</p>
      {farm.address && <p className="mt-1 text-[14px] text-on-surface-variant">{farm.address}</p>}
      <p className="mt-1 text-[13px] text-on-surface-variant">
        Timezone {farm.timezone}
        {coordinates ? ` · ${coordinates}` : ''}
      </p>
    </div>
  );
}

function WeatherCardContent({ weather }: { weather: WeatherBlock }) {
  return (
    <div>
      <p className="text-[28px] font-bold leading-8 tracking-[-0.02em] text-on-surface">
        {weather.temperature !== null ? `${Math.round(weather.temperature)}°C` : '—'}
      </p>
      <p className="mt-1 text-[14px] text-on-surface-variant">
        {weather.conditions || 'No condition reported'}
        {weather.windspeed !== null ? ` · Wind ${Math.round(weather.windspeed)} km/h` : ''}
      </p>
      <p className="mt-2 text-[12px] text-on-surface-variant">
        Weather data by{' '}
        <a
          href="https://open-meteo.com/"
          target="_blank"
          rel="noreferrer"
          className="underline decoration-outline underline-offset-2 hover:text-on-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          Open-Meteo
        </a>{' '}
        (CC-BY 4.0)
      </p>
    </div>
  );
}

function CropsCardContent({ crops }: { crops: CropsBlock }) {
  if (!crops.cycles.length) {
    return <p className="text-[14px] text-on-surface-variant">No crop cycles recorded yet.</p>;
  }
  return (
    <ul role="list" className="space-y-3">
      {crops.cycles.map((cycle: CropItem, index) => (
        <li
          key={`${cycle.crop}-${cycle.season_year}-${index}`}
          className="flex flex-wrap items-center gap-2 text-[14px]"
        >
          <span className="font-semibold text-on-surface">{cycle.crop}</span>
          <Badge variant="default" size="sm">
            {cycle.status}
          </Badge>
          <span className="text-on-surface-variant">
            {cycle.season_year} · Planted {formatDate(cycle.planting_date)} · Harvest{' '}
            {formatDate(cycle.expected_harvest_date)}
          </span>
        </li>
      ))}
    </ul>
  );
}

function TasksCardContent({ tasks }: { tasks: TasksBlock }) {
  if (!tasks.items.length) {
    return <p className="text-[14px] text-on-surface-variant">No upcoming tasks.</p>;
  }
  return (
    <ul role="list" className="space-y-3">
      {tasks.items.map((task, index) => (
        <li key={`${task.title}-${index}`} className="text-[14px]">
          <span className="font-medium text-on-surface">{task.title}</span>
          <span className="text-on-surface-variant">
            {' '}
            · {task.crop} · Due {formatDate(task.due_date)}
          </span>
        </li>
      ))}
    </ul>
  );
}

const ALERT_BADGE_VARIANT: Record<string, 'error' | 'warning' | 'info'> = {
  error: 'error',
  critical: 'error',
  warning: 'warning',
  info: 'info',
};

function AlertsCardContent({ alerts }: { alerts: AlertsBlock }) {
  if (!alerts.items.length) {
    return <p className="text-[14px] text-on-surface-variant">No alerts for your farm.</p>;
  }
  return (
    <ul role="list" className="space-y-3">
      {alerts.items.map((alert, index) => (
        <li key={`${alert.severity}-${index}`} className="flex flex-wrap items-center gap-2 text-[14px]">
          <AlertTriangle
            className={alert.severity === 'error' || alert.severity === 'critical' ? 'h-4 w-4 text-error' : 'h-4 w-4 text-warning'}
            aria-hidden="true"
          />
          <Badge variant={ALERT_BADGE_VARIANT[alert.severity] ?? 'info'} size="sm">
            {alert.severity}
          </Badge>
          <span className="text-on-surface">{alert.message}</span>
        </li>
      ))}
    </ul>
  );
}

function ActivityCardContent({ activity }: { activity: ActivityBlock }) {
  if (!activity.items.length) {
    return <p className="text-[14px] text-on-surface-variant">No recent activity.</p>;
  }
  return (
    <ul role="list" className="space-y-3">
      {activity.items.map((item, index) => (
        <li key={`${item.event_type}-${index}`} className="text-[14px]">
          <span className="font-medium text-on-surface">{item.description || item.event_type}</span>
          <span className="text-on-surface-variant"> · {formatTimestamp(item.occurred_at)}</span>
        </li>
      ))}
    </ul>
  );
}

export function FarmIntelligenceBlocks({ data, offline }: { data: DashboardResponse; offline: boolean }) {
  return (
    <div>
      {offline && (
        <p
          role="status"
          className="mb-4 rounded-lg bg-warning-container px-4 py-2 text-[13px] font-medium text-on-warning-container"
        >
          You're offline — showing the last loaded farm data.
        </p>
      )}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <BlockCard title="Farm" available={data.farm.available} updatedAt={data.farm.updated_at}>
          <FarmCardContent farm={data.farm} />
        </BlockCard>
        <BlockCard
          title="Weather"
          available={data.weather.available}
          reason={data.weather.unavailable_reason}
          updatedAt={data.weather.updated_at}
        >
          <WeatherCardContent weather={data.weather} />
        </BlockCard>
        <BlockCard
          title="Crops"
          available={data.crops.available}
          reason={data.crops.unavailable_reason}
          updatedAt={data.crops.updated_at}
        >
          <CropsCardContent crops={data.crops} />
        </BlockCard>
        <BlockCard
          title="Upcoming Tasks"
          available={data.tasks.available}
          reason={data.tasks.unavailable_reason}
          updatedAt={data.tasks.updated_at}
        >
          <TasksCardContent tasks={data.tasks} />
        </BlockCard>
        <BlockCard title="Alerts" available={data.alerts.available} updatedAt={data.alerts.updated_at}>
          <AlertsCardContent alerts={data.alerts} />
        </BlockCard>
        <BlockCard
          title="Saved Recommendations"
          available={data.recommendations.available}
          reason={data.recommendations.unavailable_reason}
        >
          <p className="text-[14px] text-on-surface-variant">No recommendations saved yet.</p>
        </BlockCard>
        <BlockCard
          title="Recent Activity"
          available={data.activity.available}
          reason={data.activity.unavailable_reason}
          updatedAt={data.activity.updated_at}
          // Farm activity spans the full width on wide screens.
        >
          <ActivityCardContent activity={data.activity} />
        </BlockCard>
      </div>
    </div>
  );
}

function NoFarmEmptyState() {
  return (
    <div
      role="status"
      className="rounded-2xl border border-outline bg-surface-container px-6 py-10 text-center"
    >
      <Sprout className="mx-auto h-10 w-10 text-primary" aria-hidden="true" />
      <h3 className="mt-3 text-[17px] font-semibold text-on-surface">No farm yet</h3>
      <p className="mx-auto mt-2 max-w-md text-[14px] leading-6 text-on-surface-variant">
        Create your farm to see live crop, weather, task, and activity data here. Farm setup is not
        available on the web yet — create one through the API or mobile app, then revisit this page.
      </p>
    </div>
  );
}

export function FarmIntelligence() {
  const state = useDashboard();

  return (
    <section className="mt-8" aria-labelledby="farm-overview-heading">
      <OfflineIndicator />
      <h2 id="farm-overview-heading" className="mb-4 text-[20px] font-bold tracking-[-0.015em] text-on-surface">
        Your Farm
      </h2>

      {state.phase === 'loading' && <Spinner label="Loading your farm overview" />}

      {state.phase === 'offline' && (
        <p role="status" className="text-[14px] text-on-surface-variant">
          You're offline — your farm overview will refresh when you reconnect.
        </p>
      )}

      {state.phase === 'no-farm' && <NoFarmEmptyState />}

      {state.phase === 'error' && (
        <div role="alert" className="rounded-2xl border border-outline bg-surface p-5">
          <p className="text-[14px] leading-6 text-error">{state.message}</p>
          <button
            type="button"
            onClick={state.retry}
            className="mt-3 inline-flex min-h-[44px] items-center gap-1.5 rounded-lg border border-outline px-3 text-[13px] font-semibold text-on-surface transition-colors hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          >
            <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
            Try again
          </button>
        </div>
      )}

      {state.phase === 'ready' && (
        <FarmIntelligenceBlocks data={state.data} offline={state.offline} />
      )}
    </section>
  );
}
