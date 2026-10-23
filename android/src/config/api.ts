export const API_ENDPOINTS = {
  chat: '/api/v1/chat',
  weather: '/api/v1/weather',
  weatherCurrent: '/api/v1/weather/current',
  resources: '/api/v1/resources',
  resourceCategories: '/api/v1/resources/categories',
  health: '/health',
} as const;

// Base URL must NOT carry the /api/v1 prefix: API_ENDPOINTS already include it,
// so concatenation would double it.
const rawBaseUrl =
  process.env.EXPO_PUBLIC_API_BASE_URL ??
  (__DEV__
    ? // Android emulator uses 10.0.2.2 to reach host machine
      'http://10.0.2.2:8000/api/v1'
    : 'https://api.myfarmai.example.com/api/v1');

export const getApiBaseUrl = (): string =>
  rawBaseUrl.replace(/\/?api\/v1\/?$/, '').replace(/\/$/, '');

export const API_BASE_URL = getApiBaseUrl();