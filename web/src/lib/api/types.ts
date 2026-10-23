export interface ChatRequest {
  message: string;
  conversation_id?: string;
  language?: string;
  crop?: string;
  location?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  conversationId: string;
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
  weather_description?: string;
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