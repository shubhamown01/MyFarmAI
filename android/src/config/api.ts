export const API_ENDPOINTS = {
  chat: '/api/v1/chat',
  weather: '/api/v1/weather',
  weatherCurrent: '/api/v1/weather/current',
  resources: '/api/v1/resources',
  resourceCategories: '/api/v1/resources/categories',
  farms: '/api/v1/farms',
  dashboard: '/api/v1/dashboard',
  login: '/api/v1/auth/login',
  health: '/health',
  // Phase 7B crop plans — {farm_id}/{plan_id}/{task_id} are filled by the client
  cropPlans: '/api/v1/farms/{farm_id}/crop-plans',
  cropPlan: '/api/v1/crop-plans/{plan_id}',
  cropPlanRevisions: '/api/v1/crop-plans/{plan_id}/revisions',
  cropPlanTasks: '/api/v1/crop-plans/{plan_id}/tasks',
  cropPlanTask: '/api/v1/crop-plans/{plan_id}/tasks/{task_id}',
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