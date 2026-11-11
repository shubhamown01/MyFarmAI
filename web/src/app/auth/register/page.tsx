'use client';

import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ApiError, apiClient } from '@/lib/api/client';

const inputClass =
  'mt-1.5 h-11 w-full rounded-xl border border-outline bg-surface px-3.5 text-[14px] text-on-surface placeholder:text-on-surface-disabled transition-colors hover:border-outline-strong focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/25';

// Email OTP signup (E1): request code → verify → session cookie → onboarding.
// The backend's privacy-aware response means "code sent" never reveals
// whether the address was already registered.
export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [stage, setStage] = useState<'email' | 'verify'>('email');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [devMode, setDevMode] = useState(false);
  const [resendIn, setResendIn] = useState(0);

  useEffect(() => {
    if (resendIn <= 0) return;
    const t = setInterval(() => setResendIn((s) => (s > 0 ? s - 1 : 0)), 1000);
    return () => clearInterval(t);
  }, [resendIn]);

  const requestCode = async (event?: FormEvent) => {
    event?.preventDefault();
    setError(null);
    setMessage(null);
    setBusy(true);
    try {
      const resp = await apiClient.requestEmailOtp(email.trim());
      setDevMode(resp.delivery_mode !== 'provider');
      setStage('verify');
      setMessage('If the email address is valid, a verification code has been sent.');
      // Match the backend's 60 s resend cooldown so the button re-enables
      // when the server will actually accept a request again.
      setResendIn(60);
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        setResendIn(60);
        setMessage(null);
        setError('A code was recently requested. Try again in a minute.');
      } else {
        setError('Could not send the code. Please try again.');
      }
    } finally {
      setBusy(false);
    }
  };

  const verifyCode = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setBusy(true);
    try {
      await apiClient.verifyEmailOtp(email.trim(), code.trim(), password);
      router.push('/onboarding');
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.code === 'OTP_EXPIRED') setError('That code has expired. Request a new one.');
        else if (err.code === 'OTP_MAX_ATTEMPTS')
          setError('Too many attempts. Request a new code.');
        else setError('Invalid or used code. Check the 6-digit code and try again.');
      } else {
        setError('Verification failed. Please try again.');
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-surface px-4">
      <div className="w-full max-w-sm rounded-2xl border border-outline bg-background p-6">
        <h1 className="text-[20px] font-semibold text-on-surface">Create your account</h1>
        <p className="mt-1 text-[13px] text-on-surface-variant">
          {stage === 'email'
            ? 'We will email you a 6-digit verification code.'
            : `Enter the 6-digit code sent to ${email}.`}
        </p>

        {stage === 'email' ? (
          <form onSubmit={requestCode} className="mt-6 space-y-4" noValidate>
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
            <button
              type="submit"
              disabled={busy}
              className="h-11 w-full rounded-xl bg-primary text-[14px] font-medium text-on-primary transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {busy ? 'Sending…' : 'Send code'}
            </button>
          </form>
        ) : (
          <form onSubmit={verifyCode} className="mt-6 space-y-4" noValidate>
            <div>
              <label htmlFor="code" className="text-[13px] font-medium text-on-surface">
                Verification code
              </label>
              <input
                id="code"
                inputMode="numeric"
                autoComplete="one-time-code"
                pattern="[0-9]{6}"
                maxLength={6}
                required
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                className={`${inputClass} text-center text-[18px] tracking-[0.3em]`}
                placeholder="000000"
              />
            </div>
            <div>
              <label htmlFor="password" className="text-[13px] font-medium text-on-surface">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="new-password"
                minLength={8}
                maxLength={128}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={inputClass}
                placeholder="At least 8 characters"
              />
              <p className="mt-1 text-[12px] text-on-surface-variant">
                Used to sign in on the Android app and after logging out.
              </p>
            </div>
            <button
              type="submit"
              disabled={busy || code.length !== 6 || password.length < 8}
              className="h-11 w-full rounded-xl bg-primary text-[14px] font-medium text-on-primary transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {busy ? 'Verifying…' : 'Verify and continue'}
            </button>
            <button
              type="button"
              onClick={() => requestCode()}
              disabled={busy || resendIn > 0}
              className="mt-2 h-11 w-full rounded-xl border border-outline bg-surface text-[14px] font-medium text-on-surface hover:border-outline-strong disabled:opacity-50"
            >
              {resendIn > 0 ? `Resend code (available in ${resendIn}s)` : busy ? 'Sending…' : 'Resend code'}
            </button>
            <button
              type="button"
              onClick={() => {
                setStage('email');
                setCode('');
                setMessage(null);
                setError(null);
                setDevMode(false);
              }}
              className="w-full text-center text-[13px] text-on-surface-variant hover:text-on-surface"
            >
              Use a different email
            </button>
          </form>
        )}

        {devMode && stage === 'verify' && (
          <p role="note" className="mt-3 rounded-xl border border-outline bg-surface p-3 text-[12px] text-on-surface-variant">
            <strong className="font-medium text-on-surface">Development mode:</strong> no real
            email is sent in this environment. The code is written to the server&apos;s outbox
            file: <code className="text-on-surface">backend/data/dev_otp_outbox.txt</code>.
          </p>
        )}

        {message && (
          <p role="status" className="mt-3 text-[13px] text-on-surface-variant">
            {message}
          </p>
        )}
        {error && (
          <p role="alert" className="mt-3 text-[13px] text-error">
            {error}
          </p>
        )}

        <p className="mt-4 text-center text-[13px] text-on-surface-variant">
          Already have an account?{' '}
          <Link href="/auth/login" className="font-medium text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}
