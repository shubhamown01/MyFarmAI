import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Privacy Policy',
};

const Sect = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <section className="mt-6">
    <h2 className="text-[16px] font-semibold">{title}</h2>
    <div className="mt-2 space-y-2 text-[14px] leading-6 text-on-surface-variant">{children}</div>
  </section>
);

export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
      <h1 className="text-2xl font-semibold">Privacy Policy</h1>
      <p className="mt-2 text-[13px] text-on-surface-variant">
        Draft for the current public TEST deployment — account creation is limited to
        approved testers. Reviewed by the project owner before production use.
      </p>

      <Sect title="What we collect">
        <p>Email address and a one-time verification code when you create an account; the code itself is never stored readable — only a hash.</p>
        <p>Farmer profile details you enter voluntarily, plus the farms, plots and crop plans you create.</p>
        <p>Operational logs (request IDs, timestamps, error events) used to keep the service working.</p>
      </Sect>

      <Sect title="What we do NOT collect">
        <p>No passwords in plain text, no payment data, no device trackers or advertising identifiers, and no content from your files beyond what you explicitly submit (e.g. a leaf photo for diagnosis).</p>
      </Sect>

      <Sect title="How data is used">
        <p>Only to operate the app: authenticating you, answering agricultural questions, storing the farms you create, sending verification codes, and diagnosing errors.</p>
        <p>AI answers may be processed by the configured model service; never expose personal data in questions.</p>
      </Sect>

      <Sect title="Where data lives">
        <p>Accounts, farms and logs live in cloud-hosted infrastructure with the project owner; chat transcripts are stored on your device session only.</p>
        <p>Contact: put testing-related requests through the project owner.</p>
      </Sect>

      <Sect title="Your controls">
        <p>Log out any time from Settings. For test-period account removal or data export, contact the project owner.</p>
      </Sect>
    </main>
  );
}
