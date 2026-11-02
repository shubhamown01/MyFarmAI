import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TextInput,
  Pressable,
} from 'react-native';
import { useCropPlans } from '../hooks/useCropPlans';
import { useTheme } from '../theme';
import { spacing, borderRadius } from '../theme/colors';
import { SignInForm, StateScreen } from './DashboardScreen';
import { apiClient, ApiError } from '../lib/api/client';
import { CropPlan, PlanTask, PlanTaskStatus } from '../types/cropPlan';

const formatDate = (value: string) =>
  new Date(value).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

const formatDateTime = (value: string) =>
  new Date(value).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

// Backend dates are YYYY-MM-DD; keep the user honest without a date-picker dep.
const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;
const INVALID_DATE = 'Use the format YYYY-MM-DD (for example 2026-11-01).';

const friendlyError = (error: unknown): string => {
  if (error instanceof ApiError) {
    if (error.code === 'NETWORK_ERROR') {
      return 'You appear to be offline. Check your connection and try again.';
    }
    if (error.code === 'FARM_FORBIDDEN') {
      return "You don't have permission to change this plan.";
    }
    if (error.message) return error.message;
  }
  return 'Something went wrong. Please try again.';
};

type ViewMode = { mode: 'list' } | { mode: 'create' } | { mode: 'detail'; planId: string };

export const CropPlanningScreen: React.FC = () => {
  const { status, farmId, farmName, plans, errorMessage, reload, signIn } =
    useCropPlans();
  const { colors } = useTheme();
  const [view, setView] = useState<ViewMode>({ mode: 'list' });

  if (status === 'loading') {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={[styles.centeredText, { color: colors.onSurfaceVariant }]}>
          Loading crop plans…
        </Text>
      </View>
    );
  }

  if (status === 'signed-out') {
    return <SignInForm onSignIn={signIn} />;
  }

  if (status === 'no-farm') {
    return (
      <StateScreen
        title="No farm yet"
        description="Crop plans live on your farm. Ask your farm's owner to add you, then try again."
        actionLabel="Try again"
        onAction={reload}
      />
    );
  }

  if (status === 'offline') {
    return (
      <StateScreen
        title="You're offline"
        description="Crop plans need a connection. Check your network and try again."
        actionLabel="Try again"
        onAction={reload}
      />
    );
  }

  if (status === 'error' || farmId == null) {
    return (
      <StateScreen
        title="Couldn't load crop plans"
        description={errorMessage || 'Something went wrong. Please try again.'}
        actionLabel="Try again"
        onAction={reload}
      />
    );
  }

  if (view.mode === 'create') {
    return (
      <CreatePlanForm
        farmId={farmId}
        onDone={() => {
          setView({ mode: 'list' });
          reload();
        }}
        onCancel={() => setView({ mode: 'list' })}
      />
    );
  }

  if (view.mode === 'detail') {
    return (
      <PlanDetail
        planId={view.planId}
        onBack={() => {
          setView({ mode: 'list' });
          reload();
        }}
      />
    );
  }

  return (
    <PlansList
      farmName={farmName}
      plans={plans}
      onReload={reload}
      onCreate={() => setView({ mode: 'create' })}
      onOpenPlan={(planId) => setView({ mode: 'detail', planId })}
    />
  );
};

const PlansList: React.FC<{
  farmName: string | null;
  plans: CropPlan[];
  onReload: () => void;
  onCreate: () => void;
  onOpenPlan: (planId: string) => void;
}> = ({ farmName, plans, onReload, onCreate, onOpenPlan }) => {
  const { colors } = useTheme();
  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      accessibilityLabel="Crop plans"
    >
      <View style={styles.headerRow}>
        <Text style={[styles.headerTitle, { color: colors.onSurface }]}>
          {farmName ? `Plans for ${farmName}` : 'Crop plans'}
        </Text>
        <Pressable
          onPress={onReload}
          accessibilityRole="button"
          accessibilityLabel="Refresh crop plans"
          style={({ pressed }) => [
            styles.headerButton,
            {
              backgroundColor: pressed
                ? colors.outlineVariant
                : colors.surfaceContainerHighest,
            },
          ]}
        >
          <Text style={{ color: colors.onSurface }}>Refresh</Text>
        </Pressable>
        <Pressable
          onPress={onCreate}
          accessibilityRole="button"
          accessibilityLabel="New crop plan"
          style={({ pressed }) => [
            styles.headerButton,
            { backgroundColor: pressed ? colors.primaryActive : colors.primary },
          ]}
        >
          <Text style={{ color: colors.onPrimary }}>New plan</Text>
        </Pressable>
      </View>

      {plans.length === 0 ? (
        <View style={[styles.card, { backgroundColor: colors.surfaceContainer }]}>
          <Text style={[styles.body, { color: colors.onSurfaceVariant }]}>
            No crop plans yet. Create one to see milestones for your planting
            date.
          </Text>
        </View>
      ) : (
        plans.map((plan) => (
          <Pressable
            key={plan.id}
            onPress={() => onOpenPlan(plan.id)}
            accessibilityRole="button"
            accessibilityLabel={`Open plan ${plan.variety || 'crop plan'}`}
            style={({ pressed }) => [
              styles.card,
              { backgroundColor: colors.surfaceContainer, opacity: pressed ? 0.7 : 1 },
            ]}
          >
            <Text style={[styles.itemTitle, { color: colors.onSurface }]}>
              {plan.variety || 'Crop plan'}
            </Text>
            <Text style={[styles.body, { color: colors.onSurfaceVariant }]}>
              {plan.planting_date
                ? `Planted ${formatDate(plan.planting_date)}`
                : 'No planting date set'}
            </Text>
            <Text style={[styles.body, { color: colors.onSurfaceVariant }]}>
              {plan.milestones.length} milestone
              {plan.milestones.length === 1 ? '' : 's'} ·{' '}
              {plan.tasks.filter((t) => t.status === 'pending').length} open /{' '}
              {plan.tasks.length} tasks
            </Text>
            <Text style={[styles.lastUpdated, { color: colors.onSurfaceDisabled }]}>
              Updated {formatDateTime(plan.updated_at)}
            </Text>
          </Pressable>
        ))
      )}
    </ScrollView>
  );
};

const CreatePlanForm: React.FC<{
  farmId: string;
  onDone: () => void;
  onCancel: () => void;
}> = ({ farmId, onDone, onCancel }) => {
  const { colors } = useTheme();
  const [variety, setVariety] = useState('');
  const [plantingDate, setPlantingDate] = useState('');
  const [taskTitle, setTaskTitle] = useState('');
  const [taskDue, setTaskDue] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    if (plantingDate && !DATE_PATTERN.test(plantingDate)) {
      setError(INVALID_DATE);
      return;
    }
    if (taskDue && !DATE_PATTERN.test(taskDue)) {
      setError(INVALID_DATE);
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await apiClient.createCropPlan(farmId, {
        ...(variety.trim() ? { variety: variety.trim() } : {}),
        ...(plantingDate ? { planting_date: plantingDate } : {}),
        ...(taskTitle.trim()
          ? {
              tasks: [
                {
                  title: taskTitle.trim(),
                  ...(taskDue ? { due_date: taskDue } : {}),
                },
              ],
            }
          : {}),
      });
      onDone();
    } catch (err) {
      setError(friendlyError(err));
      setSubmitting(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.form} accessibilityLabel="Create crop plan">
      <Text style={[styles.formTitle, { color: colors.onSurface }]}>
        New crop plan
      </Text>
      <TextInput
        style={[
          styles.input,
          { backgroundColor: colors.surface, color: colors.onSurface, borderColor: colors.outline },
        ]}
        placeholder="Variety (optional)"
        placeholderTextColor={colors.onSurfaceDisabled}
        value={variety}
        onChangeText={setVariety}
        maxLength={100}
        accessibilityLabel="Variety"
      />
      <TextInput
        style={[
          styles.input,
          { backgroundColor: colors.surface, color: colors.onSurface, borderColor: colors.outline },
        ]}
        placeholder="Planting date YYYY-MM-DD (optional)"
        placeholderTextColor={colors.onSurfaceDisabled}
        value={plantingDate}
        onChangeText={setPlantingDate}
        autoCapitalize="none"
        accessibilityLabel="Planting date"
      />
      <Text style={[styles.hint, { color: colors.onSurfaceVariant }]}>
        Milestones (sowing and harvest windows) are estimates from generic
        growing-day ranges — variety, local climate and soil are not accounted
        for unless data exists.
      </Text>
      <TextInput
        style={[
          styles.input,
          { backgroundColor: colors.surface, color: colors.onSurface, borderColor: colors.outline },
        ]}
        placeholder="First task (optional)"
        placeholderTextColor={colors.onSurfaceDisabled}
        value={taskTitle}
        onChangeText={setTaskTitle}
        maxLength={200}
        accessibilityLabel="First task title"
      />
      {taskTitle.trim().length > 0 && (
        <TextInput
          style={[
            styles.input,
            { backgroundColor: colors.surface, color: colors.onSurface, borderColor: colors.outline },
          ]}
          placeholder="Task due date YYYY-MM-DD (optional)"
          placeholderTextColor={colors.onSurfaceDisabled}
          value={taskDue}
          onChangeText={setTaskDue}
          autoCapitalize="none"
          accessibilityLabel="Task due date"
        />
      )}
      {error && (
        <Text
          style={[styles.formError, { color: colors.error }]}
          accessibilityLiveRegion="assertive"
        >
          {error}
        </Text>
      )}
      <View style={styles.formRow}>
        <Pressable
          onPress={onCancel}
          accessibilityRole="button"
          accessibilityLabel="Cancel creating plan"
          style={({ pressed }) => [
            styles.submit,
            styles.grow,
            {
              backgroundColor: pressed
                ? colors.outlineVariant
                : colors.surfaceContainerHighest,
            },
          ]}
        >
          <Text style={{ color: colors.onSurface, fontWeight: '600' }}>Back</Text>
        </Pressable>
        <Pressable
          onPress={submit}
          disabled={submitting}
          accessibilityRole="button"
          accessibilityLabel="Create plan"
          accessibilityState={{ disabled: submitting, busy: submitting }}
          style={({ pressed }) => [
            styles.submit,
            styles.grow,
            {
              backgroundColor: pressed ? colors.primaryActive : colors.primary,
              opacity: submitting ? 0.6 : 1,
            },
          ]}
        >
          {submitting ? (
            <ActivityIndicator color={colors.onPrimary} size="small" />
          ) : (
            <Text style={{ color: colors.onPrimary, fontWeight: '600' }}>
              Create plan
            </Text>
          )}
        </Pressable>
      </View>
    </ScrollView>
  );
};

const PlanDetail: React.FC<{ planId: string; onBack: () => void }> = ({
  planId,
  onBack,
}) => {
  const { colors } = useTheme();
  const [plan, setPlan] = useState<CropPlan | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busyTaskId, setBusyTaskId] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [revisions, setRevisions] = useState<
    { id: string; changed_by: string; summary: string; created_at: string }[] | null
  >(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskDue, setNewTaskDue] = useState('');

  const load = useCallback(async () => {
    setLoadError(null);
    try {
      setPlan(await apiClient.getCropPlan(planId));
    } catch (error) {
      setLoadError(friendlyError(error));
    }
  }, [planId]);

  useEffect(() => {
    load();
  }, [load]);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const list = await apiClient.getCropPlanRevisions(planId);
      setRevisions(
        list.map((r) => ({
          id: r.id,
          changed_by: r.changed_by,
          summary: r.summary,
          created_at: r.created_at,
        }))
      );
    } catch (error) {
      setActionError(friendlyError(error));
    } finally {
      setHistoryLoading(false);
    }
  }, [planId]);

  const toggleHistory = () => {
    const next = !showHistory;
    setShowHistory(next);
    if (next && revisions == null) loadHistory();
  };

  const setTaskStatus = async (task: PlanTask, status: PlanTaskStatus) => {
    setBusyTaskId(task.id);
    setActionError(null);
    try {
      const updated = await apiClient.updateCropPlanTask(planId, task.id, {
        status,
      });
      // Cancelled/done tasks stay in the list (soft cancel) — swap in place.
      setPlan((prev) =>
        prev
          ? {
              ...prev,
              tasks: prev.tasks.map((t) => (t.id === updated.id ? { ...t, ...updated } : t)),
            }
          : prev
      );
    } catch (error) {
      setActionError(friendlyError(error));
    } finally {
      setBusyTaskId(null);
    }
  };

  const addTask = async () => {
    if (!newTaskTitle.trim()) return;
    if (newTaskDue && !DATE_PATTERN.test(newTaskDue)) {
      setActionError(INVALID_DATE);
      return;
    }
    setActionError(null);
    try {
      const task = await apiClient.addCropPlanTask(planId, {
        title: newTaskTitle.trim(),
        ...(newTaskDue ? { due_date: newTaskDue } : {}),
      });
      setPlan((prev) => (prev ? { ...prev, tasks: [...prev.tasks, task] } : prev));
      setNewTaskTitle('');
      setNewTaskDue('');
    } catch (error) {
      setActionError(friendlyError(error));
    }
  };

  if (loadError) {
    return (
      <StateScreen
        title="Couldn't load plan"
        description={loadError}
        actionLabel="Try again"
        onAction={load}
      />
    );
  }

  if (!plan) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      accessibilityLabel="Crop plan detail"
    >
      <Pressable
        onPress={onBack}
        accessibilityRole="button"
        accessibilityLabel="Back to plans list"
        style={({ pressed }) => [
          styles.backButton,
          { backgroundColor: pressed ? colors.outlineVariant : colors.surfaceContainerHighest },
        ]}
      >
        <Text style={{ color: colors.onSurface }}>‹ All plans</Text>
      </Pressable>

      <View style={[styles.card, { backgroundColor: colors.surfaceContainer }]}>
        <Text style={[styles.sectionTitle, { color: colors.primary }]}>Plan</Text>
        <Text style={[styles.itemTitle, { color: colors.onSurface }]}>
          {plan.variety || 'Crop plan'}
        </Text>
        <Text style={[styles.body, { color: colors.onSurfaceVariant }]}>
          {plan.planting_date
            ? `Planted ${formatDate(plan.planting_date)}`
            : 'No planting date set'}
        </Text>
      </View>

      {/* Assumptions are rendered verbatim — never paraphrased or elided. */}
      <View style={[styles.card, { backgroundColor: colors.infoContainer }]}>
        <Text style={[styles.sectionTitle, { color: colors.onInfoContainer }]}>
          Assumptions
        </Text>
        <Text style={[styles.body, { color: colors.onInfoContainer }]}>
          {plan.assumptions ?? 'No assumptions recorded.'}
        </Text>
      </View>

      <View style={[styles.card, { backgroundColor: colors.surfaceContainer }]}>
        <Text style={[styles.sectionTitle, { color: colors.primary }]}>
          Milestones
        </Text>
        {plan.milestones.length === 0 ? (
          <Text style={[styles.body, { color: colors.onSurfaceVariant }]}>
            No milestones. Set a planting date to see estimated windows.
          </Text>
        ) : (
          plan.milestones.map((m, i) => (
            <View
              key={`${m.title}-${i}`}
              style={[styles.listItem, { borderBottomColor: colors.outline }]}
            >
              <Text style={[styles.itemTitle, { color: colors.onSurface }]}>
                {m.title}
              </Text>
              <Text style={[styles.body, { color: colors.onSurfaceVariant }]}>
                {formatDate(m.date)}
                {m.note ? ` · ${m.note}` : ''}
              </Text>
            </View>
          ))
        )}
      </View>

      <View style={[styles.card, { backgroundColor: colors.surfaceContainer }]}>
        <Text style={[styles.sectionTitle, { color: colors.primary }]}>Tasks</Text>
        {plan.tasks.length === 0 ? (
          <Text style={[styles.body, { color: colors.onSurfaceVariant }]}>
            No tasks yet.
          </Text>
        ) : (
          plan.tasks.map((task) => {
            const cancelled = task.status === 'cancelled';
            const done = task.status === 'done';
            return (
              <View
                key={task.id}
                style={[styles.listItem, { borderBottomColor: colors.outline }]}
              >
                <Text
                  style={[
                    styles.itemTitle,
                    { color: cancelled ? colors.onSurfaceDisabled : colors.onSurface },
                    (cancelled || done) && styles.struck,
                  ]}
                >
                  {task.title}
                  {cancelled ? '  (cancelled)' : done ? '  ✓' : ''}
                </Text>
                <Text style={[styles.body, { color: colors.onSurfaceVariant }]}>
                  {task.due_date ? `Due ${formatDate(task.due_date)}` : 'No due date'}
                  {` · ${task.source === 'suggested' ? 'suggested' : 'your task'}`}
                  {cancelled ? ' · cancelled — kept for your records' : ''}
                </Text>
                {task.status === 'pending' && (
                  <View style={styles.taskActions}>
                    <Pressable
                      onPress={() => setTaskStatus(task, 'done')}
                      disabled={busyTaskId === task.id}
                      accessibilityRole="button"
                      accessibilityLabel={`Mark ${task.title} done`}
                      accessibilityState={{ disabled: busyTaskId === task.id, busy: busyTaskId === task.id }}
                      style={({ pressed }) => [
                        styles.taskButton,
                        { backgroundColor: pressed ? colors.primaryActive : colors.primary },
                        busyTaskId === task.id && { opacity: 0.6 },
                      ]}
                    >
                      <Text style={{ color: colors.onPrimary }}>Done</Text>
                    </Pressable>
                    <Pressable
                      onPress={() => setTaskStatus(task, 'cancelled')}
                      disabled={busyTaskId === task.id}
                      accessibilityRole="button"
                      accessibilityLabel={`Cancel ${task.title}`}
                      accessibilityState={{ disabled: busyTaskId === task.id, busy: busyTaskId === task.id }}
                      style={({ pressed }) => [
                        styles.taskButton,
                        {
                          backgroundColor: pressed
                            ? colors.outlineVariant
                            : colors.surfaceContainerHighest,
                        },
                        busyTaskId === task.id && { opacity: 0.6 },
                      ]}
                    >
                      <Text style={{ color: colors.onSurface }}>Cancel</Text>
                    </Pressable>
                  </View>
                )}
              </View>
            );
          })
        )}
        {actionError && (
          <Text
            style={[styles.formError, { color: colors.error }]}
            accessibilityLiveRegion="assertive"
          >
            {actionError}
          </Text>
        )}
        <View style={styles.addTaskRow}>
          <TextInput
            style={[
              styles.input,
              styles.grow,
              { backgroundColor: colors.surface, color: colors.onSurface, borderColor: colors.outline },
            ]}
            placeholder="New task title"
            placeholderTextColor={colors.onSurfaceDisabled}
            value={newTaskTitle}
            onChangeText={setNewTaskTitle}
            maxLength={200}
            accessibilityLabel="New task title"
          />
          <TextInput
            style={[
              styles.input,
              styles.dateInput,
              { backgroundColor: colors.surface, color: colors.onSurface, borderColor: colors.outline },
            ]}
            placeholder="YYYY-MM-DD"
            placeholderTextColor={colors.onSurfaceDisabled}
            value={newTaskDue}
            onChangeText={setNewTaskDue}
            autoCapitalize="none"
            accessibilityLabel="New task due date"
          />
          <Pressable
            onPress={addTask}
            disabled={!newTaskTitle.trim()}
            accessibilityRole="button"
            accessibilityLabel="Add task"
            accessibilityState={{ disabled: !newTaskTitle.trim() }}
            style={({ pressed }) => [
              styles.taskButton,
              { backgroundColor: pressed ? colors.primaryActive : colors.primary },
              !newTaskTitle.trim() && { opacity: 0.5 },
            ]}
          >
            <Text style={{ color: colors.onPrimary }}>Add</Text>
          </Pressable>
        </View>
      </View>

      <View style={[styles.card, { backgroundColor: colors.surfaceContainer }]}>
        <Pressable
          onPress={toggleHistory}
          accessibilityRole="button"
          accessibilityLabel={showHistory ? 'Hide plan change history' : 'Show plan change history'}
          accessibilityState={{ expanded: showHistory }}
          style={({ pressed }) => [
            styles.historyToggle,
            { backgroundColor: pressed ? colors.outlineVariant : colors.surfaceContainerHigh },
          ]}
        >
          <Text style={{ color: colors.onSurface }}>
            {showHistory ? 'Hide change history' : 'Show change history'}
          </Text>
        </Pressable>
        {showHistory &&
          (historyLoading ? (
            <ActivityIndicator color={colors.primary} size="small" />
          ) : revisions && revisions.length > 0 ? (
            revisions.map((r) => (
              <View
                key={r.id}
                style={[styles.listItem, { borderBottomColor: colors.outline }]}
              >
                <Text style={[styles.body, { color: colors.onSurface }]}>{r.summary}</Text>
                <Text style={[styles.lastUpdated, { color: colors.onSurfaceDisabled }]}>
                  {formatDateTime(r.created_at)} · by {r.changed_by.slice(0, 8)}…
                </Text>
              </View>
            ))
          ) : (
            <Text style={[styles.body, { color: colors.onSurfaceVariant }]}>
              No recorded changes.
            </Text>
          ))}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  screen: { flex: 1 },
  content: { padding: spacing[4], gap: spacing[4] },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing[6],
    gap: spacing[3],
  },
  centeredText: { textAlign: 'center' },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing[2],
  },
  headerTitle: { flex: 1, fontSize: 18, fontWeight: '600', flexWrap: 'wrap' },
  headerButton: {
    minHeight: 48,
    paddingHorizontal: spacing[4],
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backButton: {
    minHeight: 48,
    alignSelf: 'flex-start',
    paddingHorizontal: spacing[4],
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  card: {
    borderRadius: borderRadius.lg,
    padding: spacing[4],
    gap: spacing[2],
    elevation: 1,
  },
  sectionTitle: { fontSize: 16, fontWeight: '600' },
  body: { fontSize: 14, lineHeight: 20 },
  listItem: { paddingVertical: spacing[2], borderBottomWidth: 1 },
  itemTitle: { fontSize: 15, fontWeight: '500' },
  struck: { textDecorationLine: 'line-through' },
  taskActions: { flexDirection: 'row', gap: spacing[2], marginTop: spacing[1] },
  taskButton: {
    minHeight: 48,
    paddingHorizontal: spacing[4],
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  addTaskRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing[2],
    marginTop: spacing[2],
    flexWrap: 'wrap',
  },
  dateInput: { minWidth: 120, flex: 0 },
  historyToggle: {
    minHeight: 48,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing[4],
  },
  lastUpdated: { fontSize: 12, marginTop: spacing[1] },
  form: {
    padding: spacing[6],
    gap: spacing[3],
  },
  formTitle: { fontSize: 20, fontWeight: '600', textAlign: 'center' },
  formError: { fontSize: 14 },
  formRow: { flexDirection: 'row', gap: spacing[2] },
  hint: { fontSize: 13, lineHeight: 18 },
  input: {
    minHeight: 48,
    borderWidth: 1,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing[4],
    fontSize: 16,
  },
  submit: {
    minHeight: 48,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing[5],
  },
  grow: { flex: 1 },
});

export default CropPlanningScreen;
