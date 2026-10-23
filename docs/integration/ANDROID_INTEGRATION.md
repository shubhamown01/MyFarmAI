# MyFarm AI — Android Integration Guide (React Native / Expo)

## Overview

This guide covers integrating the MyFarm AI backend with a React Native / Expo Android application.

## Prerequisites

- React Native / Expo SDK 51+
- Node.js 18+
- Android Studio (for native builds)
- EAS CLI (`npm install -g eas-cli`)

## Base URL Configuration

### Development (Local)

```typescript
// config/api.ts
const API_BASE_URL = __DEV__
  ? 'http://10.0.2.2:8000/api/v1'  // Android emulator → host localhost
  : 'https://api.myfarmai.example.com/api/v1';  // Production

export const API_ENDPOINTS = {
  chat: `${API_BASE_URL}/chat`,
  weather: `${API_BASE_URL}/weather`,
  weatherCurrent: `${API_BASE_URL}/weather/current`,
  resources: `${API_BASE_URL}/resources`,
  resourceCategories: `${API_BASE_URL}/resources/categories`,
  health: `${API_BASE_URL}/health`,
};
```

| Environment | Base URL | Notes |
|-------------|----------|-------|
| Android Emulator | `http://10.0.2.2:8000/api/v1` | Special IP for emulator → host |
| Physical Device (USB) | `http://<host-ip>:8000/api/v1` | Host machine's LAN IP |
| Physical Device (WiFi) | `http://<host-ip>:8000/api/v1` | Same network |
| Production | `https://api.myfarmai.example.com/api/v1` | HTTPS required |

> **Note**: `10.0.2.2` is Android emulator's alias for host machine's `localhost`. For physical devices, use host machine's LAN IP (e.g., `192.168.1.100`).

## API Client Setup

### HTTP Client with Request ID

```typescript
// lib/api/client.ts
import { API_ENDPOINTS } from '../config/api';

const REQUEST_TIMEOUT = 120000; // 120s for chat (Ollama can be slow)

class ApiClient {
  private baseHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const requestId = crypto.randomUUID();
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
      const response = await fetch(endpoint, {
        ...options,
        headers: {
          ...this.baseHeaders,
          'x-request-id': crypto.randomUUID(),
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
  async sendMessage(message: string, conversationId?: string, context?: ChatContext) {
    return this.request<ChatResponse>(API_ENDPOINTS.chat, {
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
    return this.request<WeatherResponse>(
      `${API_ENDPOINTS.weather}?${params}`
    );
  }

  async getCurrentWeather(lat: number, lon: number) {
    return this.request<WeatherResponse>(
      `${API_ENDPOINTS.weatherCurrent}?latitude=${lat}&longitude=${lon}`
    );
  }

  // Resources
  async getResources(category?: string) {
    const params = category ? `?category=${category}` : '';
    return this.request<ResourcesResponse>(
      `${API_ENDPOINTS.resources}${params}`
    );
  }

  async getCategories() {
    return this.request<string[]>(API_ENDPOINTS.resourceCategories);
  }

  async getResourcesByCategory(category: string) {
    return this.request<ResourcesResponse>(
      `${API_ENDPOINTS.resources}/${category}`
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
```

## Chat Integration

### Types

```typescript
// types/chat.ts
export interface ChatContext {
  language?: 'en' | 'hi';
  crop?: string;
  location?: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  language?: string;
  crop?: string;
  location?: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  model: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  conversationId: string;
}
```

### Chat Hook

```typescript
// hooks/useChat.ts
import { useState, useCallback } from 'react';
import { apiClient, ApiError } from '../lib/api/client';
import { ChatContext, ChatMessage, ChatResponse } from '../types/chat';

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (text: string, context?: ChatContext) => {
      if (!text.trim()) return;

      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: text,
        timestamp: new Date(),
        conversationId: conversationId || '',
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      try {
        const response: ChatResponse = await apiClient.sendMessage(
          text,
          conversationId || undefined,
          context
        );

        const assistantMessage: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: response.response,
          timestamp: new Date(),
          conversationId: response.conversation_id,
        };

        setMessages((prev) => [...prev, assistantMessage]);
        setConversationId(response.conversation_id);
      } catch (error) {
        if (error instanceof ApiError) {
          setError(`${error.code}: ${error.message}`);
        } else {
          setError('Failed to send message');
        }
        // Remove user message on error
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setIsLoading(false);
      }
    },
    [conversationId]
  );

  const clearConversation = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setError(null);
  }, []);

  return {
    messages,
    conversationId,
    isLoading,
    error,
    sendMessage,
    clearConversation,
  };
}
```

## Weather Integration

### Types

```typescript
// types/weather.ts
export interface CurrentWeather {
  temperature: number;
  windspeed: number;
  winddirection: number;
  weathercode: number;
  weather_description: string;
  time: string;
}

export interface DailyForecast {
  date: string;
  temperature_2m_max: number;
  temperature_2m_min: number;
  precipitation_sum: number;
  precipitation_probability_max: number;
  weathercode: number;
  weather_description: string;
}

export interface WeatherResponse {
  latitude: number;
  longitude: number;
  timezone: string;
  current_weather?: CurrentWeather;
  daily?: DailyForecast[];
}
```

### Weather Hook

```typescript
// hooks/useWeather.ts
import { useState, useCallback } from 'react';
import { apiClient } from '../lib/api/client';
import { WeatherResponse } from '../types/weather';

export function useWeather() {
  const [weather, setWeather] = useState<WeatherResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchWeather = useCallback(
    async (latitude: number, longitude: number, currentOnly = false) => {
      setIsLoading(true);
      setError(null);

      try {
        const data = currentOnly
          ? await apiClient.getCurrentWeather(latitude, longitude)
          : await apiClient.getWeather(latitude, longitude);
        setWeather(data);
      } catch (error) {
        setError('Failed to fetch weather');
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  return { weather, isLoading, error, fetchWeather };
}
```

### Weather Code Mapping

```typescript
// utils/weatherCodes.ts
export const WEATHER_CODES: Record<number, string> = {
  0: 'Clear sky',
  1: 'Mainly clear',
  2: 'Partly cloudy',
  3: 'Overcast',
  45: 'Fog',
  48: 'Depositing rime fog',
  51: 'Light drizzle',
  53: 'Moderate drizzle',
  55: 'Dense drizzle',
  61: 'Slight rain',
  63: 'Moderate rain',
  65: 'Heavy rain',
  71: 'Slight snow',
  73: 'Moderate snow',
  75: 'Heavy snow',
  80: 'Slight rain showers',
  81: 'Moderate rain showers',
  82: 'Violent rain showers',
  95: 'Thunderstorm',
  96: 'Thunderstorm with slight hail',
  99: 'Thunderstorm with heavy hail',
};

export function getWeatherDescription(code: number): string {
  return WEATHER_CODES[code] || 'Unknown';
}
```

## Agricultural Resources Integration

### Types

```typescript
// types/resources.ts
export interface AgriculturalResource {
  title: string;
  category: string;
  url: string;
  source: string;
  description: string;
}

export interface ResourcesResponse {
  resources: AgriculturalResource[];
  total: number;
  categories: string[];
}
```

### Resources Hook

```typescript
// hooks/useResources.ts
import { useState, useCallback, useEffect } from 'react';
import { apiClient } from '../lib/api/client';
import { AgriculturalResource, ResourcesResponse } from '../types/resources';

export function useResources() {
  const [resources, setResources] = useState<AgriculturalResource[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchResources = useCallback(async (category?: string) => {
    setIsLoading(true);
    try {
      const response = category
        ? await apiClient.getResources(category)
        : await apiClient.getResources();
      setResources(response.resources);
      setCategories(response.categories);
    } catch (error) {
      setError('Failed to load resources');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchCategories = useCallback(async () => {
    try {
      const cats = await apiClient.getCategories();
      setCategories(cats);
    } catch (error) {
      // ignore
    }
  }, []);

  useEffect(() => {
    fetchResources();
    fetchCategories();
  }, []);

  return {
    resources,
    categories,
    selectedCategory,
    setSelectedCategory: (cat: string | null) => {
      setSelectedCategory(cat);
      fetchResources(cat || undefined);
    },
    isLoading,
    error,
  };
}
```

## Speech Integration (STT/TTS)

### Speech-to-Text (Using Expo Speech Recognition)

```typescript
// lib/speech/stt.ts
import * as Speech from 'expo-speech-recognition';

export async function startListening(
  language: string = 'hi-IN',
  onResult: (text: string) => void,
  onError: (error: string) => void
) {
  try {
    const available = await Speech.isAvailableAsync();
    if (!available) {
      throw new Error('Speech recognition not available');
    }

    await Speech.startListening({
      language,
      onResult: (result) => {
        if (result.isFinal) {
          onResult(result.text);
        }
      },
      onError: (error) => onError(error.message),
      partialResults: true,
    });
  } catch (error) {
    console.error('STT error:', error);
  }
}

export async function stopListening() {
  await Speech.stopListening();
}
```

### Text-to-Speech (Using Expo Speech)

```typescript
// lib/speech/tts.ts
import * as Speech from 'expo-speech';

export async function speak(
  text: string,
  language: string = 'hi-IN',
  onDone?: () => void
) {
  return new Promise<void>((resolve) => {
    Speech.speak(text, {
      language,
      pitch: 1.0,
      rate: 0.9,
      onDone: () => {
        onDone?.();
        resolve();
      },
      onError: (error) => {
        console.error('TTS error:', error);
        resolve();
      },
    });
  });
}

export async function stopSpeaking() {
  await Speech.stop();
}
```

## Offline Support

### Conversation Caching

```typescript
// lib/storage/conversations.ts
import * as SecureStore from 'expo-secure-store';

const STORAGE_KEY = 'myfarmai_conversations';

export interface StoredConversation {
  id: string;
  messages: ChatMessage[];
  updatedAt: number;
}

export async function saveConversation(conversation: StoredConversation) {
  const existing = await getConversations();
  const updated = existing.filter((c) => c.id !== conversation.id);
  updated.unshift(conversation);
  await SecureStore.setItemAsync(
    STORAGE_KEY,
    JSON.stringify(updated.slice(0, 50)) // Keep last 50
  );
}

export async function getConversations(): Promise<StoredConversation[]> {
  const data = await SecureStore.getItemAsync(STORAGE_KEY);
  return data ? JSON.parse(data) : [];
}

export async function deleteConversation(id: string) {
  const existing = await getConversations();
  const updated = existing.filter((c) => c.id !== id);
  await SecureStore.setItemAsync(STORAGE_KEY, JSON.stringify(updated));
}
```

## EAS Build Configuration

### eas.json

```json
{
  "cli": {
    "version": ">= 5.0.0"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "android": {
        "gradleCommand": ":app:assembleDebug"
      }
    },
    "preview": {
      "distribution": "internal",
      "android": {
        "buildType": "apk"
      }
    },
    "production": {
      "android": {
        "buildType": "aab"
      }
    }
  },
  "submit": {
    "production": {}
  }
}
```

### Build Commands

```bash
# Development build (for testing on device)
eas build --profile development --platform android

# Preview APK (for internal testing)
eas build --profile preview --platform android

# Production AAB (for Play Store)
eas build --profile production --platform android
```

## APK Distribution

### Direct Download (GitHub Releases)

```yaml
# .github/workflows/android-release.yml
name: Android Release
on:
  release:
    types: [published]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - name: Install dependencies
        run: npm ci
      - name: Build APK
        run: eas build --platform android --profile preview --non-interactive
      - name: Upload APK
        uses: actions/upload-release-asset@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          upload_url: ${{ github.event.release.upload_url }}
          asset_path: ./myfarmai.apk
          asset_name: myfarmai-${{ github.event.release.tag_name }}.apk
```

### Installation Instructions for Users

```markdown
# Installation

1. Download the latest APK from [Releases](https://github.com/yourorg/myfarmai/releases)
2. Enable "Install from unknown sources" in Android settings
3. Open the downloaded APK and tap "Install"
4. Open the app and grant microphone permission for voice features
```

## Permissions

### AndroidManifest.xml

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
```

### Runtime Permissions (Expo)

```typescript
// hooks/usePermissions.ts
import * as Permissions from 'expo-permissions';
import * as Location from 'expo-location';

export async function requestPermissions() {
  const microphone = await Permissions.askAsync(Permissions.MEDIA_LIBRARY);
  const location = await Location.requestForegroundPermissionsAsync();
  
  return {
    microphone: microphone.status === 'granted',
    location: location.status === 'granted',
  };
}
```

## Error Handling

### User-Friendly Error Messages

```typescript
// lib/api/errors.ts
export function getUserFriendlyError(error: ApiError): string {
  switch (error.code) {
    case 'RATE_LIMIT_EXCEEDED':
      return 'Too many requests. Please wait a moment and try again.';
    case 'OLLAMA_TIMEOUT':
      return 'The AI is taking too long to respond. Try a shorter question.';
    case 'OLLAMA_CONNECTION_FAILED':
      return 'Cannot connect to AI service. Check your connection.';
    case 'WEATHER_TIMEOUT':
      return 'Weather service is slow. Try again in a moment.';
    case 'CONVERSATION_NOT_FOUND':
      return 'Conversation expired. Starting a new one.';
    case 'NETWORK_ERROR':
      return 'Network error. Check your internet connection.';
    default:
      return error.message || 'An unexpected error occurred';
  }
}
```

## Testing Checklist

- [ ] Chat sends/receives messages correctly
- [ ] Conversation continuity works (conversation_id persists)
- [ ] Weather fetches current + forecast
- [ ] Resources list loads and filters by category
- [ ] Speech-to-text works in Hindi/English
- [ ] Text-to-speech plays Hindi/English
- [ ] Offline conversation caching works
- [ ] Rate limiting triggers correctly (429)
- [ ] Request ID appears in response headers
- [ ] CORS works from emulator/device
- [ ] APK installs and runs on Android 8+
- [ ] Permissions requested correctly
- [ ] Error messages are user-friendly

## Debugging

### Enable Debug Logging

```typescript
// lib/api/client.ts
const DEBUG = __DEV__;

if (DEBUG) {
  console.log('[API]', options.method || 'GET', endpoint, options.body);
}
```

### Common Issues

| Issue | Solution |
|-------|----------|
| CORS error on emulator | Use `10.0.2.2` not `localhost` |
| Network timeout | Increase `REQUEST_TIMEOUT` |
| Speech not working | Check microphone permission |
| Location not working | Check location permission + GPS enabled |
| CORS error on device | Check host IP, firewall, CORS config |
| Rate limited | Wait or increase `RATE_LIMIT_REQUESTS` |

## Production Checklist

- [ ] HTTPS endpoint configured
- [ ] CORS origins restricted to app domains
- [ ] Rate limits appropriate for production
- [ ] Error messages don't leak internals
- [ ] Logging doesn't expose sensitive data
- [ ] APK signed with release keystore
- [ ] Play Store listing prepared
- [ ] Privacy policy published
- [ ] Crash reporting configured (Sentry, etc.)