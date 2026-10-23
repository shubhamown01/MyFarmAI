'use client';

import { useCallback, useEffect, useState } from 'react';

export interface FarmProfile {
  name: string;
  locationLabel: string;
  latitude: number;
  longitude: number;
}

export const DEFAULT_PROFILE: FarmProfile = {
  name: 'Shubham',
  locationLabel: 'Durg, CG',
  latitude: 21.1938,
  longitude: 81.3509,
};

const PROFILE_STORAGE_KEY = 'myfarmai_profile_v1';
const PROFILE_EVENT = 'myfarmai:profile-change';

function isFiniteCoordinate(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function normalizeProfile(value: Partial<FarmProfile> | null | undefined): FarmProfile {
  return {
    name: value?.name?.trim() || DEFAULT_PROFILE.name,
    locationLabel: value?.locationLabel?.trim() || DEFAULT_PROFILE.locationLabel,
    latitude: isFiniteCoordinate(value?.latitude) ? value.latitude : DEFAULT_PROFILE.latitude,
    longitude: isFiniteCoordinate(value?.longitude) ? value.longitude : DEFAULT_PROFILE.longitude,
  };
}

function readStoredProfile(): FarmProfile | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(PROFILE_STORAGE_KEY);
    if (!raw) return null;
    return normalizeProfile(JSON.parse(raw) as Partial<FarmProfile>);
  } catch {
    return null;
  }
}

/**
 * Reads the farmer profile from local storage. The app has no authentication or
 * profile endpoint yet, so local storage is the source of truth and the default
 * profile keeps the dashboard useful on first visit.
 */
export function useProfile() {
  const [profile, setProfile] = useState<FarmProfile>(DEFAULT_PROFILE);

  useEffect(() => {
    const sync = () => setProfile(readStoredProfile() ?? DEFAULT_PROFILE);
    sync();

    window.addEventListener(PROFILE_EVENT, sync);
    window.addEventListener('storage', sync);
    return () => {
      window.removeEventListener(PROFILE_EVENT, sync);
      window.removeEventListener('storage', sync);
    };
  }, []);

  const updateProfile = useCallback((updates: Partial<FarmProfile>) => {
    const next = normalizeProfile({ ...(readStoredProfile() ?? DEFAULT_PROFILE), ...updates });
    window.localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(next));
    setProfile(next);
    window.dispatchEvent(new Event(PROFILE_EVENT));
    return next;
  }, []);

  return { profile, updateProfile };
}
