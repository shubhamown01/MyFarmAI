'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

export function useWeather(latitude?: number, longitude?: number) {
  const {
    data: weather,
    isLoading,
    isFetching,
    error,
    refetch,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ['weather', latitude, longitude],
    queryFn: () => apiClient.getWeather(latitude!, longitude!),
    enabled: latitude !== undefined && longitude !== undefined,
    staleTime: 1000 * 60 * 10,
    retry: 1,
  });

  return {
    weather,
    currentWeather: weather?.current_weather,
    forecast: weather?.daily,
    isLoading,
    isFetching,
    error,
    refetch,
    dataUpdatedAt,
  };
}
