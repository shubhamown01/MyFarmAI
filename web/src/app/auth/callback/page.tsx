'use client';

import { Suspense, useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ApiError, apiClient } from '@/lib/api/client';

// OAuth callback (E2): the provider redirects back here with ?code&state&state.
// We hand both to the backend, which validates them server-side and sets the
// session cookie, then continue to onboarding. Owner blocker B1 (no OAuth
// apps configured yet) surfaces as OAUTH_NOT_CONFIGURED → shown honestly.
export default function OAuthCallbackPage() {
  return (
    <Suspense fallback={
      <main className="flex min-h-screen items-center justify-center bg-surface px-4">
        <p role="status" className="text-[14px] text-on-surface-variant">Completing sign-in…</p>
      </main>
    }>
      <OAuthCallbackInner />
    </Suspense>
  );
}

function OAuthCallbackInner() {
  const router = useRouter();
  const params = useSearchParams();
  const started = useRef(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    const provider = params.get('provider') || 'google';
    const code = params.get('code');
    const state = params.get('state');
    const redirectUri = `${window.location.origin}/auth/callback?provider=${provider}`;

    if (!code || !state) {
      setError('Missing authorization response. Please start again.');
      return;
    }

    apiClient
      .oauthCallback(provider, code, state, redirectUri)
      .then(() => router.push('/onboarding'))
      .catch((err) => {
        if (err instanceof ApiError && err.code === 'OAUTH_EMAIL_TAKEN') {
          setError('This email already has an account. Sign in with your password instead.');
        } else if (err instanceof ApiError && err.code === 'OAUTH_NOT_CONFIGURED') {
          setError('This sign-in provider is not configured yet.');
        } else {
          setError('Sign-in failed. Please try again.');
        }
      });
  }, [params, router]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-surface px-4">
      <div className="w-full max-w-sm rounded-2xl border border-outline bg-background p-6 text-center">
        {error ? (
          <>
            <p role="alert" className="text-[14px] text-error">
              {error}
            </p>
            <a href="/auth/login" className="mt-4 inline-block text-[13px] font-medium text-primary hover:underline">
              Back to sign in
            </a>
          </>
        ) : (
          <p role="status" className="text-[14px] text-on-surface-variant">
            Completing sign-in…
          </p>
        )}
      </div>
    </main>
  );
}
