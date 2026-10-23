# MyFarm AI — Web Integration Guide (Next.js / TypeScript)

## Overview

This guide covers integrating the MyFarm AI backend with a Next.js 15+ web application using TypeScript and Tailwind CSS.

## Prerequisites

- Next.js 15+ (App Router)
- TypeScript 5+
- Tailwind CSS 4+
- Node.js 18+

## Project Setup

```bash
npx create-next-app@latest myfarmai-web --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
cd myfarmai-web
npm install @tanstack/react-query zustand lucide-react clsx tailwind-merge
```

## Environment Configuration

### `.env.local`

```env
# Development
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1

# Production
# NEXT_PUBLIC_API_BASE_URL=https://api.myfarmai.example.com/api/v1
```

### `next.config.js`

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_BASE_URL}/:path*`,
      },
    ],
  },
};

module.exports = nextConfig;
```

## API Client

### Types

```typescript
// lib/api/types.ts
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
  generationtime_ms: number;
  utc_offset_seconds: number;
  timezone: string;
  timezone_abbreviation: string;
  elevation: number;
  current_weather?: CurrentWeather;
  daily?: DailyForecast[];
}

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

export interface ErrorResponse {
  detail: string;
  error_code?: string;
}

export interface HealthResponse {
  status: string;
  service: string;
}
```

### API Client

```typescript
// lib/api/client.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '/api/v1';
const REQUEST_TIMEOUT = 120000; // 120s for chat

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
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
    const requestId = crypto.randomUUID();
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
        const error = await response.json().catch(() => ({}));
        throw new ApiError(
          response.status,
          error.detail || response.statusText,
          error.error_code
        );
      }

      return response.json();
    } catch (error) {
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
    return this.request<ResourcesResponse>(`/resources${category ? `?category=${category}` : ''}`);
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

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const requestId = crypto.randomUUID();
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          ...this.defaultHeaders,
          'x-request-id': crypto.randomUUID(),
          ...options.headers,
        },
        signal: controller.signal,
      });

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
      if (error instanceof ApiError) throw error;
      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new ApiError(408, 'Request timeout', 'TIMEOUT');
      }
      throw new ApiError(0, 'Network error', 'NETWORK_ERROR');
    }
  }
}

export const apiClient = new ApiClient();
export { ApiError };
export type { ChatResponse, WeatherResponse, ResourcesResponse, HealthResponse };
```

## React Query Integration

### Query Provider

```typescript
// providers/QueryProvider.tsx
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode, useState } from 'react';

export function QueryProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 1000 * 60 * 5, // 5 minutes
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```

### Layout Wrapper

```typescript
// app/providers.tsx
'use client';

import { QueryProvider } from '@/providers/QueryProvider';
import { ReactNode } from 'react';

export function Providers({ children }: { children: ReactNode }) {
  return <QueryProvider>{children}</QueryProvider>;
}
```

```typescript
// app/layout.tsx
import { Providers } from './providers';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

## Chat Integration

### Chat Hook

```typescript
// hooks/useChat.ts
'use client';

import { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, ApiError } from '@/lib/api/client';
import { ChatResponse, ChatMessage } from '@/lib/api/types';

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const queryClient = useQueryClient();

  const sendMessageMutation = useMutation({
    mutationFn: ({
      message,
      conversationId,
      context,
    }: {
      message: string;
      conversationId?: string;
      context?: { language?: string; crop?: string; location?: string };
    }) => apiClient.sendMessage(message, conversationId, context),
    onMutate: async ({ message }) => {
      // Optimistic update
      const tempId = crypto.randomUUID();
      const optimisticMessage: ChatMessage = {
        id: tempId,
        role: 'user',
        content: message,
        timestamp: new Date(),
        conversationId: conversationId || '',
      };
      setMessages((prev) => [...prev, optimisticMessage]);
      setIsLoading(true);
    },
    onSuccess: (response, variables) => {
      // Replace optimistic message with real response
      setMessages((prev) =>
        prev.map((m) =>
          m.id.startsWith('temp-') && m.role === 'user'
            ? { ...m, id: crypto.randomUUID() }
            : m
        );
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
    },
    onError: (error) => {
      setMessages((prev) => prev.slice(0, -1)); // Remove optimistic message
    },
    onSettled: () => {
      setIsLoading(false);
    },
  });

  const sendMessage = useCallback(
    (message: string, context?: { language?: string; crop?: string; location?: string }) => {
      if (!message.trim()) return;
      sendMessageMutation.mutate({ message, conversationId, context });
    },
    [conversationId]
  );

  const clearConversation = useCallback(() => {
    setMessages([]);
    setConversationId(null);
  }, []);

  return {
    messages,
    conversationId,
    isLoading,
    sendMessage,
    clearConversation,
  };
}
```

### Chat Component

```tsx
// components/Chat/ChatInterface.tsx
'use client';

import { useState } from 'react';
import { useChat } from '@/hooks/useChat';
import { MessageCircle, Send, X, Mic, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export function ChatInterface() {
  const [input, setInput] = useState('');
  const { messages, conversationId, isLoading, sendMessage, clearConversation } = useChat();
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage(input);
      setInput('');
    }
  };

  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center">
        <MessageCircle className="w-16 h-16 text-muted-foreground/50 mb-4" />
        <h2 className="text-xl font-semibold mb-2">Welcome to MyFarm AI</h2>
        <p className="text-muted-foreground max-w-md">
          Ask me anything about farming — crops, weather, soil, pests, or government schemes.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              'flex gap-3 max-w-[80%]',
              message.role === 'user' ? 'self-end flex-row-reverse' : 'self-start'
            )}
          >
            <div
              className={cn(
                'rounded-2xl px-4 py-2 max-w-[75%]',
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              )}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-center gap-2">
            <Loader2 className="w-5 h-5 animate-spin text-primary" />
            <span className="text-sm text-muted-foreground">Thinking...</span>
          </div>
        )}
      </div>

      <div className="border-t p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <button
            type="button"
            onClick={() => setShowClearConfirm(true)}
            className="p-2 text-muted-foreground hover:text-foreground"
            title="Clear conversation"
          >
            <X className="w-5 h-5" />
          </button>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about crops, weather, soil..."
            className="flex-1 px-4 py-2 border rounded-full focus:outline-none focus:ring-2 focus:ring-primary"
            disabled={isLoading}
            placeholder="Ask about crops, weather, soil..."
          />

          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="p-2 bg-primary text-primary-foreground rounded-full disabled:opacity-50"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
}
```

## Weather Integration

### Weather Hook

```typescript
// hooks/useWeather.ts
'use client';

import { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { WeatherResponse } from '@/lib/api/types';

export function useWeather(latitude?: number, longitude?: number) {
  const { data: weather, isLoading, error, refetch } = useQuery({
    queryKey: ['weather', latitude, longitude],
    queryFn: () => apiClient.getWeather(latitude!, longitude!),
    enabled: latitude !== undefined && longitude !== undefined,
    staleTime: 1000 * 60 * 10, // 10 minutes
  });

  const currentWeather = weather?.current_weather;
  const forecast = weather?.daily;

  return {
    weather,
    currentWeather,
    forecast,
    isLoading,
    error,
    refetch,
  };
}
```

### Weather Component

```tsx
// components/Weather/WeatherCard.tsx
'use client';

import { useWeather } from '@/hooks/useWeather';
import { getWeatherDescription } from '@/lib/utils/weatherCodes';
import { Sun, Cloud, CloudRain, Droplets, Wind } from 'lucide-react';

export function WeatherCard({ latitude, longitude }: { latitude: number; longitude: number }) {
  const { currentWeather, forecast, isLoading, error } = useWeather(latitude, longitude);

  if (isLoading) return <div className="animate-pulse h-32" />;
  if (error) return <div className="text-red-500">Failed to load weather</div>;
  if (!currentWeather) return null;

  return (
    <div className="rounded-xl border p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Current Weather</h3>
        <span className="text-sm text-muted-foreground">
          {new Date(currentWeather.time).toLocaleTimeString()}
        </span>
      </div>

      <div className="grid grid-cols-4 gap-4 text-center">
        <div>
          <p className="text-2xl font-bold">{currentWeather.temperature}°C</p>
          <p className="text-sm text-muted-foreground">Temperature</p>
        </div>
        <div>
          <p className="text-2xl font-bold">{currentWeather.windspeed} km/h</p>
          <p className="text-sm text-muted-foreground">Wind</p>
        </div>
        <div>
          <p className="text-2xl font-bold">{currentWeather.weathercode}</p>
          <p className="text-sm text-muted-foreground">Code</p>
        </div>
        <div>
          <p className="text-2xl font-bold">{getWeatherDescription(currentWeather.weathercode)}</p>
        </div>
      </div>

      {forecast && forecast.length > 0 && (
        <div>
          <h4 className="font-medium mb-2">7-Day Forecast</h4>
          <div className="grid grid-cols-7 gap-2 overflow-x-auto pb-2">
            {forecast.slice(0, 7).map((day) => (
              <div key={day.date} className="min-w-[80px] rounded-lg border p-2 text-center">
                <p className="text-xs font-medium">{new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}</p>
                <p className="text-sm">{getWeatherDescription(day.weathercode)}</p>
                <p className="text-sm font-medium">{day.temperature_2m_max}°/{day.temperature_2m_min}°</p>
                <p className="text-xs text-muted-foreground">{day.precipitation_probability_max}% rain</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

## Agricultural Resources Integration

### Resources Hook

```typescript
// hooks/useResources.ts
'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { ResourcesResponse, AgriculturalResource } from '@/lib/api/types';

export function useResources() {
  const [category, setCategory] = useState<string | null>(null);

  const { data: resourcesData, isLoading, error } = useQuery({
    queryKey: ['resources', category],
    queryFn: () => (category ? apiClient.getResources(category) : apiClient.getResources()),
  });

  const { data: categories } = useQuery({
    queryKey: ['resource-categories'],
    queryFn: () => apiClient.getCategories(),
  });

  return {
    resources: resourcesData?.resources || [],
    total: resourcesData?.total || 0,
    categories: categories || [],
    category,
    setCategory,
    isLoading,
    error,
  };
}
```

## Speech Integration (Web Speech API)

### Speech-to-Text Hook

```typescript
// hooks/useSpeechRecognition.ts
'use client';

import { useState, useRef, useCallback, useEffect } from 'react';

export function useSpeechRecognition(language = 'hi-IN') {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.lang = language;
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;

      recognitionRef.current.onresult = (event) => {
        let finalTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          }
        }
        if (finalTranscript) {
          setTranscript((prev) => prev + ' ' + finalTranscript);
        }
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }

    return () => {
      recognitionRef.current?.stop();
    };
  }, [language]);

  const startListening = useCallback(() => {
    if (recognitionRef.current && !isListening) {
      setTranscript('');
      recognitionRef.current.start();
      setIsListening(true);
    }
  }, []);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
    setIsListening(false);
  }, []);

  const resetTranscript = useCallback(() => {
    setTranscript('');
  }, []);

  return {
    isListening,
    transcript,
    startListening,
    stopListening,
    resetTranscript,
  };
}
```

### Text-to-Speech Hook

```typescript
// hooks/useSpeechSynthesis.ts
'use client';

import { useState, useCallback } from 'react';

export function useSpeechSynthesis() {
  const [isSpeaking, setIsSpeaking] = useState(false);

  const speak = useCallback(
    (text: string, language = 'hi-IN') => {
      if (!('speechSynthesis' in window)) return;

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = language;
      utterance.rate = 0.9;
      utterance.pitch = 1;

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);
    }, []);

  const stop = useCallback(() => {
    window.speechSynthesis.cancel();
  }, []);

  return { speak, stop, isSpeaking };
}
```

## UI Components

### Tailwind Setup

```css
/* app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 142 76% 36%;
    --primary-foreground: 355 7% 97%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --border: 214.3 31.8% 91.4%;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --primary: 142 70% 45%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --border: 217.2 32.6% 17.5%;
  }
}

@layer utilities {
  .animate-pulse-slow {
    animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }
}
```

### Utility Functions

```typescript
// lib/utils.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

## Deployment

### Vercel Deployment

```json
// vercel.json
{
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "env": {
    "NEXT_PUBLIC_API_BASE_URL": "@api-base-url"
  }
}
```

### Environment Variables

| Variable | Development | Production |
|----------|-------------|------------|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000/api/v1` | `https://api.myfarmai.example.com/api/v1` |

### Build Commands

```bash
# Development
npm run dev

# Production build
npm run build

# Preview production build
npm start
```

## CORS Configuration

Ensure backend CORS allows your web domain:

```bash
# .env (backend)
CORS_ALLOWED_ORIGINS=https://myfarmai.example.com,https://www.myfarmai.example.com
```

## Production Checklist

- [ ] HTTPS enforced
- [ ] CORS restricted to production domains
- [ ] API rate limits configured
- [ ] Error boundaries implemented
- [ ] Analytics/privacy compliant
- [ ] CSP headers configured
- [ ] PWA manifest configured
- [ ] Service worker for offline (optional)
- [ ] CDN configured for static assets
- [ ] Monitoring/alerting configured

## Testing Checklist

- [ ] Chat sends/receives messages
- [ ] Conversation continuity works
- [ ] Weather displays current + forecast
- [ ] Resources list and filter by category
- [ ] Speech recognition works (Hindi/English)
- [ ] Text-to-speech plays
- [ ] Request ID in response headers
- [ ] CORS works from production domain
- [ ] Rate limiting triggers (429)
- [ ] Error boundaries catch errors
- [ ] Responsive design works mobile/desktop
- [ ] Dark mode works
- [ ] Accessibility (ARIA, keyboard nav)