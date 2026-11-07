'use client';

import { FormEvent, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ApiError, apiClient } from '@/lib/api/client';

const inputClass =
  'mt-1.5 h-11 w-full rounded-xl border border-outline bg-surface px-3.5 text-[14px] text-on-surface placeholder:text-on-surface-disabled transition-colors hover:border-outline-strong focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/25';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await apiClient.login(email.trim(), password);
      router.push('/onboarding');
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 401
          ? 'Incorrect email or password.'
          : 'Sign in failed. Please try again.'
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-surface px-4">
      <div className="w-full max-w-sm rounded-2xl border border-outline bg-background p-6">
        <h1 className="text-[20px] font-semibold text-on-surface">Sign in to MyFarmAI</h1>
        <p className="mt-1 text-[13px] text-on-surface-variant">
          Welcome back. Sign in to continue to your farm.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
          <div>
            <label htmlFor="email" className="text-[13px] font-medium text-on-surface">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClass}
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label htmlFor="password" className="text-[13px] font-medium text-on-surface">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass}
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p role="alert" className="text-[13px] text-error">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="h-11 w-full rounded-xl bg-primary text-[14px] font-medium text-on-primary transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div className="mt-4 space-y-2">
          {['google', 'microsoft'].map((provider) => (
            <button
              key={provider}
              type="button"
              disabled={busy}
              onClick={async () => {
                setError(null);
                setBusy(true);
                try {
                  const redirectUri = `${window.location.origin}/auth/callback?provider=${provider}`;
                  const { authorize_url } = await apiClient.getOAuthAuthorizeUrl(provider, redirectUri);
                  window.location.href = authorize_url;
                } catch {
                  // OAUTH_NOT_CONFIGURED (owner blocker B1) or network failure.
                  setError(`${provider} sign-in is not configured yet. Use email and password.`);
                  setBusy(false);
                }
              }}
              className="h-11 w-full rounded-xl border border-outline bg-surface text-[14px] font-medium text-on-surface transition-colors hover:border-outline-strong disabled:opacity-50"
            >
              Continue with {provider === 'google' ? 'Google' : 'Microsoft'}
            </button>
          ))}
        </div>

        <p className="mt-4 text-center text-[13px] text-on-surface-variant">
          New here?{' '}
          <Link href="/auth/register" className="font-medium text-primary hover:underline">
            Create an account
          </Link>
        </p>
      </div>
    </main>
  );
}
