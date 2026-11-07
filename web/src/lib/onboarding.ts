// Onboarding step-ordering logic (E5) — kept pure so it can be unit-tested.
// Mirrors the backend's computed step order: contact_verified → verification
// → location → land → profile.

import { OnboardingStatus } from '@/lib/api/types';

export const STEP_LABELS: Record<string, string> = {
  contact_verified: 'Verify your contact',
  verification: 'Identity verification',
  location: 'Set your home location',
  land: 'Register your land',
  profile: 'Complete your farmer profile',
};

/** Index of the step in the fixed onboarding order. */
export function stepIndex(step: string): number {
  const order = Object.keys(STEP_LABELS);
  const i = order.indexOf(step);
  return i === -1 ? order.length : i;
}

/**
 * The step the farmer should work on now: the first incomplete step in the
 * backend's `steps` list (which is already ordered), or null when complete.
 */
export function firstIncomplete(status: OnboardingStatus): string | null {
  return status.next_step;
}

/**
 * Is onboarding blocked before the interactive steps (location/land/profile)?
 * Pending selfie review and unverified contact are waiting states, not forms.
 */
export function isWaitingState(step: string | null): boolean {
  return step === 'contact_verified' || step === 'verification';
}

/** Format an area (m²) in every supported unit for display. */
export function formatArea(conversions: Record<string, number>): string {
  const ha = conversions['hectare'];
  const acre = conversions['acre'];
  const sqm = conversions['sq_m'];
  if (ha === undefined || acre === undefined || sqm === undefined) return '';
  return `${ha.toLocaleString(undefined, { maximumFractionDigits: 4 })} ha · ${acre.toLocaleString(undefined, { maximumFractionDigits: 4 })} acre · ${sqm.toLocaleString(undefined, { maximumFractionDigits: 0 })} m²`;
}
