import type { Metadata } from 'next';
import { Users } from 'lucide-react';
import { UnavailablePage } from '@/components/Layout';

export const metadata: Metadata = {
  title: 'Community',
};

export default function CommunityPage() {
  return (
    <div className="mx-auto w-full max-w-[900px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <img
        src="/images/empty-states/empty-community.svg"
        alt="Farmer collaboration and community discussion"
        className="w-full h-auto max-w-[420px] mx-auto mb-6"
        width={400}
        height={300}
        loading="lazy"
        decoding="async"
      />
      <UnavailablePage
        title="Community"
        description="Community posts, farmer discussions, and profiles are not available yet. The backend does not include community features, so there are no posts to browse here."
        icon={<Users className="h-7 w-7 text-icon-purple" aria-hidden="true" />}
        primaryAction={{ href: '/assistant', label: 'Ask the AI Assistant' }}
        secondaryAction={{ href: '/knowledge', label: 'Browse knowledge' }}
      />
    </div>
  );
}
