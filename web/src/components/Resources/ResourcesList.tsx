'use client';

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ExternalLink, RefreshCw } from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { AgriculturalResource, ResourcesResponse } from '@/lib/api/types';
import { cn } from '@/lib/utils';

export interface ResourcesListProps {
  initialCategory?: string | null;
}

function CategoryButton({
  active,
  children,
  onClick,
}: {
  active: boolean;
  children: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        'min-h-9 rounded-full border px-3.5 text-[13px] font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
        active
          ? 'border-primary bg-primary text-on-primary'
          : 'border-outline bg-surface text-on-surface hover:bg-surface-container-low',
      )}
    >
      {children}
    </button>
  );
}

export function ResourcesList({ initialCategory = null }: ResourcesListProps) {
  const [category, setCategory] = useState<string | null>(initialCategory);

  useEffect(() => {
    setCategory(initialCategory);
  }, [initialCategory]);

  const resourcesQuery = useQuery<ResourcesResponse>({
    queryKey: ['resources', category],
    queryFn: () => apiClient.getResources(category ?? undefined),
  });

  const resources = resourcesQuery.data?.resources ?? [];
  const categories = resourcesQuery.data?.categories ?? [];

  if (resourcesQuery.isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-label="Loading resources">
        {Array.from({ length: 6 }).map((_, index) => (
          <div
            key={index}
            className="h-44 animate-pulse rounded-2xl border border-outline bg-surface-container-low"
          />
        ))}
      </div>
    );
  }

  if (resourcesQuery.error) {
    return (
      <div className="rounded-2xl border border-outline bg-surface p-8 text-center">
        <p className="text-[15px] font-semibold text-on-surface">Resources are unavailable right now.</p>
        <p className="mx-auto mt-1.5 max-w-md text-[13px] leading-5 text-on-surface-variant">
          The resource service could not be reached. Check your connection, then try again.
        </p>
        <button
          type="button"
          onClick={() => void resourcesQuery.refetch()}
          className="mt-4 inline-flex min-h-10 items-center gap-2 rounded-xl border border-outline px-4 text-[13px] font-semibold text-on-surface transition-colors hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          <RefreshCw className="h-4 w-4" aria-hidden="true" />
          Try again
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-5 flex flex-wrap gap-2" role="group" aria-label="Filter resources by category">
        <CategoryButton active={!category} onClick={() => setCategory(null)}>
          All
        </CategoryButton>
        {categories.map((item) => (
          <CategoryButton
            key={item}
            active={category === item}
            onClick={() => setCategory(item)}
          >
            {item.charAt(0).toUpperCase() + item.slice(1)}
          </CategoryButton>
        ))}
      </div>

      <p className="mb-4 text-[13px] text-on-surface-variant" aria-live="polite">
        {resources.length} {resources.length === 1 ? 'resource' : 'resources'}
        {category ? ` in ${category}` : ''}
      </p>

      {resources.length ? (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" role="list">
          {resources.map((resource: AgriculturalResource) => (
            <li key={resource.url}>
              <a
                href={resource.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex h-full flex-col rounded-2xl border border-outline bg-surface p-5 transition-all hover:-translate-y-0.5 hover:border-outline-strong hover:shadow-elev-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="rounded-full bg-primary-container px-2.5 py-1 text-[11px] font-semibold capitalize text-primary-strong">
                    {resource.category}
                  </span>
                  <span className="truncate text-[11px] text-on-surface-variant">
                    {resource.source}
                  </span>
                </div>
                <h3 className="mt-3 text-[16px] font-semibold leading-6 text-on-surface">
                  {resource.title}
                </h3>
                <p className="mt-2 flex-1 text-[13px] leading-5 text-on-surface-variant">
                  {resource.description}
                </p>
                <span className="mt-4 inline-flex items-center gap-1.5 text-[13px] font-semibold text-primary">
                  Open resource
                  <ExternalLink className="h-4 w-4" aria-hidden="true" />
                </span>
              </a>
            </li>
          ))}
        </ul>
      ) : (
        <div className="rounded-2xl border border-dashed border-outline-strong bg-surface p-8 text-center">
          <img
            src="/images/empty-states/empty-search.svg"
            alt="No resources found"
            className="mx-auto mb-3 max-w-xs h-auto w-full object-contain"
            width={400}
            height={300}
            loading="lazy"
            decoding="async"
          />
          <p className="text-[15px] font-semibold text-on-surface">No resources in this category.</p>
          <p className="mt-1.5 text-[13px] text-on-surface-variant">
            Choose another category or show everything.
          </p>
          {category && (
            <button
              type="button"
              onClick={() => setCategory(null)}
              className="mt-4 inline-flex min-h-10 items-center rounded-xl border border-outline px-4 text-[13px] font-semibold text-on-surface transition-colors hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              Show all resources
            </button>
          )}
        </div>
      )}
    </div>
  );
}
