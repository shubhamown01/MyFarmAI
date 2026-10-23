import type { Metadata } from 'next';
import { HomeDashboard } from '@/components/Dashboard/HomeDashboard';
import { RightPanel } from '@/components/Layout';

export const metadata: Metadata = {
  title: 'Home',
};

export default function HomePage() {
  return (
    <div className="mx-auto w-full max-w-[1400px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_336px]">
        <HomeDashboard />
        <RightPanel />
      </div>
    </div>
  );
}
