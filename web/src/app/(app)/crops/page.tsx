import type { Metadata } from 'next';
import { CropPlanning } from '@/components/Crops/CropPlanning';

export const metadata: Metadata = {
  title: 'Crops',
};

export default function CropsPage() {
  return (
    <div className="mx-auto w-full max-w-[900px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <CropPlanning />
    </div>
  );
}
