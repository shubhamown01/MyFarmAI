import { ChatResponse, WeatherResponse, ResourcesResponse, HealthResponse } from './types';

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

  // Health
  async checkHealth() {
    return this.request<HealthResponse>('/health');
  }
}

export const apiClient = new ApiClient();
export type { ChatResponse, WeatherResponse, ResourcesResponse, HealthResponse };