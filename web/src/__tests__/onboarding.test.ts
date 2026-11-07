import { firstIncomplete, formatArea, isWaitingState } from '@/lib/onboarding';
import { OnboardingStatus } from '@/lib/api/types';

function status(overrides: Partial<OnboardingStatus> = {}): OnboardingStatus {
  return {
    verification_status: 'active',
    steps: [],
    next_step: 'location',
    complete: false,
    ...overrides,
  };
}

describe('onboarding helpers', () => {
  it('picks the backend-provided next step', () => {
    expect(firstIncomplete(status({ next_step: 'land' }))).toBe('land');
  });

  it('returns null when complete', () => {
    expect(firstIncomplete(status({ next_step: null, complete: true }))).toBeNull();
  });

  it('treats contact and verification as waiting states', () => {
    expect(isWaitingState('contact_verified')).toBe(true);
    expect(isWaitingState('verification')).toBe(true);
    expect(isWaitingState('location')).toBe(false);
    expect(isWaitingState('land')).toBe(false);
    expect(isWaitingState('profile')).toBe(false);
    expect(isWaitingState(null)).toBe(false);
  });

  it('formats area in all units', () => {
    const text = formatArea({ sq_m: 10000, hectare: 1, acre: 2.471054, sq_km: 0.01 });
    expect(text).toContain('1 ha');
    expect(text).toContain('acre');
    expect(text).toContain('10,000 m²');
  });

  it('returns empty string when conversions are missing', () => {
    expect(formatArea({})).toBe('');
  });
});
