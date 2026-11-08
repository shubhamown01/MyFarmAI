import {
  ChatResponse,
  WeatherResponse,
  ResourcesResponse,
  HealthResponse,
  DashboardResponse,
  FarmSummary,
  CropCycleSummary,
  CropPlan,
  CropPlanCreatePayload,
  CropPlanRevision,
  CropPlanTask,
  CropPlanTaskUpdatePayload,
  LoginResponse,
  OnboardingStatus,
  FarmerProfile,
  FarmerProfilePayload,
  Plot,
  PolygonPoint,
  HomeLocationSave,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '/api/v1';
const REQUEST_TIMEOUT = 120000; // 120s for chat

export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

class ApiClient {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const requestId =
      typeof crypto !== 'undefined' && 'randomUUID' in crypto
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          ...this.defaultHeaders,
          'x-request-id': requestId,
          ...options.headers,
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        const detail = payload?.detail;
        const nestedDetail =
          detail && typeof detail === 'object' ? detail.detail : undefined;
        const message =
          (typeof detail === 'string' ? detail : nestedDetail) ||
          payload?.message ||
          response.statusText ||
          'The request could not be completed.';
        const code =
          (detail && typeof detail === 'object' ? detail.error_code : undefined) ||
          payload?.error_code;
        throw new ApiError(response.status, message, code);
      }

      if (response.status === 204) {
        return undefined as T; // 204 No Content: no body to parse (logout)
      }
      return response.json() as Promise<T>;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof ApiError) throw error;
      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new ApiError(408, 'Request timeout', 'TIMEOUT');
      }
      throw new ApiError(0, 'Network error', 'NETWORK_ERROR');
    }
  }

  // Chat
  async sendMessage(
    message: string,
    conversationId?: string,
    context?: { language?: string; crop?: string; location?: string }
  ) {
    return this.request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        language: context?.language || 'en',
        crop: context?.crop,
        location: context?.location,
      }),
    });
  }

  // Weather
  async getWeather(lat: number, lon: number, currentOnly = false) {
    const params = new URLSearchParams({
      latitude: lat.toString(),
      longitude: lon.toString(),
      current: 'true',
      daily: currentOnly ? 'false' : 'true',
    });
    return this.request<WeatherResponse>(`/weather?${params}`);
  }

  async getCurrentWeather(lat: number, lon: number) {
    return this.request<WeatherResponse>(
      `/weather/current?latitude=${lat}&longitude=${lon}`
    );
  }

  // Resources
  async getResources(category?: string) {
    const params = category ? `?category=${category}` : '';
    return this.request<ResourcesResponse>(`/resources${params}`);
  }

  async getCategories() {
    return this.request<string[]>('/resources/categories');
  }

  async getResourcesByCategory(category: string) {
    return this.request<ResourcesResponse>(`/resources/${category}`);
  }

  // Farms & Dashboard
  async getFarms() {
    return this.request<FarmSummary[]>('/farms');
  }

  async getDashboard(farmId: string) {
    const params = new URLSearchParams({ farm_id: farmId });
    return this.request<DashboardResponse>(`/dashboard?${params}`);
  }

  // Crop cycles (Phase 5A — listed for plan creation)
  async getCropCycles(farmId: string) {
    return this.request<CropCycleSummary[]>(`/farms/${farmId}/crop-cycles`);
  }

  // Crop plans (Phase 7B)
  async getCropPlans(farmId: string) {
    return this.request<CropPlan[]>(`/farms/${farmId}/crop-plans`);
  }

  async createCropPlan(farmId: string, payload: CropPlanCreatePayload) {
    return this.request<CropPlan>(`/farms/${farmId}/crop-plans`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getCropPlan(planId: string) {
    return this.request<CropPlan>(`/crop-plans/${planId}`);
  }

  async getCropPlanRevisions(planId: string) {
    return this.request<CropPlanRevision[]>(`/crop-plans/${planId}/revisions`);
  }

  async addCropPlanTask(
    planId: string,
    payload: { title: string; due_date?: string | null }
  ) {
    return this.request<CropPlanTask>(`/crop-plans/${planId}/tasks`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateCropPlanTask(
    planId: string,
    taskId: string,
    payload: CropPlanTaskUpdatePayload
  ) {
    return this.request<CropPlanTask>(
      `/crop-plans/${planId}/tasks/${taskId}`,
      {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }
    );
  }

  // Health
  async checkHealth() {
    return this.request<HealthResponse>('/health');
  }

  // ── Auth (Phase 3 / E1-E2) ── cookie-based sessions via same-origin proxy

  async login(email: string, password: string) {
    return this.request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async logout() {
    return this.request<void>('/auth/logout', { method: 'POST' });
  }

  async getMe() {
    return this.request<LoginResponse['user']>('/auth/me');
  }

  async requestEmailOtp(email: string) {
    return this.request<{ message: string; delivery_mode?: string }>(
      '/auth/register/email/request-otp',
      {
        method: 'POST',
        body: JSON.stringify({ email }),
      }
    );
  }

  async verifyEmailOtp(email: string, code: string) {
    return this.request<LoginResponse>('/auth/register/email/verify', {
      method: 'POST',
      body: JSON.stringify({ email, code }),
    });
  }

  async getOAuthAuthorizeUrl(provider: string, redirectUri: string) {
    return this.request<{ authorize_url: string; state: string }>(
      `/auth/oauth/${provider}/authorize?redirect_uri=${encodeURIComponent(redirectUri)}`
    );
  }

  /** Finishes OAuth: backend validates code+state and sets the session cookie. */
  async oauthCallback(provider: string, code: string, state: string, redirectUri: string) {
    const params = new URLSearchParams({ code, state, redirect_uri: redirectUri });
    return this.request<LoginResponse>(`/auth/oauth/${provider}/callback?${params}`);
  }

  // ── Onboarding (E5) ──

  async getOnboardingStatus() {
    return this.request<OnboardingStatus>('/me/onboarding');
  }

  async getFarmerProfile() {
    return this.request<FarmerProfile>('/me/farmer-profile');
  }

  async saveFarmerProfile(payload: FarmerProfilePayload) {
    return this.request<FarmerProfile>('/me/farmer-profile', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  // ── Land registration (E4) ──

  async createFarm(name: string) {
    return this.request<FarmSummary>('/farms', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  }

  async createPlot(farmId: string, name: string, landType: string) {
    return this.request<Plot>(`/farms/${farmId}/plots`, {
      method: 'POST',
      body: JSON.stringify({ name, land_type: landType }),
    });
  }

  async listPlots(farmId: string) {
    return this.request<Plot[]>(`/farms/${farmId}/plots`);
  }

  async saveBoundary(farmId: string, plotId: string, polygon: PolygonPoint[], source: 'map_drawn' | 'manual_entry') {
    return this.request<Plot>(`/farms/${farmId}/plots/${plotId}/boundary`, {
      method: 'PUT',
      body: JSON.stringify({ polygon, source }),
    });
  }

  async saveHomeLocation(payload: HomeLocationSave) {
    return this.request<unknown>('/me/home-location', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  async saveManualArea(farmId: string, plotId: string, value: number, unit: string) {
    return this.request<unknown>(`/farms/${farmId}/plots/${plotId}/area`, {
      method: 'POST',
      body: JSON.stringify({ area_value: value, area_unit: unit, confirm: true }),
    });
  }
}

export const apiClient = new ApiClient();
export type {
  ChatResponse,
  WeatherResponse,
  ResourcesResponse,
  HealthResponse,
  DashboardResponse,
  FarmSummary,
  CropCycleSummary,
  CropPlan,
  CropPlanCreatePayload,
  CropPlanRevision,
  CropPlanTask,
  CropPlanTaskUpdatePayload,
  LoginResponse,
  OnboardingStatus,
  FarmerProfile,
  Plot,
  PolygonPoint,
} from './types';