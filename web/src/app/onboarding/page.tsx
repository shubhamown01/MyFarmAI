'use client';

import dynamic from 'next/dynamic';
import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ApiError, apiClient } from '@/lib/api/client';
import { STEP_LABELS, firstIncomplete, formatArea, isWaitingState } from '@/lib/onboarding';

// Leaflet touches window at import time — client-only.
const FarmMap = dynamic(() => import('@/components/onboarding/FarmMap'), {
  ssr: false,
  loading: () => <div className="h-[320px] w-full animate-pulse rounded-xl bg-surface" />,
});

const inputClass =
  'mt-1.5 h-11 w-full rounded-xl border border-outline bg-surface px-3.5 text-[14px] text-on-surface placeholder:text-on-surface-disabled transition-colors hover:border-outline-strong focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/25';

const buttonClass =
  'h-11 w-full rounded-xl bg-primary text-[14px] font-medium text-on-primary transition-opacity hover:opacity-90 disabled:opacity-50';

const AREA_DISCLAIMER =
  'Map-measured areas are estimates, not legal land-survey certificates.';

export default function OnboardingPage() {
  const router = useRouter();
  const [loaded, setLoaded] = useState(false);
  const [step, setStep] = useState<string | null>(null);
  const [verificationStatus, setVerificationStatus] = useState('');

  const load = useCallback(async () => {
    try {
      const status = await apiClient.getOnboardingStatus();
      setVerificationStatus(status.verification_status);
      if (status.complete || status.next_step === null) {
        setStep('done');
      } else {
        setStep(firstIncomplete(status));
      }
    } catch (err) {
      if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
        router.push('/auth/login');
        return;
      }
      setStep('error');
    } finally {
      setLoaded(true);
    }
  }, [router]);

  useEffect(() => {
    load();
  }, [load]);

  const refresh = () => {
    setLoaded(false);
    setStep(null);
    load();
  };

  if (!loaded) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-surface">
        <p role="status" className="text-[14px] text-on-surface-variant">
          Loading your progress…
        </p>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-start justify-center bg-surface px-4 py-10">
      <div className="w-full max-w-lg rounded-2xl border border-outline bg-background p-6">
        <h1 className="text-[20px] font-semibold text-on-surface">Set up your farm</h1>
        {step === 'contact_verified' && <ContactStep />}
        {step === 'verification' && <VerificationStep status={verificationStatus} />}
        {step === 'location' && <LocationStep onDone={refresh} />}
        {step === 'land' && <LandStep onDone={refresh} />}
        {step === 'profile' && <ProfileStep onDone={refresh} />}
        {step === 'done' && <DoneStep />}
        {step === 'error' && (
          <p role="alert" className="mt-4 text-[13px] text-error">
            Could not load your onboarding progress.{' '}
            <button onClick={refresh} className="text-primary hover:underline">
              Retry
            </button>
          </p>
        )}
      </div>
    </main>
  );
}

// ── Waiting states (no form — honest status only) ──────────────────────────

function ContactStep() {
  return (
    <div className="mt-4">
      <p className="text-[14px] text-on-surface-variant">
        First, verify your contact. If you signed up by email, use the link or
        code we sent you. Then continue here.
      </p>
      <Link href="/" className="mt-3 inline-block text-[13px] font-medium text-primary hover:underline">
        Back to home
      </Link>
    </div>
  );
}

function VerificationStep({ status }: { status: string }) {
  if (status === 'rejected') {
    return (
      <div className="mt-4" role="status">
        <p className="text-[14px] text-on-surface-variant">
          Your identity verification was not approved, so farm setup stays locked.
          Contact the MyFarmAI team to resolve this — an administrator can review
          and re-open your account.
        </p>
      </div>
    );
  }

  const message =
    status === 'pending_review'
      ? 'Your identity verification is awaiting manual review. Check back soon.'
      : 'Your account is awaiting administrator approval. Farm setup unlocks once an administrator approves it — this is usually quick.';

  return (
    <div className="mt-4" role="status">
      <p className="text-[14px] text-on-surface-variant">{message}</p>
      <button
        onClick={() => window.location.reload()}
        className="mt-3 text-[13px] font-medium text-primary hover:underline"
      >
        Check again
      </button>
    </div>
  );
}

// ── Location step ──────────────────────────────────────────────────────────

function LocationStep({ onDone }: { onDone: () => void }) {
  const [pin, setPin] = useState<{ lat: number; lon: number } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const detect = () => {
    setError(null);
    if (!('geolocation' in navigator)) {
      setError('Location detection is not available in this browser. Tap the map instead.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => setPin({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
      () => setError('Could not detect your location. Tap the map to place a pin instead.'),
      { timeout: 10000 }
    );
  };

  const save = async () => {
    if (!pin) return;
    setBusy(true);
    setError(null);
    try {
      await apiClient.saveHomeLocation({
        latitude: pin.lat,
        longitude: pin.lon,
        source: 'auto_detected',
      });
      onDone();
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 403
          ? 'Your account must be verified first.'
          : 'Could not save your location. Please try again.'
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mt-4">
      <p className="text-[14px] text-on-surface-variant">
        Where do you live? We use this for local weather and crop advice. You can
        also tap the map to place a pin manually.
      </p>
      <div className="mt-3 flex gap-2">
        <button onClick={detect} type="button" className="h-11 flex-1 rounded-xl border border-outline bg-surface text-[14px] font-medium text-on-surface hover:border-outline-strong">
          Use my location
        </button>
        {pin && (
          <button onClick={save} disabled={busy} className={buttonClass + ' flex-1'}>
            {busy ? 'Saving…' : `Save pin (${pin.lat.toFixed(5)}, ${pin.lon.toFixed(5)})`}
          </button>
        )}
      </div>
      <div className="mt-3">
        <FarmMap points={[]} onAddPoint={(_, __) => {}} pin={pin} onPin={(lat, lon) => setPin({ lat, lon })} />
      </div>
      {error && (
        <p role="alert" className="mt-3 text-[13px] text-error">
          {error}
        </p>
      )}
    </div>
  );
}

// ── Land step ──────────────────────────────────────────────────────────────

function LandStep({ onDone }: { onDone: () => void }) {
  const [points, setPoints] = useState<{ lat: number; lon: number }[]>([]);
  const [plotId, setPlotId] = useState<string | null>(null);
  const [farmId, setFarmId] = useState<string | null>(null);
  const [savedArea, setSavedArea] = useState<string | null>(null);
  const [manualValue, setManualValue] = useState('');
  const [manualUnit, setManualUnit] = useState('acre');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addPoint = (lat: number, lon: number) => setPoints((p) => [...p, { lat, lon }]);

  const saveBoundary = async () => {
    if (!farmId || !plotId || points.length < 3) return;
    setBusy(true);
    setError(null);
    try {
      const plot = await apiClient.saveBoundary(farmId, plotId, points, 'map_drawn');
      setSavedArea(plot.latest_measurement ? formatArea(plot.latest_measurement.conversions) : null);
    } catch (err) {
      setError(
        err instanceof ApiError && err.code === 'INVALID_POLYGON'
          ? 'That shape is not a valid plot boundary (it may self-intersect or be too small). Adjust the points and try again.'
          : 'Could not save the boundary. Please try again.'
      );
    } finally {
      setBusy(false);
    }
  };

  const ensurePlot = async (): Promise<[string, string]> => {
    if (farmId && plotId) return [farmId, plotId];
    const farm = await apiClient.createFarm('My Farm');
    const plot = await apiClient.createPlot(farm.id, 'Plot 1', 'agricultural');
    setFarmId(farm.id);
    setPlotId(plot.id);
    return [farm.id, plot.id];
  };

  const saveManualArea = async () => {
    setBusy(true);
    setError(null);
    try {
      const [fid, pid] = await ensurePlot();
      const value = Number(manualValue);
      await apiClient.saveManualArea(fid, pid, value, manualUnit);
      onDone();
    } catch (err) {
      setError('Could not save the area. Check the value and try again.');
    } finally {
      setBusy(false);
    }
  };

  const saveAndContinue = async () => {
    setBusy(true);
    setError(null);
    try {
      await ensurePlot();
      await saveBoundary();
      onDone();
    } catch (err) {
      setError('Could not save your land. Please try again.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mt-4">
      <p className="text-[14px] text-on-surface-variant">
        Tap the map at least 3 times to outline your land boundary — or enter
        the area manually if you know it.
      </p>
      <div className="mt-3">
        <FarmMap points={points} onAddPoint={addPoint} pin={null} />
      </div>
      <div className="mt-2 flex items-center justify-between text-[13px] text-on-surface-variant">
        <span>
          {points.length} point{points.length === 1 ? '' : 's'} placed
        </span>
        {points.length > 0 && (
          <button type="button" onClick={() => setPoints([])} className="text-primary hover:underline">
            Clear
          </button>
        )}
      </div>

      <button
        type="button"
        onClick={saveAndContinue}
        disabled={busy || points.length < 3}
        className={buttonClass + ' mt-3'}
      >
        {busy ? 'Saving…' : 'Save boundary and continue'}
      </button>

      {savedArea && (
        <p role="status" className="mt-3 text-[13px] text-on-surface-variant">
          Area: {savedArea}
        </p>
      )}

      <div className="mt-5 border-t border-outline pt-4">
        <p className="text-[13px] font-medium text-on-surface">Know the exact area?</p>
        <div className="mt-2 flex gap-2">
          <input
            aria-label="Area value"
            type="number"
            min="0"
            step="any"
            value={manualValue}
            onChange={(e) => setManualValue(e.target.value)}
            className={inputClass + ' mt-0 flex-1'}
            placeholder="e.g. 2.5"
          />
          <select
            aria-label="Area unit"
            value={manualUnit}
            onChange={(e) => setManualUnit(e.target.value)}
            className={inputClass + ' mt-0 w-28'}
          >
            <option value="sq_m">m²</option>
            <option value="sq_km">km²</option>
            <option value="hectare">hectare</option>
            <option value="acre">acre</option>
            <option value="sq_ft">ft²</option>
            <option value="sq_yd">yd²</option>
          </select>
        </div>
        <button
          type="button"
          onClick={saveManualArea}
          disabled={busy || !manualValue}
          className="mt-2 h-11 w-full rounded-xl border border-outline bg-surface text-[14px] font-medium text-on-surface hover:border-outline-strong disabled:opacity-50"
        >
          Save manual area and continue
        </button>
        <p className="mt-2 text-[12px] text-on-surface-variant">
          Manual entries are stored as user-reported, separate from map-measured.
        </p>
      </div>

      <p className="mt-4 text-[12px] text-on-surface-variant">{AREA_DISCLAIMER}</p>

      {error && (
        <p role="alert" className="mt-3 text-[13px] text-error">
          {error}
        </p>
      )}
    </div>
  );
}

// ── Profile step ───────────────────────────────────────────────────────────

const FARMING_TYPES = [
  { value: 'home_farming', label: 'Home farming (terrace/kitchen garden)' },
  { value: 'small_outdoor', label: 'Small outdoor plot' },
  { value: 'agricultural', label: 'Agricultural farm' },
  { value: 'other', label: 'Other' },
] as const;

function ProfileStep({ onDone }: { onDone: () => void }) {
  const [fullName, setFullName] = useState('');
  const [farmingType, setFarmingType] = useState('');
  const [experience, setExperience] = useState('');
  const [crops, setCrops] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const save = async () => {
    if (!fullName.trim() || !farmingType) {
      setError('Enter your name and farming type to finish.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await apiClient.saveFarmerProfile({
        full_name: fullName.trim(),
        farming_type: farmingType,
        farming_experience_years: experience ? Number(experience) : undefined,
        intended_crops: crops
          ? crops.split(',').map((c) => c.trim()).filter(Boolean)
          : undefined,
      });
      onDone();
    } catch (err) {
      setError('Could not save your profile. Please try again.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mt-4">
      <p className="text-[14px] text-on-surface-variant">
        Last step — only your name and farming type are required.
      </p>
      <div className="mt-3 space-y-3">
        <div>
          <label htmlFor="full-name" className="text-[13px] font-medium text-on-surface">
            Your name
          </label>
          <input
            id="full-name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className={inputClass}
            required
            maxLength={255}
          />
        </div>
        <div>
          <label htmlFor="farming-type" className="text-[13px] font-medium text-on-surface">
            Farming type
          </label>
          <select
            id="farming-type"
            value={farmingType}
            onChange={(e) => setFarmingType(e.target.value)}
            className={inputClass}
            required
          >
            <option value="" disabled>
              Select…
            </option>
            {FARMING_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="experience" className="text-[13px] font-medium text-on-surface">
            Years of experience (optional)
          </label>
          <input
            id="experience"
            type="number"
            min={0}
            max={100}
            value={experience}
            onChange={(e) => setExperience(e.target.value)}
            className={inputClass}
          />
        </div>
        <div>
          <label htmlFor="crops" className="text-[13px] font-medium text-on-surface">
            Crops you want to grow (optional, comma-separated)
          </label>
          <input
            id="crops"
            value={crops}
            onChange={(e) => setCrops(e.target.value)}
            className={inputClass}
            placeholder="wheat, tomato"
          />
        </div>
      </div>
      <button type="button" onClick={save} disabled={busy} className={buttonClass + ' mt-4'}>
        {busy ? 'Saving…' : 'Finish setup'}
      </button>
      {error && (
        <p role="alert" className="mt-3 text-[13px] text-error">
          {error}
        </p>
      )}
    </div>
  );
}

// ── Done ───────────────────────────────────────────────────────────────────

function DoneStep() {
  return (
    <div className="mt-4">
      <p className="text-[14px] text-on-surface-variant">
        Your farm is set up. You can update everything later in settings.
      </p>
      <Link href="/" className={buttonClass + ' mt-4 inline-flex items-center justify-center'}>
        Go to my farm
      </Link>
    </div>
  );
}
