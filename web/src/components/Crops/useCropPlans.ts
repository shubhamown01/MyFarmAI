'use client';

import { useQuery } from '@tanstack/react-query';
import { ApiError, apiClient } from '@/lib/api/client';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';
import type { CropPlan } from '@/lib/api/types';

export type CropPlansState =
  | { phase: 'loading' }
  | { phase: 'no-farm' }
  | { phase: 'offline' }
  | { phase: 'error'; message: string; retry: () => void }
  | {
      phase: 'ready';
      farmId: string;
      plans: CropPlan[];
      offline: boolean;
      refetch: () => void;
    };

const STALE_TIME = 1000 * 60 * 5; // 5 minutes, matching the app-wide query default

/**
 * Loads the crop plans for the user's first farm (same farm resolution as
 * the dashboard). A 404 from either farms or plans renders the no-farm
 * empty state — never an error (non-members get 404 by design).
 */
export function useCropPlans(): CropPlansState {
  const { isOnline } = useOnlineStatus();

  const farmsQuery = useQuery({
    queryKey: ['farms'],
    queryFn: () => apiClient.getFarms(),
    staleTime: STALE_TIME,
    retry: 1,
  });

  const farmId = farmsQuery.data?.[0]?.id;
  const plansQuery = useQuery({
    queryKey: ['crop-plans', farmId],
    queryFn: () => apiClient.getCropPlans(farmId!),
    enabled: farmId !== undefined,
    staleTime: STALE_TIME,
    retry: 1,
  });

  // Offline before anything else — even cached data is annotated as stale.
  if (!isOnline) {
    return plansQuery.data
      ? {
          phase: 'ready',
          farmId: farmId!,
          plans: plansQuery.data,
          offline: true,
          refetch: () => plansQuery.refetch(),
        }
      : { phase: 'offline' };
  }

  if (farmsQuery.isLoading || (farmId !== undefined && plansQuery.isLoading)) {
    return { phase: 'loading' };
  }

  // No farm yet, or the farm is gone/unshared — same friendly empty state
  // as the dashboard (404 FARM_NOT_FOUND deliberately does not leak existence).
  if (!farmId || (plansQuery.error instanceof ApiError && plansQuery.error.status === 404)) {
    return { phase: 'no-farm' };
  }

  if (plansQuery.error || farmsQuery.error) {
    const error = plansQuery.error ?? farmsQuery.error;
    return {
      phase: 'error',
      message:
        error instanceof Error && error.message
          ? error.message
          : 'Your crop plans could not be loaded.',
      retry: () => {
        farmsQuery.refetch();
        plansQuery.refetch();
      },
    };
  }

  if (!plansQuery.data) {
    return { phase: 'loading' };
  }

  return {
    phase: 'ready',
    farmId,
    plans: plansQuery.data,
    offline: false,
    refetch: () => plansQuery.refetch(),
  };
}
