import type { Metadata } from 'next';
import { Bug } from 'lucide-react';
import { UnavailablePage } from '@/components/Layout';

export const metadata: Metadata = {
  title: 'Pest & Disease',
};

export default function PestDiseasePage() {
  return (
    <div className="mx-auto w-full max-w-[900px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 mb-6">
        <img
          src="/images/plant-disease.svg"
          alt="Crop leaves showing distinguishable plant disease symptoms"
          className="w-full h-auto aspect-[4:3] object-cover"
          width={1000}
          height={750}
          loading="lazy"
          decoding="async"
        />
        <img
          src="/images/pest-identification.svg"
          alt="Macro photography of common agricultural pests on crops"
          className="w-full h-auto aspect-[4:3] object-cover"
          width={1000}
          height={750}
          loading="lazy"
          decoding="async"
        />
      </div>
      <UnavailablePage
        title="Pest & Disease"
        description="API-only; no user-facing vision interface is currently available. The backend can analyse a leaf photo, but this app has no screen to send one yet, so no photos are collected here. You can describe the symptoms to the AI assistant for general guidance."
        icon={<Bug className="h-7 w-7 text-icon-red" aria-hidden="true" />}
        primaryAction={{
          href: '/assistant?q=How%20can%20I%20identify%20a%20pest%20or%20disease%20on%20my%20crop%3F',
          label: 'Describe symptoms to the assistant',
        }}
        secondaryAction={{ href: '/knowledge?category=advisory', label: 'Browse advisory guides' }}
      />
    </div>
  );
}
