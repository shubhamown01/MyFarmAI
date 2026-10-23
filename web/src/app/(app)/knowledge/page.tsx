import type { Metadata } from 'next';
import { Suspense } from 'react';
import { KnowledgeContent } from './KnowledgeContent';

export const metadata: Metadata = {
  title: 'Knowledge',
};

export default function KnowledgePage() {
  return (
    <div className="mx-auto w-full max-w-[1180px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <div className="mb-6">
        <img
          src="/images/knowledge-community.svg"
          alt="Authentic Indian farming activities, farmer collaboration, and crop management"
          className="w-full h-auto max-w-[560px] mx-auto mb-6"
          width={1000}
          height={750}
          loading="lazy"
          decoding="async"
        />
        <h1 className="text-[28px] font-bold tracking-[-0.025em] text-on-surface sm:text-[32px]">
          Knowledge Library
        </h1>
        <p className="mt-1 max-w-2xl text-[15px] leading-6 text-on-surface-variant">
          Government schemes, market information, advisory guides, and other agricultural
          resources, served by the MyFarmAI backend.
        </p>
      </div>

      <Suspense
        fallback={
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-label="Loading resources">
            {Array.from({ length: 6 }).map((_, index) => (
              <div
                key={index}
                className="h-44 animate-pulse rounded-2xl border border-outline bg-surface-container-low"
              />
            ))}
          </div>
        }
      >
        <KnowledgeContent />
      </Suspense>
    </div>
  );
}
