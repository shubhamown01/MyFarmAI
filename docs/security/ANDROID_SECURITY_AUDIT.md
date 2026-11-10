# MyFarmAI — Android Security Audit (V1.0.0)

- **Date:** 2026-11-10
- **App:** Expo SDK 51 / React Native 0.74, package `com.myfarmai.android`, version 1.0.0
- **Method:** source review, generated manifest inspection, Gradle/Expo config
  review, `npm audit`, typecheck/lint. No APK dynamic instrumentation was
  performed during this audit.

## 1. Token and data storage

| Data | Storage | Assessment |
|---|---|---|
| Session token | `expo-secure-store` (`src/lib/auth/session.ts`) | PASS — Keystore-backed |
| Refresh token | `expo-secure-store` | PASS |
| Conversations | `expo-secure-store` (`src/storage/conversations.ts`) | PASS |
| Profile / preferences | Server-side; not persisted as auth material | PASS |
| Plaintext token in AsyncStorage | Not found | PASS |

No WebView is used, so there is no JavaScript bridge or mixed-content surface.
Deep links use the custom schemes `myfarmai://` and `com.myfarmai.android://`;
no sensitive data is accepted from link parameters.

## 2. Manifest and permissions

Generated release manifest (`android/android/app/src/main/AndroidManifest.xml`,
gitignored; `android/app.json` is the source of truth):

| Item | State | Assessment |
|---|---|---|
| `INTERNET` | Present | Required |
| `RECORD_AUDIO` | Present | Required for voice input |
| `ACCESS_FINE/COARSE_LOCATION` | Present | Required for weather/onboarding |
| `READ/WRITE_EXTERNAL_STORAGE` | Present (legacy) | Low — unused on modern Android; remove in a future cleanup |
| `SYSTEM_ALERT_WINDOW` | Absent from rebuilt release APK | **Fixed and verified** — blocked via `app.json`, removed by manifest merger |
| `allowBackup` | `true` | Medium/Low — SecureStore values are not restorable; owner decision |
| `MainActivity exported` | `true` | Expected for launcher + deep links; no privileged intent handling |
| Cleartext traffic | Debug manifest only (`usesCleartextTraffic=true`) | PASS — release blocks cleartext by platform default |

## 3. Network security

- Release API base defaults to `https://api.myfarmai.example.com/api/v1` when
  `EXPO_PUBLIC_API_BASE_URL` is unset. This is a placeholder host, not an HTTP
  endpoint; it fails closed (no cleartext fallback).
- Debug builds use `http://10.0.2.2:8000` for the emulator, gated by `__DEV__`
  and the debug manifest's cleartext flag.
- No certificate pinning. For a V1 consumer app this is acceptable; consider
  pinning or at least documenting the trusted CA set if the threat model changes.
- Auth uses Bearer tokens; refresh rotation is implemented in
  `src/lib/api/client.ts`.

## 4. Signing and release process

- Release signing reads `MYFARMAI_KEYSTORE_PATH`, `MYFARMAI_KEYSTORE_PASSWORD`,
  `MYFARMAI_KEY_ALIAS`, `MYFARMAI_KEY_PASSWORD` from the environment. No keystore
  or password is committed.
- **Finding SEC-027:** when the env vars are missing, Gradle silently falls back
  to the public debug keystore for the `release` variant. The process must fail
  closed.
- `enableProguardInReleaseBuilds` defaults to `false`; R8 shrinking is not
  enabled unless the Gradle property is set. This is hardening, not a
  vulnerability (JS bundle is Hermes-compiled; native symbols are limited).
- Prior release evidence records a signed build and verified checksum
  (`docs/release/`); this audit did not re-verify the signature.

## 5. Dependency posture

`npm audit`: 57 advisories — 1 critical (`tar`), 18 high, 29 moderate, 9 low.
Almost all are in build/dev tooling (`@expo/cli`, `tar`, `cacache`, `postcss`,
`node-forge`). Runtime-facing items are navigation/deep-link parsers
(`query-string`/`decode-uri-component`) with low-impact DoS behavior. The
framework itself (Expo 51 / RN 0.74) is EOL and no longer receives patches;
plan an SDK upgrade (SEC-010).

## 6. Findings

| ID | Finding | Severity | Status |
|---|---|---|---|
| SEC-008 | `SYSTEM_ALERT_WINDOW` in release manifest | Medium | Fixed and verified in rebuilt APK |
| SEC-009 | `allowBackup=true` | Medium/Low | Open (owner decision) |
| SEC-010 | EOL Expo/RN framework with advisories | Medium | Open (upgrade plan) |
| SEC-017 | Legacy external-storage permissions | Low | Open |
| SEC-018 | Placeholder production API default | Low | Open |
| SEC-027 | Release signing falls back to debug key | Medium | Open (process guard) |

## 7. Verification

```bash
cd android && npm run typecheck && npm run lint   # PASS
cd android && npm audit                            # 57 advisories (see above)
```

`expo prebuild` regenerated the manifest with
`<uses-permission ... tools:node="remove"/>`; the release APK was rebuilt with
`JAVA_HOME=/data/JDKs/jdk-17.0.21+9`, signed by `CN=MyFarmAI Release`, and
`aapt dump permissions` confirms `SYSTEM_ALERT_WINDOW` is absent. The hosted APK
is byte-identical. SEC-027 (debug fallback when signing env vars are missing)
remains an owner process decision.
