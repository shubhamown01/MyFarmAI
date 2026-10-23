import type { Metadata } from 'next';
import { Sprout } from 'lucide-react';
import { UnavailablePage } from '@/components/Layout';

export const metadata: Metadata = {
  title: 'Crops',
};

export default function CropsPage() {
  return (
    <div className="mx-auto w-full max-w-[900px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <img
        src="/images/crop-guidance.svg"
        alt="Close-up photography of healthy crop growth and agricultural practices"
        className="w-full h-auto max-w-[520px] mx-auto mb-6"
        width={1000}
        height={750}
        loading="lazy"
        decoding="async"
      />
      <UnavailablePage
        title="Crops"
        description="Crop planning, field records, and crop-specific guidance are not connected to this app yet. The backend has no crop endpoint, so no sample fields are shown here. You can still ask the AI assistant a crop question."
        icon={<Sprout className="h-7 w-7 text-primary" aria-hidden="true" />}
        primaryAction={{ href: '/assistant', label: 'Ask the AI Assistant' }}
        secondaryAction={{ href: '/knowledge', label: 'Browse knowledge' }}
      />
    </div>
  );
}
