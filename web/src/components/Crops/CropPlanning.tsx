'use client';

import { useId, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CalendarDays, History, Info, Leaf, Plus, RotateCcw, Sprout } from 'lucide-react';
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  Input,
  OfflineIndicator,
  Spinner,
} from '@/components/ui';
import { ApiError, apiClient } from '@/lib/api/client';
import type {
  CropPlan,
  CropPlanTask,
  PlanTaskStatus,
} from '@/lib/api/types';
import { useCropPlans } from './useCropPlans';

const STALE_TIME = 1000 * 60 * 5; // 5 minutes, matching the app-wide query default

const dateFormat = new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' });

function formatDate(iso: string | null): string {
  if (!iso) return 'Not set';
  const date = new Date(`${iso}T00:00:00`);
  return Number.isNaN(date.getTime()) ? iso : dateFormat.format(date);
}

function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : dateFormat.format(date);
}

function mutationMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError && error.message) return error.message;
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

// ---------------------------------------------------------------------------
// List view
// ---------------------------------------------------------------------------

function PlanListItem({
  plan,
  onOpen,
}: {
  plan: CropPlan;
  onOpen: (planId: string) => void;
}) {
  const pending = plan.tasks.filter((task) => task.status === 'pending').length;
  return (
    <li>
      <Card variant="outlined">
        <CardContent className="flex flex-wrap items-center justify-between gap-3 px-4 py-4 sm:px-5">
          <div className="min-w-0">
            <p className="text-[15px] font-semibold text-on-surface">
              {plan.variety || 'Untitled plan'}
            </p>
            <p className="mt-1 text-[13px] text-on-surface-variant">
              Planted {formatDate(plan.planting_date)} · {plan.tasks.length} task
              {plan.tasks.length === 1 ? '' : 's'}
              {pending > 0 ? ` · ${pending} pending` : ''}
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={() => onOpen(plan.id)}>
            View plan
          </Button>
        </CardContent>
      </Card>
    </li>
  );
}

// ---------------------------------------------------------------------------
// Create form
// ---------------------------------------------------------------------------

function CreatePlanForm({
  farmId,
  onCreated,
}: {
  farmId: string;
  onCreated: (plan: CropPlan) => void;
}) {
  const queryClient = useQueryClient();
  const cycleSelectId = useId();
  const [variety, setVariety] = useState('');
  const [plantingDate, setPlantingDate] = useState('');
  const [cycleId, setCycleId] = useState('');
  const [firstTask, setFirstTask] = useState('');
  const [error, setError] = useState<string | null>(null);

  const cyclesQuery = useQuery({
    queryKey: ['crop-cycles', farmId],
    queryFn: () => apiClient.getCropCycles(farmId),
    staleTime: STALE_TIME,
    retry: 1,
  });
  const activeCycles = (cyclesQuery.data ?? []).filter(
    (cycle) => cycle.status === 'active'
  );

  const createMutation = useMutation({
    mutationFn: () =>
      apiClient.createCropPlan(farmId, {
        variety: variety.trim() || null,
        planting_date: plantingDate || null,
        crop_cycle_id: cycleId || null,
        tasks: firstTask.trim()
          ? [{ title: firstTask.trim(), due_date: null }]
          : [],
      }),
    onSuccess: (plan) => {
      queryClient.invalidateQueries({ queryKey: ['crop-plans'] });
      setVariety('');
      setPlantingDate('');
      setCycleId('');
      setFirstTask('');
      setError(null);
      onCreated(plan);
    },
    onError: (err) =>
      setError(mutationMessage(err, 'Your plan could not be created.')),
  });

  return (
    <Card variant="outlined">
      <CardHeader className="px-4 py-3 sm:px-5">
        <h2 className="text-[15px] font-semibold text-on-surface">Create a crop plan</h2>
      </CardHeader>
      <CardContent className="px-4 py-4 sm:px-5">
        <form
          className="grid gap-4 sm:grid-cols-2"
          onSubmit={(event) => {
            event.preventDefault();
            createMutation.mutate();
          }}
        >
          <Input
            label="Variety"
            value={variety}
            onChange={(event) => setVariety(event.target.value)}
            maxLength={100}
            placeholder="e.g. Lokwan wheat"
          />
          <Input
            label="Planting date"
            type="date"
            value={plantingDate}
            onChange={(event) => setPlantingDate(event.target.value)}
          />
          <div>
            <label
              htmlFor={cycleSelectId}
              className="mb-1.5 block text-label-large text-on-surface"
            >
              Link a crop cycle (optional)
            </label>
            <select
              id={cycleSelectId}
              value={cycleId}
              onChange={(event) => setCycleId(event.target.value)}
              className="w-full rounded-md border border-outline bg-surface px-4 py-2.5 text-on-surface transition-colors duration-fast ease-out-quick hover:border-outline-strong focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary disabled:bg-surface-container-low disabled:text-on-surface-disabled"
            >
              <option value="">No linked cycle</option>
              {activeCycles.map((cycle) => (
                <option key={cycle.id} value={cycle.id}>
                  Season {cycle.season_year}
                  {cycle.season_name ? ` · ${cycle.season_name}` : ''} ·{' '}
                  {cycle.status}
                </option>
              ))}
            </select>
          </div>
          <Input
            label="First task (optional)"
            value={firstTask}
            onChange={(event) => setFirstTask(event.target.value)}
            maxLength={200}
            placeholder="e.g. Prepare seedbed"
            helperText="Milestones are estimates — add your own tasks to track real work."
          />
          {error && (
            <p role="alert" className="text-body-small text-error sm:col-span-2">
              {error}
            </p>
          )}
          <div className="sm:col-span-2">
            <Button type="submit" loading={createMutation.isPending}>
              <Plus className="h-4 w-4" aria-hidden="true" />
              Create plan
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Plan detail — milestones, assumptions, tasks, revision history
// ---------------------------------------------------------------------------

function TaskRow({
  planId,
  task,
}: {
  planId: string;
  task: CropPlanTask;
}) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const statusMutation = useMutation({
    mutationFn: (status: PlanTaskStatus) =>
      apiClient.updateCropPlanTask(planId, task.id, { status }),
    onSuccess: () => {
      // User tasks are never deleted — soft status changes only, so the
      // cancelled task stays visible in the refreshed detail.
      queryClient.invalidateQueries({ queryKey: ['crop-plan', planId] });
      queryClient.invalidateQueries({ queryKey: ['crop-plans'] });
      setError(null);
    },
    onError: (err) =>
      setError(mutationMessage(err, 'The task could not be updated.')),
  });

  const cancelled = task.status === 'cancelled';
  const done = task.status === 'done';

  return (
    <li className="text-[14px]">
      <div className="flex flex-wrap items-center gap-2">
        <span
          className={
            cancelled
              ? 'text-on-surface-variant line-through'
              : done
                ? 'text-on-surface-variant'
                : 'font-medium text-on-surface'
          }
        >
          {task.title}
        </span>
        {task.source === 'suggested' && (
          <Badge variant="info" size="sm">
            suggested
          </Badge>
        )}
        {done && (
          <Badge variant="success" size="sm">
            done
          </Badge>
        )}
        {cancelled && (
          <Badge variant="outline" size="sm">
            cancelled
          </Badge>
        )}
      </div>
      <p className="mt-0.5 text-[12px] text-on-surface-variant">
        Due {formatDate(task.due_date)}
      </p>
      {task.status === 'pending' && (
        <div className="mt-2 flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            loading={statusMutation.isPending}
            onClick={() => statusMutation.mutate('done')}
          >
            Mark done
          </Button>
          <Button
            variant="ghost"
            size="sm"
            loading={statusMutation.isPending}
            onClick={() => statusMutation.mutate('cancelled')}
          >
            Cancel task
          </Button>
        </div>
      )}
      {error && (
        <p role="alert" className="mt-1 text-body-small text-error">
          {error}
        </p>
      )}
    </li>
  );
}

function AddTaskForm({ planId }: { planId: string }) {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [error, setError] = useState<string | null>(null);

  const addMutation = useMutation({
    mutationFn: () =>
      apiClient.addCropPlanTask(planId, {
        title: title.trim(),
        due_date: dueDate || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crop-plan', planId] });
      queryClient.invalidateQueries({ queryKey: ['crop-plans'] });
      setTitle('');
      setDueDate('');
      setError(null);
    },
    onError: (err) =>
      setError(mutationMessage(err, 'The task could not be added.')),
  });

  return (
    <form
      className="grid gap-3 sm:grid-cols-[1fr_auto_auto] sm:items-end"
      onSubmit={(event) => {
        event.preventDefault();
        if (title.trim()) addMutation.mutate();
      }}
    >
      <Input
        label="New task"
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        maxLength={200}
        placeholder="e.g. Apply basal dose"
        required
      />
      <Input
        label="Due date"
        type="date"
        value={dueDate}
        onChange={(event) => setDueDate(event.target.value)}
      />
      <Button type="submit" loading={addMutation.isPending}>
        Add task
      </Button>
      {error && (
        <p role="alert" className="text-body-small text-error sm:col-span-3">
          {error}
        </p>
      )}
    </form>
  );
}

function RevisionHistory({ planId }: { planId: string }) {
  const revisionsQuery = useQuery({
    queryKey: ['crop-plan-revisions', planId],
    queryFn: () => apiClient.getCropPlanRevisions(planId),
    staleTime: STALE_TIME,
    retry: 1,
  });

  if (revisionsQuery.isLoading) {
    return <Spinner label="Loading revision history" />;
  }
  if (revisionsQuery.error) {
    return (
      <p role="alert" className="text-[14px] text-error">
        {mutationMessage(revisionsQuery.error, 'Revision history could not be loaded.')}
      </p>
    );
  }
  const revisions = revisionsQuery.data ?? [];
  if (!revisions.length) {
    return (
      <p className="text-[14px] text-on-surface-variant">No revisions recorded yet.</p>
    );
  }
  return (
    <ul role="list" className="space-y-2">
      {revisions.map((revision) => (
        <li key={revision.id} className="text-[14px]">
          <span className="font-medium text-on-surface">{revision.summary}</span>
          <span className="text-on-surface-variant">
            {' '}
            · {formatTimestamp(revision.created_at)}
          </span>
        </li>
      ))}
    </ul>
  );
}

function PlanDetail({ planId, onBack }: { planId: string; onBack: () => void }) {
  const [showRevisions, setShowRevisions] = useState(false);
  const planQuery = useQuery({
    queryKey: ['crop-plan', planId],
    queryFn: () => apiClient.getCropPlan(planId),
    staleTime: STALE_TIME,
    retry: 1,
  });

  if (planQuery.isLoading) {
    return <Spinner label="Loading plan" />;
  }
  if (planQuery.error || !planQuery.data) {
    return (
      <div role="alert" className="rounded-2xl border border-outline bg-surface p-5">
        <p className="text-[14px] leading-6 text-error">
          {mutationMessage(planQuery.error, 'This plan could not be loaded.')}
        </p>
        <Button variant="outline" size="sm" className="mt-3" onClick={() => planQuery.refetch()}>
          <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
          Try again
        </Button>
      </div>
    );
  }

  const plan = planQuery.data;

  return (
    <div>
      <Button variant="ghost" size="sm" onClick={onBack}>
        <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
        All plans
      </Button>

      <Card variant="outlined" className="mt-3">
        <CardHeader className="px-4 py-3 sm:px-5">
          <h2 className="text-[17px] font-semibold text-on-surface">{plan.variety || 'Untitled plan'}</h2>
        </CardHeader>
        <CardContent className="px-4 py-4 sm:px-5">
          <p className="flex items-center gap-2 text-[14px] text-on-surface-variant">
            <CalendarDays className="h-4 w-4 flex-none" aria-hidden="true" />
            Planting date: {formatDate(plan.planting_date)}
          </p>

          <h2 className="mt-5 flex items-center gap-2 text-[14px] font-semibold text-on-surface">
            <Info className="h-4 w-4 text-primary" aria-hidden="true" />
            Assumptions
          </h2>
          {/* Displayed verbatim — it explains that milestones are estimates. */}
          <p className="mt-1 rounded-lg bg-surface-container-low px-3 py-2 text-[13px] leading-6 text-on-surface-variant">
            {plan.assumptions}
          </p>

          <h2 className="mt-5 text-[14px] font-semibold text-on-surface">
            Expected milestones
          </h2>
          {plan.milestones.length ? (
            <ul role="list" className="mt-1 space-y-2">
              {plan.milestones.map((milestone, index) => (
                <li
                  key={`${milestone.title}-${index}`}
                  className="text-[14px]"
                >
                  <span className="font-medium text-on-surface">{milestone.title}</span>
                  <span className="text-on-surface-variant">
                    {' '}
                    · {formatDate(milestone.date)}
                    {milestone.note ? ` · ${milestone.note}` : ''}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-1 text-[14px] text-on-surface-variant">
              No milestones — set a planting date to see estimates.
            </p>
          )}

          <h2 className="mt-5 text-[14px] font-semibold text-on-surface">Tasks</h2>
          {plan.tasks.length ? (
            <ul role="list" className="mt-1 space-y-3">
              {plan.tasks.map((task) => (
                <TaskRow key={task.id} planId={plan.id} task={task} />
              ))}
            </ul>
          ) : (
            <p className="mt-1 text-[14px] text-on-surface-variant">No tasks yet.</p>
          )}
          <div className="mt-4">
            <AddTaskForm planId={plan.id} />
          </div>

          <h2 className="mt-5 text-[14px] font-semibold text-on-surface">
            <span className="inline-flex items-center gap-2">
              <History className="h-4 w-4 text-primary" aria-hidden="true" />
              Plan history
            </span>
          </h2>
          <div className="mt-2">
            <Button
              variant="outline"
              size="sm"
              aria-expanded={showRevisions}
              onClick={() => setShowRevisions((visible) => !visible)}
            >
              {showRevisions ? 'Hide revision history' : 'View revision history'}
            </Button>
          </div>
          {showRevisions && (
            <div className="mt-3">
              <RevisionHistory planId={plan.id} />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Top-level view
// ---------------------------------------------------------------------------

function NoFarmEmptyState() {
  return (
    <div
      role="status"
      className="rounded-2xl border border-outline bg-surface-container px-6 py-10 text-center"
    >
      <Sprout className="mx-auto h-10 w-10 text-primary" aria-hidden="true" />
      <h2 className="mt-3 text-[17px] font-semibold text-on-surface">No farm yet</h2>
      <p className="mx-auto mt-2 max-w-md text-[14px] leading-6 text-on-surface-variant">
        Create your farm to plan crops here. Farm setup is not available on the
        web yet — create one through the API or mobile app, then revisit this page.
      </p>
    </div>
  );
}

export function CropPlanning() {
  const state = useCropPlans();
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);

  return (
    <section aria-labelledby="crop-planning-heading">
      <OfflineIndicator />
      <h1
        id="crop-planning-heading"
        className="text-[28px] font-bold tracking-[-0.025em] text-on-surface sm:text-[32px]"
      >
        Crop Planning
      </h1>
      <p className="mt-1 text-[15px] text-on-surface-variant">
        Season plans with estimated milestones from growing-day ranges. Your own
        tasks are yours — the system never deletes them.
      </p>

      {state.phase === 'loading' && <Spinner label="Loading your crop plans" />}

      {state.phase === 'offline' && (
        <p role="status" className="mt-4 text-[14px] text-on-surface-variant">
          You're offline — your crop plans will refresh when you reconnect.
        </p>
      )}

      {state.phase === 'no-farm' && (
        <div className="mt-6">
          <NoFarmEmptyState />
        </div>
      )}

      {state.phase === 'error' && (
        <div role="alert" className="mt-6 rounded-2xl border border-outline bg-surface p-5">
          <p className="text-[14px] leading-6 text-error">{state.message}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={state.retry}>
            <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
            Try again
          </Button>
        </div>
      )}

      {state.phase === 'ready' && (
        <div className="mt-6">
          {selectedPlanId ? (
            <PlanDetail
              planId={selectedPlanId}
              onBack={() => setSelectedPlanId(null)}
            />
          ) : (
            <>
              {state.plans.length ? (
                <ul role="list" className="space-y-3">
                  {state.plans.map((plan) => (
                    <PlanListItem
                      key={plan.id}
                      plan={plan}
                      onOpen={setSelectedPlanId}
                    />
                  ))}
                </ul>
              ) : (
                <div
                  role="status"
                  className="rounded-2xl border border-dashed border-outline-strong bg-surface p-6 text-center"
                >
                  <Leaf className="mx-auto h-8 w-8 text-primary" aria-hidden="true" />
                  <p className="mt-2 text-[15px] font-semibold text-on-surface">
                    No plans yet
                  </p>
                  <p className="mx-auto mt-1 max-w-md text-[13px] leading-5 text-on-surface-variant">
                    Create your first plan below — pick a variety and planting
                    date and the season milestones are estimated for you.
                  </p>
                </div>
              )}
              <div className="mt-6">
                <CreatePlanForm
                  farmId={state.farmId}
                  onCreated={(plan) => setSelectedPlanId(plan.id)}
                />
              </div>
            </>
          )}
        </div>
      )}
    </section>
  );
}
