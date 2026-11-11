import type { Metadata } from 'next';

export const metadata: Metadata = { title: 'Question History' };

export default function HistoryLayout({ children }: { children: React.ReactNode }) {
  return children;
}
