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