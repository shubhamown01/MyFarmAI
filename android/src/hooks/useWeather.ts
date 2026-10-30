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
      } catch {
        setError('Failed to fetch weather');
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const fetchCurrentWeather = useCallback(
    async (latitude: number, longitude: number) => {
      return fetchWeather(latitude, longitude, true);
    },
    [fetchWeather]
  );

  return {
    weather,
    isLoading,
    error,
    fetchWeather,
    fetchCurrentWeather,
  };
}