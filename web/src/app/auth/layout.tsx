import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: { default: 'Sign in', template: '%s · MyFarmAI' },
};

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return children;
}
