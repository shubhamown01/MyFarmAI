import { useState, useCallback, useEffect } from 'react';
import { apiClient, ApiError } from '../lib/api/client';
import { DashboardResponse } from '../types/dashboard';
import { setSessionToken, setRefreshToken, clearSessionTokens, getSessionToken } from '../lib/auth/session';

export type DashboardStatus =
  | 'loading' // fetching (initial load)
  | 'signed-out' // no/expired session (401) — sign-in form shown
  | 'no-farm' // signed in but user has no farm (404 FARM_NOT_FOUND / empty list)
  | 'offline' // network unreachable
  | 'error' // other backend error
  | 'ready'; // dashboard data

export function useDashboard() {
  const [status, setStatus] = useState<DashboardStatus>('loading');
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
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
      const data = await apiClient.getDashboard(farms[0].id);
      setDashboard(data);
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

  const signOut = useCallback(async () => {
    await clearSessionTokens();
    setDashboard(null);
    setHasSession(false);
    setStatus('signed-out');
  }, []);

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
    dashboard,
    errorMessage,
    hasSession,
    reload: load,
    signIn,
    signOut,
  };
}
