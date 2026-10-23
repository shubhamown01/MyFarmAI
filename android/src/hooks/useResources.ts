import { useState, useCallback } from 'react';
import { apiClient } from '../lib/api/client';
import { ResourcesResponse, AgriculturalResource } from '../../types/resources';

export function useResources() {
  const [resources, setResources] = useState<AgriculturalResource[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchResources = useCallback(async (category?: string) => {
    setIsLoading(true);
    setError(null);

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
      const categories = await apiClient.getCategories();
      return categories;
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      return [];
    }
  }, []);

  const setCategory = useCallback(
    (category: string | null) => {
      setSelectedCategory(category);
    },
    []
  );

  return {
    resources,
    categories,
    selectedCategory,
    setCategory: setCategory,
    isLoading,
    error,
    fetchResources,
    fetchCategories,
  };
}