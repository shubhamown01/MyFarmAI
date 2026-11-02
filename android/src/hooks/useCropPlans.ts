import { useState, useCallback, useEffect } from 'react';
import { apiClient, ApiError } from '../lib/api/client';
import { CropPlan } from '../types/cropPlan';
import {
  setSessionToken,
  setRefreshToken,
  clearSessionTokens,
  getSessionToken,
} from '../lib/auth/session';

// Same status machine as useDashboard: the sign-in/no-farm/offline states are
// shared so the crop-planning screen behaves exactly like the dashboard.
export type CropPlansStatus =
  | 'loading'
  | 'signed-out'
  | 'no-farm'
  | 'offline'
  | 'error'
  | 'ready';

export function useCropPlans() {
  const [status, setStatus] = useState<CropPlansStatus>('loading');
  const [farmId, setFarmId] = useState<string | null>(null);
  const [farmName, setFarmName] = useState<string | null>(null);
  const [plans, setPlans] = useState<CropPlan[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [hasSession, setHasSession] = useState<boolean | null>(null);

  const load = useCallback(async () => {
    setStatus('loading');
    setErrorMessage(null);
    try {
      const farms = await apiClient.getFarms();
      if (farms.length === 0) {
        setStatus('no-farm');
        return;
      }
      const list = await apiClient.getCropPlans(farms[0].id);
      setFarmId(farms[0].id);
      setFarmName(farms[0].name);
      setPlans(list);
      setStatus('ready');
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 401) {
          await clearSessionTokens();
          setStatus('signed-out');
        } else if (error.status === 404 && error.code === 'FARM_NOT_FOUND') {
          setStatus('no-farm');
        } else if (error.code === 'NETWORK_ERROR') {
          setStatus('offline');
        } else {
          setErrorMessage(error.message);
          setStatus('error');
        }
      } else {
        setErrorMessage('Something went wrong. Please try again.');
        setStatus('error');
      }
    }
  }, []);

  const signIn = useCallback(
    async (email: string, password: string): Promise<string | null> => {
      try {
        const result = await apiClient.login(email, password);
        if (!result.access_token) {
          return 'Sign-in failed. Please try again.';
        }
        await setSessionToken(result.access_token);
        if (result.refresh_token) {
          await setRefreshToken(result.refresh_token);
        }
        setHasSession(true);
        await load();
        return null;
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          return 'Invalid email or password.';
        }
        if (error instanceof ApiError && error.code === 'NETWORK_ERROR') {
          return 'You appear to be offline. Check your connection and try again.';
        }
        return 'Sign-in failed. Please try again.';
      }
    },
    [load]
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const token = await getSessionToken();
      if (!cancelled) setHasSession(!!token);
      await load();
    })();
    return () => {
      cancelled = true;
    };
  }, [load]);

  return {
    status,
    farmId,
    farmName,
    plans,
    errorMessage,
    hasSession,
    reload: load,
    signIn,
  };
}
