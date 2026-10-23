'use client';

import { useSearchParams } from 'next/navigation';
import { ResourcesList } from '@/components/Resources/ResourcesList';

export function KnowledgeContent() {
  const searchParams = useSearchParams();
  const category = searchParams.get('category')?.toLowerCase() ?? null;

  return <ResourcesList initialCategory={category} />;
}
