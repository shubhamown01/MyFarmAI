import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Download MyFarmAI 1.0.0',
  description:
    'Download the official MyFarmAI Android APK, verify its SHA-256 checksum, and open the web app.',
};

const VERSION = '1.0.0';
const RELEASED = '10 November 2026';
const APK_URL =
  'https://github.com/shubhamown01/MyFarmAI/releases/download/v1.0.0/app-release.apk';
const RELEASE_URL = 'https://github.com/shubhamown01/MyFarmAI/releases/tag/v1.0.0';
const ISSUES_URL = 'https://github.com/shubhamown01/MyFarmAI/issues';
const SHA256 = '352020c56819c9349e139204692c4a01ba21ca4a8401a6601f5ef4072192c465';
const SIZE = '67,884,479 bytes (64.7 MiB)';

const INSTALL_STEPS = [
  'Download the APK on your Android phone using the button above.',
  'If Android asks, allow your browser to install unknown apps (Settings → Apps → Special access → Install unknown apps).',
  'Open the downloaded file and confirm the install.',
  'Launch MyFarmAI AI and sign in with the account provided to you.',
] as const;

const LIMITATIONS = [
  'Self-registration needs an emailed verification code. Email delivery is not enabled on the current hosted deployment, so new accounts cannot be created there yet.',
  'The hosted deployment runs with the local AI model disabled, so the assistant and research features report themselves as unavailable there.',
  'MyFarmAI is not on Google Play. The APK is a direct install, so Android shows the usual sideload warnings.',
  'There are no push notifications. The app states this in Settings.',
  'There is no in-app update checker yet. Check this page for new versions.',
] as const;

export default function DownloadPage() {
  return (
    <div className="min-h-dvh bg-surface text-on-surface">
      <header className="mx-auto flex max-w-3xl items-center justify-between px-4 py-5 sm:px-6">
        <Link href="/landing" className="flex items-center gap-2 text-[17px] font-semibold">
          <span aria-hidden="true" className="text-primary">
            🌱
          </span>
          MyFarm AI
        </Link>
        <nav aria-label="Primary" className="flex items-center gap-3 text-[14px]">
          <Link
            href="/auth/login"
            className="rounded-xl px-4 py-2 font-medium transition-colors hover:bg-surface-container-low"
          >
            Open web app
          </Link>
        </nav>
      </header>

      <main className="mx-auto max-w-3xl px-4 pb-16 sm:px-6">
        <h1 className="text-[32px] font-bold tracking-[-0.025em] sm:text-[40px]">
          Download MyFarmAI
        </h1>
        <p className="mt-2 text-[16px] leading-7 text-on-surface-variant">
          Agricultural answers, weather and crop planning in one app. Version {VERSION},
          released {RELEASED}.
        </p>

        <div className="mt-8 grid gap-3 sm:grid-cols-2">
          <a
            href={APK_URL}
            className="flex h-12 items-center justify-center rounded-xl bg-primary px-5 text-[15px] font-medium text-on-primary transition-opacity hover:opacity-90"
          >
            Download Android APK
          </a>
          <Link
            href="/auth/login"
            className="flex h-12 items-center justify-center rounded-xl border border-outline px-5 text-[15px] font-medium transition-colors hover:bg-surface-container-low"
          >
            Use the web app
          </Link>
        </div>

        <section aria-labelledby="artifact" className="mt-10">
          <h2 id="artifact" className="text-[19px] font-semibold">
            Release artifact
          </h2>
          <dl className="mt-3 divide-y divide-outline rounded-2xl border border-outline text-[14px]">
            {[
              ['Version', `${VERSION} (versionCode 1)`],
              ['Package', 'com.myfarmai.android'],
              ['Released', RELEASED],
              ['File size', SIZE],
              ['SHA-256', SHA256],
              ['Requires', 'Android 6.0 (API 23) or newer'],
            ].map(([label, value]) => (
              <div key={label} className="grid gap-1 px-4 py-3 sm:grid-cols-[140px_1fr]">
                <dt className="font-medium text-on-surface-variant">{label}</dt>
                <dd className={label === 'SHA-256' ? 'break-all font-mono text-[13px]' : ''}>
                  {value}
                </dd>
              </div>
            ))}
          </dl>
          <p className="mt-3 text-[13px] leading-6 text-on-surface-variant">
            Verify the download before installing:{' '}
            <code className="rounded bg-surface-container-low px-1.5 py-0.5 font-mono text-[12px]">
              sha256sum app-release.apk
            </code>{' '}
            must print the value above. Release page:{' '}
            <a href={RELEASE_URL} className="text-primary underline">
              GitHub Releases
            </a>
            .
          </p>
        </section>

        <section aria-labelledby="install" className="mt-10">
          <h2 id="install" className="text-[19px] font-semibold">
            Install the APK
          </h2>
          <ol className="mt-3 list-decimal space-y-2 pl-5 text-[14px] leading-6 text-on-surface-variant">
            {INSTALL_STEPS.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </section>

        <section aria-labelledby="status" className="mt-10">
          <h2 id="status" className="text-[19px] font-semibold">
            Known limitations
          </h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-[14px] leading-6 text-on-surface-variant">
            {LIMITATIONS.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="support" className="mt-10">
          <h2 id="support" className="text-[19px] font-semibold">
            Support and updates
          </h2>
          <p className="mt-3 text-[14px] leading-6 text-on-surface-variant">
            Report a problem or ask a question at{' '}
            <a href={ISSUES_URL} className="text-primary underline">
              github.com/shubhamown01/MyFarmAI/issues
            </a>
            . New versions are announced on this page and on the{' '}
            <a href={RELEASE_URL} className="text-primary underline">
              release page
            </a>
            ; install the newer APK over the existing app — your data is preserved.
          </p>
          <p className="mt-3 text-[14px] leading-6 text-on-surface-variant">
            Read the{' '}
            <Link href="/legal/privacy" className="text-primary underline">
              privacy policy
            </Link>{' '}
            and{' '}
            <Link href="/legal/terms" className="text-primary underline">
              terms of service
            </Link>
            .
          </p>
        </section>
      </main>
    </div>
  );
}
