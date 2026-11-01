import { API_BASE_URL, API_ENDPOINTS } from '../../config/api';
import {
  WeatherResponse,
  ResourcesResponse,
  HealthResponse,
} from '../../types';
import { DashboardResponse, FarmSummary } from '../../types/dashboard';
import { getSessionToken } from '../auth/session';

const REQUEST_TIMEOUT = 120000; // 120s for chat (Ollama can be slow)
const WEATHER_TIMEOUT = 30000; // 30s for weather
const DASHBOARD_TIMEOUT = 30000; // 30s for dashboard (plain DB + optional weather)

class ApiClient {
  private baseHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    timeout = REQUEST_TIMEOUT
  ): Promise<T> {
    const requestId = crypto.randomUUID();
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    const sessionToken = await getSessionToken();

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          ...this.baseHeaders,
          'x-request-id': requestId,
          // Backend accepts the Android session ID as a bearer token
          // (auth.py _presented_session_id: bearer header or web cookie).
          ...(sessionToken
            ? { Authorization: `Bearer ${sessionToken}` }
            : {}),
          ...options.headers,
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new ApiError(
          response.status,
          error.detail || response.statusText,
          error.error_code
        );
      }

      return response.json();
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
  ): Promise<{
    response: string;
    conversation_id: string;
    model: string;
  }> {
    return this.request(
      API_ENDPOINTS.chat,
      {
        method: 'POST',
        body: JSON.stringify({
          message,
          conversation_id: conversationId,
          language: context?.language || 'en',
          crop: context?.crop,
          location: context?.location,
        }),
      },
      REQUEST_TIMEOUT
    );
  }

  // Weather
  async getWeather(
    latitude: number,
    longitude: number,
    currentOnly = false
  ) {
    const params = new URLSearchParams({
      latitude: latitude.toString(),
      longitude: longitude.toString(),
      current: 'true',
      daily: currentOnly ? 'false' : 'true',
    });
    return this.request<WeatherResponse>(
      `${API_ENDPOINTS.weather}?${params}`,
      {},
      WEATHER_TIMEOUT
    );
  }

  async getCurrentWeather(latitude: number, longitude: number) {
    return this.request<WeatherResponse>(
      `${API_ENDPOINTS.weatherCurrent}?latitude=${latitude}&longitude=${longitude}`,
      {},
      WEATHER_TIMEOUT
    );
  }

  // Resources
  async getResources(category?: string) {
    const params = category ? `?category=${category}` : '';
    return this.request<ResourcesResponse>(
      `${API_ENDPOINTS.resources}${params}`,
      {},
      WEATHER_TIMEOUT
    );
  }

  async getCategories() {
    return this.request<string[]>(
      `${API_ENDPOINTS.resourceCategories}`,
      {},
      WEATHER_TIMEOUT
    );
  }

  async getResourcesByCategory(category: string) {
    return this.request<ResourcesResponse>(
      `${API_ENDPOINTS.resources}/${category}`,
      {},
      WEATHER_TIMEOUT
    );
  }

  // Health
  async checkHealth() {
    return this.request<HealthResponse>(
      API_ENDPOINTS.health,
      {},
      WEATHER_TIMEOUT
    );
  }

  // Farms (auth-gated)
  async getFarms() {
    return this.request<FarmSummary[]>(
      API_ENDPOINTS.farms,
      {},
      DASHBOARD_TIMEOUT
    );
  }

  // Dashboard (auth-gated)
  async getDashboard(farmId: string) {
    return this.request<DashboardResponse>(
      `${API_ENDPOINTS.dashboard}?farm_id=${encodeURIComponent(farmId)}`,
      {},
      DASHBOARD_TIMEOUT
    );
  }

  // Android login: backend returns the session ID in the body when
  // android: true (web instead gets an HttpOnly cookie).
  async login(email: string, password: string) {
    return this.request<{ access_token: string | null; refresh_token: string | null }>(
      API_ENDPOINTS.login,
      {
        method: 'POST',
        body: JSON.stringify({ email, password, android: true }),
      },
      DASHBOARD_TIMEOUT
    );
  }
}

export const apiClient = new ApiClient();

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}