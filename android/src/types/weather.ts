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

export interface WeatherErrorResponse {
  detail: string;
  error_code?: string;
}