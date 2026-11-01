'use client';

import { useQuery } from '@tanstack/react-query';
import { ApiError, apiClient } from '@/lib/api/client';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';
import type { DashboardResponse } from '@/lib/api/types';

export type DashboardState =
  | { phase: 'loading' }
  | { phase: 'no-farm' }
  | { phase: 'offline' }
  | { phase: 'error'; message: string; retry: () => void }
  | { phase: 'ready'; data: DashboardResponse; offline: boolean; retry: () => void };

const STALE_TIME = 1000 * 60 * 5; // 5 minutes, matching the app-wide query default

/**
 * Loads the farm-intelligence dashboard for the user's first farm.
 * Blocks degrade independently on the backend, so any successful response
 * is rendered; only whole-request failures produce error/no-farm states.
 */
export function useDashboard(): DashboardState {
  const { isOnline } = useOnlineStatus();

  const farmsQuery = useQuery({
    queryKey: ['farms'],
    queryFn: () => apiClient.getFarms(),
    staleTime: STALE_TIME,
    retry: 1,
  });

  const farmId = farmsQuery.data?.[0]?.id;
  const dashboardQuery = useQuery({
    queryKey: ['dashboard', farmId],
    queryFn: () => apiClient.getDashboard(farmId!),
    enabled: farmId !== undefined,
    staleTime: STALE_TIME,
    retry: 1,
  });

  // Offline before anything else — even cached data is annotated as stale.
  if (!isOnline) {
    return dashboardQuery.data
      ? { phase: 'ready', data: dashboardQuery.data, offline: true, retry: () => dashboardQuery.refetch() }
      : { phase: 'offline' };
  }

  if (farmsQuery.isLoading || (farmId !== undefined && dashboardQuery.isLoading)) {
    return { phase: 'loading' };
  }

  // No farm yet, or the farm is gone/unshared — same friendly empty state,
  // never an error (404 FARM_NOT_FOUND deliberately does not leak existence).
  if (!farmId || dashboardQuery.error instanceof ApiError && dashboardQuery.error.status === 404) {
    return { phase: 'no-farm' };
  }

  if (dashboardQuery.error || farmsQuery.error) {
    const error = dashboardQuery.error ?? farmsQuery.error;
    return {
      phase: 'error',
      message:
        error instanceof Error && error.message
          ? error.message
          : 'Your farm overview could not be loaded.',
      retry: () => {
        farmsQuery.refetch();
        dashboardQuery.refetch();
      },
    };
  }

  if (!dashboardQuery.data) {
    return { phase: 'loading' };
  }

  return {
    phase: 'ready',
    data: dashboardQuery.data,
    offline: false,
    retry: () => dashboardQuery.refetch(),
  };
}
