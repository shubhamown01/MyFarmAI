import {
  API_ENDPOINTS,
  getApiBaseUrl,
  API_BASE_URL,
} from '../api';

// NOTE: EXPO_PUBLIC_* variables are compiled into the module bundle by
// Expo's babel env-inline transform, so tests here run against the dev
// fallback path. BASE_URL switch (staging/production) is a build-time
// env change verified via scripts/check-api-url.mjs and at runtime on a
// device, not via process.env mutation in Jest.
describe('api base URL resolution (contract TEST-001 regression)', () => {
  it('dev fallback resolves to the Android-emulator host', () => {
    expect(getApiBaseUrl()).toBe('http://10.0.2.2:8000');
  });

  it('concatenated chat endpoint contains exactly one /api/v1 prefix', () => {
    const url = `${API_BASE_URL}${API_ENDPOINTS.chat}`;
    expect(url).toBe('http://10.0.2.2:8000/api/v1/chat');
    expect(url.match(/api\/v1/g)?.length).toBe(1);
  });

  it('declared endpoints carry their /api/v1 prefix exactly once', () => {
    for (const value of Object.values(API_ENDPOINTS)) {
      expect(value.startsWith('/api/v1/') || value === '/health').toBe(true);
      expect(value.match(/api\/v1/g)?.length ?? (value === '/health' ? 0 : 2)).toBe(
        value === '/health' ? 0 : 1,
      );
    }
    expect(API_BASE_URL).toBe(getApiBaseUrl());
  });
});
