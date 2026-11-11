'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Check, LogOut, MapPin, User } from 'lucide-react';
import { apiClient, ApiError } from '@/lib/api/client';
import { useProfile } from '@/hooks/useProfile';
import { useTheme } from '@/providers';
import { cn } from '@/lib/utils';

const THEME_OPTIONS = [
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
  { value: 'system', label: 'System' },
] as const;

const inputClass =
  'mt-1.5 h-11 w-full rounded-xl border border-outline bg-surface px-3.5 text-[14px] text-on-surface placeholder:text-on-surface-disabled transition-colors hover:border-outline-strong focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/25';

export default function SettingsPage() {
  const { profile, updateProfile } = useProfile();
  const { mode, setTheme } = useTheme();
  const router = useRouter();
  const [name, setName] = useState(profile.name);
  const [locationLabel, setLocationLabel] = useState(profile.locationLabel);
  const [latitude, setLatitude] = useState(String(profile.latitude));
  const [longitude, setLongitude] = useState(String(profile.longitude));
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [loggingOut, setLoggingOut] = useState(false);
  const [logoutError, setLogoutError] = useState<string | null>(null);

  const handleLogout = async () => {
    setLoggingOut(true);
    setLogoutError(null);
    try {
      await apiClient.logout(); // 204; clears the session cookie
      router.push('/auth/login');
    } catch {
      setLogoutError('Could not log out. Check your connection and retry.');
      setLoggingOut(false);
    }
  };

  useEffect(() => {
    setName(profile.name);
    setLocationLabel(profile.locationLabel);
    setLatitude(String(profile.latitude));
    setLongitude(String(profile.longitude));
  }, [profile.name, profile.locationLabel, profile.latitude, profile.longitude]);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setStatus(null);

    const cleanName = name.trim();
    const cleanLocation = locationLabel.trim();
    const parsedLatitude = Number(latitude);
    const parsedLongitude = Number(longitude);

    if (!cleanName) {
      setError('Enter your name.');
      return;
    }
    if (!cleanLocation) {
      setError('Enter a location name, such as “Durg, CG”.');
      return;
    }
    if (
      !Number.isFinite(parsedLatitude) ||
      parsedLatitude < -90 ||
      parsedLatitude > 90
    ) {
      setError('Latitude must be a number between -90 and 90.');
      return;
    }
    if (
      !Number.isFinite(parsedLongitude) ||
      parsedLongitude < -180 ||
      parsedLongitude > 180
    ) {
      setError('Longitude must be a number between -180 and 180.');
      return;
    }

    setError(null);
    updateProfile({
      name: cleanName,
      locationLabel: cleanLocation,
      latitude: parsedLatitude,
      longitude: parsedLongitude,
    });
    setStatus('Profile saved on this device.');
  };

  const clearStatus = () => {
    if (status) setStatus(null);
    if (error) setError(null);
  };

  return (
    <div className="mx-auto w-full max-w-[760px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <div className="mb-6">
        <h1 className="text-[28px] font-bold tracking-[-0.025em] text-on-surface sm:text-[32px]">
          Settings
        </h1>
        <p className="mt-1 text-[15px] text-on-surface-variant">
          Your profile and preferences are stored on this device.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6" noValidate>
        <section
          className="rounded-2xl border border-outline bg-surface p-5 sm:p-6"
          aria-labelledby="profile-heading"
        >
          <div className="flex items-center gap-2">
            <User className="h-5 w-5 text-primary" aria-hidden="true" />
            <h2 id="profile-heading" className="text-[17px] font-semibold text-on-surface">
              Profile
            </h2>
          </div>

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label htmlFor="profile-name" className="text-[13px] font-medium text-on-surface">
                Name
              </label>
              <input
                id="profile-name"
                type="text"
                value={name}
                onChange={(event) => {
                  setName(event.target.value);
                  clearStatus();
                }}
                autoComplete="name"
                className={inputClass}
              />
            </div>

            <div className="sm:col-span-2">
              <label htmlFor="profile-location" className="text-[13px] font-medium text-on-surface">
                Location name
              </label>
              <input
                id="profile-location"
                type="text"
                value={locationLabel}
                onChange={(event) => {
                  setLocationLabel(event.target.value);
                  clearStatus();
                }}
                placeholder="Durg, CG"
                className={inputClass}
              />
            </div>

            <div>
              <label htmlFor="profile-latitude" className="text-[13px] font-medium text-on-surface">
                Latitude
              </label>
              <input
                id="profile-latitude"
                type="number"
                inputMode="decimal"
                step="any"
                min="-90"
                max="90"
                value={latitude}
                onChange={(event) => {
                  setLatitude(event.target.value);
                  clearStatus();
                }}
                className={inputClass}
              />
            </div>

            <div>
              <label htmlFor="profile-longitude" className="text-[13px] font-medium text-on-surface">
                Longitude
              </label>
              <input
                id="profile-longitude"
                type="number"
                inputMode="decimal"
                step="any"
                min="-180"
                max="180"
                value={longitude}
                onChange={(event) => {
                  setLongitude(event.target.value);
                  clearStatus();
                }}
                className={inputClass}
              />
            </div>
          </div>

          <p className="mt-3 flex items-start gap-1.5 text-[12px] leading-5 text-on-surface-variant">
            <MapPin className="mt-0.5 h-3.5 w-3.5 flex-none" aria-hidden="true" />
            The location is used for weather. There is no account service, so these details
            never leave this browser.
          </p>

          {error && (
            <p role="alert" className="mt-4 rounded-lg bg-error-container px-3 py-2 text-[13px] text-on-error-container">
              {error}
            </p>
          )}

          <div className="mt-5 flex flex-wrap items-center gap-3">
            <button
              type="submit"
              className="inline-flex min-h-10 items-center gap-2 rounded-xl bg-primary px-4 text-[14px] font-semibold text-on-primary transition-colors hover:bg-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            >
              Save profile
            </button>
            {status && (
              <p role="status" className="inline-flex items-center gap-1.5 text-[13px] font-medium text-primary">
                <Check className="h-4 w-4" aria-hidden="true" />
                {status}
              </p>
            )}
          </div>
        </section>

        <section
          className="rounded-2xl border border-outline bg-surface p-5 sm:p-6"
          aria-labelledby="account-heading"
        >
          <div className="flex items-center gap-2">
            <LogOut className="h-5 w-5 text-primary" aria-hidden="true" />
            <h2 id="account-heading" className="text-[17px] font-semibold text-on-surface">
              Account
            </h2>
          </div>
          <p className="mt-1 text-[13px] text-on-surface-variant">
            End the session on this device and return to the login page.
          </p>
          <button
            type="button"
            onClick={handleLogout}
            disabled={loggingOut}
            className="mt-4 inline-flex min-h-10 items-center gap-2 rounded-xl border border-outline bg-surface px-4 text-[14px] font-semibold text-on-surface transition-colors hover:border-outline-strong hover:bg-surface-container-low focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loggingOut ? 'Logging out…' : 'Log out'}
          </button>
          {logoutError && (
            <p role="alert" className="mt-4 rounded-lg bg-error-container px-3 py-2 text-[13px] text-on-error-container">
              {logoutError}
            </p>
          )}
        </section>

        <section
          className="rounded-2xl border border-outline bg-surface p-5 sm:p-6"
          aria-labelledby="appearance-heading"
        >
          <h2 id="appearance-heading" className="text-[17px] font-semibold text-on-surface">
            Appearance
          </h2>
          <p className="mt-1 text-[13px] text-on-surface-variant">
            Choose how MyFarmAI looks on this device.
          </p>
          <div
            className="mt-4 grid grid-cols-3 gap-2 rounded-xl bg-surface-container-low p-1.5"
            role="group"
            aria-label="Theme"
          >
            {THEME_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setTheme(option.value)}
                aria-pressed={mode === option.value}
                className={cn(
                  'min-h-10 rounded-lg text-[13px] font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
                  mode === option.value
                    ? 'bg-surface text-on-surface shadow-elev-1'
                    : 'text-on-surface-variant hover:text-on-surface',
                )}
              >
                {option.label}
              </button>
            ))}
          </div>
        </section>

        <section
          className="rounded-2xl border border-outline bg-surface p-5 sm:p-6"
          aria-labelledby="notifications-heading"
        >
          <h2 id="notifications-heading" className="text-[17px] font-semibold text-on-surface">
            Notifications
          </h2>
          <p className="mt-1 text-[13px] leading-5 text-on-surface-variant">
            Notifications are not connected yet. MyFarmAI has no notification service, so
            there are no alerts to configure.
          </p>
        </section>
      </form>

      <FeedbackSection />
    </div>
  );
}

const FEEDBACK_CATEGORIES = [
  { value: 'bug', label: 'Bug' },
  { value: 'feature', label: 'Feature request' },
  { value: 'question', label: 'Question' },
  { value: 'praise', label: 'Praise' },
] as const;

/** Feedback goes to the public, unauthenticated /feedback/submit endpoint. */
function FeedbackSection() {
  const [category, setCategory] = useState<'bug' | 'feature' | 'question' | 'praise'>('bug');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setStatus(null);
    setError(null);
    try {
      await apiClient.submitFeedback({ category, message });
      setStatus('Thank you — your feedback was received.');
      setMessage('');
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'Could not send feedback. Check your connection and retry.'
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <form
      onSubmit={submit}
      className="mt-6 rounded-2xl border border-outline bg-surface p-5 sm:p-6"
      aria-labelledby="feedback-heading"
      noValidate
    >
      <h2 id="feedback-heading" className="text-[17px] font-semibold text-on-surface">
        Send feedback
      </h2>
      <p className="mt-1 text-[13px] leading-5 text-on-surface-variant">
        Report a bug or request a feature. Do not include personal or farm data.
      </p>

      <label htmlFor="feedback-category" className="mt-4 block text-[13px] font-medium text-on-surface">
        Category
      </label>
      <select
        id="feedback-category"
        value={category}
        onChange={(event) => {
          setCategory(event.target.value as typeof category);
          setStatus(null);
          setError(null);
        }}
        className={inputClass}
      >
        {FEEDBACK_CATEGORIES.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      <label htmlFor="feedback-message" className="mt-4 block text-[13px] font-medium text-on-surface">
        Message
      </label>
      <textarea
        id="feedback-message"
        value={message}
        onChange={(event) => {
          setMessage(event.target.value);
          setStatus(null);
          setError(null);
        }}
        rows={4}
        minLength={5}
        maxLength={2000}
        required
        className={`${inputClass} h-auto py-2.5`}
      />

      {status && (
        <p role="status" className="mt-3 text-[13px] text-primary">
          {status}
        </p>
      )}
      {error && (
        <p role="alert" className="mt-3 text-[13px] text-icon-red">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={busy || message.trim().length < 5}
        className="mt-4 h-11 w-full rounded-xl bg-primary text-[14px] font-medium text-on-primary transition-opacity hover:opacity-90 disabled:opacity-50 sm:w-auto sm:px-6"
      >
        {busy ? 'Sending…' : 'Send feedback'}
      </button>
    </form>
  );
}
