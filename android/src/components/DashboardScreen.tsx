import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TextInput,
  Pressable,
} from 'react-native';
import { useDashboard } from '../hooks/useDashboard';
import { useTheme } from '../theme';
import { spacing, borderRadius } from '../theme/colors';

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

export const DashboardScreen: React.FC = () => {
  const { status, dashboard, errorMessage, reload, signIn, signOut } =
    useDashboard();
  const { colors } = useTheme();

  if (status === 'loading') {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={[styles.centeredText, { color: colors.onSurfaceVariant }]}>
          Loading your farm…
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
        description="You're not part of a farm yet. Ask your farm's owner to add you, then pull down to try again."
        actionLabel="Try again"
        onAction={reload}
      />
    );
  }

  if (status === 'offline') {
    return (
      <StateScreen
        title="You're offline"
        description="Your farm dashboard needs a connection. Check your network and try again."
        actionLabel="Try again"
        onAction={reload}
      />
    );
  }

  if (status === 'error' || !dashboard) {
    return (
      <StateScreen
        title="Couldn't load dashboard"
        description={errorMessage || 'Something went wrong. Please try again.'}
        actionLabel="Try again"
        onAction={reload}
      />
    );
  }

  const { farm, crops, weather, tasks, alerts, recommendations, activity } =
    dashboard;

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      accessibilityLabel="Farm dashboard"
    >
      <View style={styles.headerRow}>
        <Text style={[styles.generatedAt, { color: colors.onSurfaceVariant }]}>
          Updated {formatDateTime(dashboard.generated_at)}
        </Text>
        <Pressable
          onPress={reload}
          accessibilityRole="button"
          accessibilityLabel="Refresh dashboard"
          accessibilityState={{ busy: false }}
          style={({ pressed }) => [
            styles.headerButton,
            { backgroundColor: pressed ? colors.primaryActive : colors.primary },
          ]}
        >
          <Text style={{ color: colors.onPrimary }}>Refresh</Text>
        </Pressable>
        <Pressable
          onPress={signOut}
          accessibilityRole="button"
          accessibilityLabel="Sign out"
          style={({ pressed }) => [
            styles.headerButton,
            {
              backgroundColor: pressed
                ? colors.outlineVariant
                : colors.surfaceContainerHighest,
            },
          ]}
        >
          <Text style={{ color: colors.onSurface }}>Sign out</Text>
        </Pressable>
      </View>

      {/* Farm overview */}
      <SectionCard title="Farm" colors={colors}>
        <Text style={[styles.farmName, { color: colors.onSurface }]}>
          {farm.name}
        </Text>
        {!!farm.address && (
          <Text style={[styles.body, { color: colors.onSurfaceVariant }]}>
            {farm.address}
          </Text>
        )}
        <Text style={[styles.body, { color: colors.onSurfaceVariant }]}>
          Timezone: {farm.timezone}
        </Text>
        {farm.latitude != null && farm.longitude != null && (
          <Text style={[styles.body, { color: colors.onSurfaceVariant }]}>
            {farm.latitude.toFixed(4)}, {farm.longitude.toFixed(4)}
          </Text>
        )}
        <LastUpdated value={farm.updated_at} colors={colors} />
      </SectionCard>

      {/* Crops */}
      <SectionCard title="Crops" colors={colors}>
        {crops.available && crops.cycles.length > 0 ? (
          crops.cycles.map((cycle, i) => (
            <View
              key={`${cycle.crop}-${cycle.season_year}-${i}`}
              style={[styles.listItem, { borderBottomColor: colors.outline }]}
            >
              <Text style={[styles.itemTitle, { color: colors.onSurface }]}>
                {cycle.crop} · {cycle.season_year}
              </Text>
              <Text style={[styles.body, { color: colors.onSurfaceVariant }]}>
                Status: {cycle.status}
                {cycle.planting_date ? ` · Planted ${formatDate(cycle.planting_date)}` : ''}
                {cycle.expected_harvest_date
                  ? ` · Harvest ${formatDate(cycle.expected_harvest_date)}`
                  : ''}
              </Text>
            </View>
          ))
        ) : (
          <Unavailable
            colors={colors}
            reason={crops.unavailable_reason || 'No active crop cycles'}
          />
        )}
        <LastUpdated value={crops.updated_at} colors={colors} />
      </SectionCard>

      {/* Weather */}
      <SectionCard title="Weather" colors={colors}>
        {weather.available ? (
          <>
            <Text style={[styles.weatherValue, { color: colors.primary }]}>
              {weather.temperature != null
                ? `${Math.round(weather.temperature)}°C`
                : '—'}
              {weather.conditions ? ` · ${weather.conditions}` : ''}
            </Text>
            {weather.windspeed != null && (
              <Text style={[styles.body, { color: colors.onSurfaceVariant }]}>
                Wind: {Math.round(weather.windspeed)} km/h
              </Text>
            )}
          </>
        ) : (
          <Unavailable
            colors={colors}
            reason={weather.unavailable_reason || 'Weather is unavailable right now'}
          />
        )}
        <LastUpdated value={weather.updated_at} colors={colors} />
      </SectionCard>

      {/* Tasks */}
      <SectionCard title="Upcoming tasks" colors={colors}>
        {tasks.available && tasks.items.length > 0 ? (
          tasks.items.map((task, i) => (
            <View
              key={`${task.title}-${i}`}
              style={[styles.listItem, { borderBottomColor: colors.outline }]}
            >
              <Text style={[styles.itemTitle, { color: colors.onSurface }]}>
                {task.title}
              </Text>
              <Text style={[styles.body, { color: colors.onSurfaceVariant }]}>
                Due {formatDate(task.due_date)} · {task.crop}
              </Text>
            </View>
          ))
        ) : (
          <Unavailable
            colors={colors}
            reason={tasks.unavailable_reason || 'No upcoming tasks'}
          />
        )}
        <LastUpdated value={tasks.updated_at} colors={colors} />
      </SectionCard>

      {/* Alerts */}
      <SectionCard title="Alerts" colors={colors}>
        {alerts.available && alerts.items.length > 0 ? (
          alerts.items.map((alert, i) => {
            const container =
              alert.severity === 'error'
                ? colors.errorContainer
                : alert.severity === 'warning'
                  ? colors.warningContainer
                  : colors.infoContainer;
            const onContainer =
              alert.severity === 'error'
                ? colors.onErrorContainer
                : alert.severity === 'warning'
                  ? colors.onWarningContainer
                  : colors.onInfoContainer;
            return (
              <View
                key={`${alert.message}-${i}`}
                style={[styles.alertItem, { backgroundColor: container }]}
                accessibilityLiveRegion="polite"
              >
                <Text style={[styles.body, { color: onContainer }]}>
                  {alert.message}
                </Text>
              </View>
            );
          })
        ) : (
          <Unavailable colors={colors} reason="No active alerts" />
        )}
        <LastUpdated value={alerts.updated_at} colors={colors} />
      </SectionCard>

      {/* Recommendations — honest empty state until the feature exists */}
      <SectionCard title="Recommendations" colors={colors}>
        <Unavailable colors={colors} reason={recommendations.unavailable_reason} />
      </SectionCard>

      {/* Activity */}
      <SectionCard title="Recent activity" colors={colors}>
        {activity.available && activity.items.length > 0 ? (
          activity.items.map((event, i) => (
            <View
              key={`${event.event_type}-${i}`}
              style={[styles.listItem, { borderBottomColor: colors.outline }]}
            >
              <Text style={[styles.itemTitle, { color: colors.onSurface }]}>
                {event.event_type.replace(/_/g, ' ')}
              </Text>
              {!!event.description && (
                <Text style={[styles.body, { color: colors.onSurfaceVariant }]}>
                  {event.description}
                </Text>
              )}
              <Text style={[styles.body, { color: colors.onSurfaceDisabled }]}>
                {formatDateTime(event.occurred_at)}
              </Text>
            </View>
          ))
        ) : (
          <Unavailable
            colors={colors}
            reason={activity.unavailable_reason || 'No recent activity'}
          />
        )}
        <LastUpdated value={activity.updated_at} colors={colors} />
      </SectionCard>
    </ScrollView>
  );
};

const SignInForm: React.FC<{ onSignIn: (email: string, password: string) => Promise<string | null> }> = ({
  onSignIn,
}) => {
  const { colors } = useTheme();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    setSubmitting(true);
    setError(null);
    const failure = await onSignIn(email.trim(), password);
    if (failure) {
      setError(failure);
      setSubmitting(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.form}>
      <Text style={[styles.formTitle, { color: colors.onSurface }]}>
        Sign in to see your farm
      </Text>
      <TextInput
        style={[
          styles.input,
          {
            backgroundColor: colors.surface,
            color: colors.onSurface,
            borderColor: colors.outline,
          },
        ]}
        placeholder="Email"
        placeholderTextColor={colors.onSurfaceDisabled}
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        keyboardType="email-address"
        accessibilityLabel="Email"
      />
      <TextInput
        style={[
          styles.input,
          {
            backgroundColor: colors.surface,
            color: colors.onSurface,
            borderColor: colors.outline,
          },
        ]}
        placeholder="Password"
        placeholderTextColor={colors.onSurfaceDisabled}
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        accessibilityLabel="Password"
      />
      {error && (
        <Text
          style={[styles.formError, { color: colors.error }]}
          accessibilityLiveRegion="assertive"
        >
          {error}
        </Text>
      )}
      <Pressable
        onPress={submit}
        disabled={submitting}
        accessibilityRole="button"
        accessibilityLabel="Sign in"
        accessibilityState={{ disabled: submitting, busy: submitting }}
        style={({ pressed }) => [
          styles.submit,
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
            Sign in
          </Text>
        )}
      </Pressable>
    </ScrollView>
  );
};

const StateScreen: React.FC<{
  title: string;
  description: string;
  actionLabel: string;
  onAction: () => void;
}> = ({ title, description, actionLabel, onAction }) => {
  const { colors } = useTheme();
  return (
    <View style={styles.centered}>
      <Text style={[styles.emptyTitle, { color: colors.onSurface }]}>
        {title}
      </Text>
      <Text
        style={[styles.emptyDescription, { color: colors.onSurfaceVariant }]}
      >
        {description}
      </Text>
      <Pressable
        onPress={onAction}
        accessibilityRole="button"
        accessibilityLabel={actionLabel}
        style={({ pressed }) => [
          styles.submit,
          {
            backgroundColor: pressed ? colors.primaryActive : colors.primary,
            minWidth: 160,
          },
        ]}
      >
        <Text style={{ color: colors.onPrimary, fontWeight: '600' }}>
          {actionLabel}
        </Text>
      </Pressable>
    </View>
  );
};

const SectionCard: React.FC<{
  title: string;
  colors: ReturnType<typeof useTheme>['colors'];
  children: React.ReactNode;
}> = ({ title, colors, children }) => (
  <View
    style={[
      styles.card,
      {
        backgroundColor: colors.surfaceContainer,
        shadowColor: colors.shadow,
      },
    ]}
  >
    <Text style={[styles.sectionTitle, { color: colors.primary }]}>
      {title}
    </Text>
    {children}
  </View>
);

const LastUpdated: React.FC<{
  value: string;
  colors: ReturnType<typeof useTheme>['colors'];
}> = ({ value, colors }) => (
  <Text style={[styles.lastUpdated, { color: colors.onSurfaceDisabled }]}>
    Last updated {formatDateTime(value)}
  </Text>
);

const Unavailable: React.FC<{
  colors: ReturnType<typeof useTheme>['colors'];
  reason: string;
}> = ({ colors, reason }) => (
  <Text style={[styles.body, { color: colors.onSurfaceVariant }]}>{reason}</Text>
);

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
  generatedAt: { flex: 1, flexWrap: 'wrap' },
  headerButton: {
    minHeight: 48,
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
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  farmName: { fontSize: 20, fontWeight: '600' },
  body: { fontSize: 14, lineHeight: 20 },
  listItem: { paddingVertical: spacing[2], borderBottomWidth: 1 },
  itemTitle: { fontSize: 15, fontWeight: '500' },
  weatherValue: { fontSize: 24, fontWeight: '600' },
  alertItem: {
    borderRadius: borderRadius.md,
    padding: spacing[3],
  },
  lastUpdated: { fontSize: 12, marginTop: spacing[1] },
  form: {
    flex: 1,
    justifyContent: 'center',
    padding: spacing[6],
    gap: spacing[3],
  },
  formTitle: { fontSize: 20, fontWeight: '600', textAlign: 'center' },
  formError: { fontSize: 14 },
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
  emptyTitle: { fontSize: 20, fontWeight: '600', textAlign: 'center' },
  emptyDescription: {
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
    marginBottom: spacing[2],
  },
});

export default DashboardScreen;
