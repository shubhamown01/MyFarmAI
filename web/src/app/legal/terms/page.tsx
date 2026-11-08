import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Terms of Service',
};

const Sect = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <section className="mt-6">
    <h2 className="text-[16px] font-semibold">{title}</h2>
    <div className="mt-2 space-y-2 text-[14px] leading-6 text-on-surface-variant">{children}</div>
  </section>
);

export default function TermsPage() {
  return (
    <main className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
      <h1 className="text-2xl font-semibold">Terms of Service</h1>
      <p className="mt-2 text-[13px] text-on-surface-variant">
        Draft for the current public TEST deployment — reviewed by the project owner before production use.
      </p>

      <Sect title="What this service is">
        <p>MyFarm AI is a free test deployment for agricultural information — an AI chat, weather lookups and crop planning tools. It is not a substitute for professional agronomic, legal or financial advice.</p>
      </Sect>

      <Sect title="Responsible use">
        <p>Create accounts only with your own, valid email address. Don&apos;t attempt to access another user&apos;s data, overload the service, or use it for unlawful purposes. Test data must be synthetic.</p>
      </Sect>

      <Sect title="Availability and quotas">
        <p>AI question usage is limited (per-user and per-time-window limits enforced by the service). Features may change, pause or be removed during testing without notice.</p>
      </Sect>

      <Sect title="No warranty">
        <p>The service is provided &quot;as is&quot; during testing, without warranties. Always verify critical actions (spraying schedules, treatment doses) against local regulations and professional guidance.</p>
      </Sect>

      <Sect title="Contact">
        <p>Report issues or feedback through the project owner; testers should use the dedicated feedback path shared in the tester guide.</p>
      </Sect>
    </main>
  );
}
