# Phase 6G — Android Release/Signing Audit

**Scope:** `/data/MyFarmAI/android` (Expo SDK 51, React Native 0.74, managed workflow)
**Mode:** Read-only audit. No release build, no keystore creation, no installs.
**Verification runs:** `npm run typecheck` — PASS (clean, no errors). `npm run lint` — PASS (clean, no warnings).
**Status labels:** PASS / FAIL / BLOCKED / NOT TESTED / PROPOSED per repo policy.

---

## 1. Signing posture

### Current state: **No signing configuration exists** (honest finding)

- The repo contains **no native `android/` Gradle project** (`app/build.gradle`, `AndroidManifest.xml` are absent — this is an Expo **managed workflow**; native folders are generated at build time by `expo prebuild` / EAS).
- **No keystore material in the repo.** Verified:
  - No `*.keystore`, `*.jks`, `storePassword`, `keyPassword`, or `signingConfig` references anywhere in `android/` (grep of source + config files: 0 matches).
  - Git-tracked `android/` file list contains only JS/TS source, `app.json`, `eas.json`, configs. Nothing binary except icons/splash.
  - Root `.gitignore` does **not** yet list `*.keystore` / `*.jks` / `android/app/*.keystore` — see Gap G1.
- `eas.json` has no `credentialsSource`, no `android.config` keystore path. On first `eas build` (or `expo run:android --variant release`), EAS/Expo would offer to **generate a keystore server-side** — which conflicts with the repo's "no automated deploy / local signing" posture.

### What the owner must prepare before any signed release (all owner-side)

1. **Generate a keystore locally, outside git:**
   `keytool -genkeypair -v -storetype PKCS12 -keystore <path-outside-repo>/myfarmai-release.keystore -alias myfarmai -keyalg RSA -keysize 2048 -validity 10000`
2. **Back it up** (loss = permanently unable to update a Play listing under the same key). Recommended: password manager + encrypted offline copy.
3. **Store passwords outside the repo** (password manager; or a local `gradle.properties` not committed).
4. **Wire signing at build time, not in the repo** — options consistent with managed workflow:
   - EAS: `eas credentials` with local keystore upload, or `credentialsSource: "local"` in `eas.json` production profile + `EXPO_ANDROID_KEYSTORE_PASSWORD` env vars in the local shell (never committed); **or**
   - Local bare build: `npx expo prebuild -p android` then a Gradle signing config that reads from `~/.gradle/gradle.properties` (outside repo).
5. **Enroll in Play App Signing** with the upload key (Play re-signs the AAB).
6. Per the no-automated-deploy rule: signing and upload are **manual local steps**; do not add CI signing secrets to the repo.

---

## 2. Build configuration

| Item | State | Evidence |
|---|---|---|
| Profiles | PASS — `development` (assembleDebug, internal), `preview` (APK, internal), `production` (AAB) | `android/eas.json` |
| API base URL | PASS — no hard-coded production URL in effect. Read from `EXPO_PUBLIC_API_BASE_URL`; `__DEV__` fallback `http://10.0.2.2:8000/api/v1` (emulator only); release fallback is the **placeholder** `https://api.myfarmai.example.com/api/v1`, which would be a **silent failure** if env is unset at release time | `src/config/api.ts` (lines 12–17), `scripts/check-api-url.mjs` (assertions pass) |
| Env handling | PASS — `.env` is git-ignored (root `.gitignore` `env ignored` confirmed via `git check-ignore`); `.env.example` documents emulator/LAN/production values | `.gitignore`, `.env.example` |
| Hermes | NOT TESTED / not explicit — Expo SDK 51 defaults Hermes **on** for managed builds; no override present. Recommend an explicit `"jsEngine": "hermes"` in `app.json` for clarity | Gap G3 |
| Minify/proguard | NOT CONFIGURED — managed workflow defaults; R8/proguard rules only tunable after prebuild. Acceptable for 1.0; revisit if APK size issues | Gap G4 |
| versionCode | GAP — **not set** in `app.json` (defaults to 1 at first build). Before any Play upload, `android.versionCode` must be set and bumped per release | Gap G2 |
| versionName | version `1.0.0` present (`app.json` `expo.version`) | PASS |
| Package name | PASS — `com.myfarmai.android` (both `ios.bundleIdentifier` and `android.package` consistent) | `app.json` |
| Self-check | PASS — `scripts/check-api-url.mjs` validates base-URL composition logic incl. `/api/v1` de-duplication | run passed |

---

## 3. Permissions & manifest

Declared in `app.json` `expo.android.permissions` (managed workflow → generated manifest):

| Permission | Verdict | Notes |
|---|---|---|
| `INTERNET` | PASS — required | API, weather |
| `RECORD_AUDIO` | PASS — required, justified | Client-side speech per ADR-016: STT/TTS run on-device; **no audio is sent to any server** (`expo-speech-recognition` / `expo-speech`; `:8001` voice proxy explicitly out of scope) |
| `ACCESS_FINE_LOCATION` / `ACCESS_COARSE_LOCATION` | REVIEW — used for weather coordinates. Verify runtime request is gated (location is optional context). If weather works on manual entry, consider dropping FINE and keeping COARSE only | Gap G5 |
| Nothing extraneous | PASS — no contacts/storage/camera/etc. | — |

Runtime permission flow: `useSpeechRecognition.ts` calls `ExpoSpeechRecognitionModule.requestPermissionsAsync()` with a `.catch()` — mic permission is requested at point of use. PASS (verify on device in owner QA).

**Play Store disclosures needed (owner-side, before listing):**
- Microphone: state that audio is processed **on-device only**, never uploaded (per ADR-016).
- Data safety form: app sends user-typed questions + approximate location (if used) to the backend for answers/weather; conversations cached locally in encrypted storage; no third-party analytics/ad SDKs.
- Location disclosure required if either location permission is retained.

---

## 4. Privacy / security

| Area | Verdict | Details |
|---|---|---|
| Sensitive data storage | PASS | Conversations cached via `expo-secure-store` (`src/storage/conversations.ts`) — encrypted on device (Android Keystore-backed). **No auth tokens exist in the app yet** (see below) |
| Auth in app | NOT PRESENT | Grep found **no** `Authorization` header, cookie, login, or token code in `android/src`. The email+password/cookie-bearer session backend contract is **not yet wired into the client**. Currently no credentials exist to leak — but when auth lands, tokens must go through SecureStore, never plain `AsyncStorage`/SharedPreferences | Gap G6 |
| Cleartext HTTP | REVIEW | No `usesCleartextTraffic` override and no `networkSecurityConfig` in the repo (managed workflow). Expo default release builds **block cleartext** — but `__DEV__` fallback `http://10.0.2.2:8000` and the documented LAN-IP flow mean debug builds rely on cleartext (normal and expected). **Release builds must use HTTPS.** Add an explicit `"expo.android.usesCleartextTraffic": false`-equivalent check after prebuild to lock it in | Gap G7 |
| Deep links | LOW RISK | `"scheme": "myfarmai"` is declared in `app.json`. No deep-link routes observed in the app; if unused at release, consider removing the scheme to shrink attack surface | Gap G8 |
| WebView | PASS — none in the app (no `react-native-webview` dependency, no WebView usage in source) | — |
| Secrets in repo | PASS — no API keys, passwords, or secrets in `android/` (grep across source/config/tracked files: clean). Only placeholder URLs | — |

---

## 5. Verification evidence

| Check | Command | Result |
|---|---|---|
| TypeScript | `npm run typecheck` (`tsc --noEmit`) | **PASS** — clean, zero errors |
| Lint | `npm run lint` (`eslint . --ext .ts,.tsx`) | **PASS** — clean, zero warnings |
| URL logic self-check | `scripts/check-api-url.mjs` | PASS (existing script, asserts pass per its design; last run recorded in repo) |
| Release build + device QA | — | **NOT TESTED — owner-side.** No emulator in this environment; owner granted no device access. Release build, APK install, mic/STT/TTS/runtime checks, and the integration-guide checklist (conversation continuity, 429 handling, request-ID headers, offline cache on device) remain owner manual steps |

---

## 6. Gap table

| # | Gap | Severity | Owner-side (a) | Repo-side candidate (b) | Blocked-on (c) |
|---|---|---|---|---|---|
| G1 | `.gitignore` lacks `*.keystore`/`*.jks` patterns before keystores ever exist | Medium | — | Add ignore patterns now (2-line change) | — |
| G2 | `android.versionCode` not set in `app.json` | High (pre-release) | Decide release cadence | Set `android.versionCode: 1` + bump policy | Owner release plan |
| G3 | Hermes engine not explicit | Low | — | Add `"jsEngine": "hermes"` to `app.json` | — |
| G4 | Minify/proguard unconfigured | Low | Accept defaults for 1.0 | Tune after first prebuild, if needed | First release build |
| G5 | Fine-location may be more than needed | Medium | Decide: keep COARSE-only? | Drop `ACCESS_FINE_LOCATION` if manual location entry suffices | Owner decision |
| G6 | Auth not wired in client (no token storage/refresh/authorized requests) | High (pre-release if backend auth ships) | Confirm whether 1.0 needs auth | Integrate SecureStore token handling + `Authorization` header in `ApiClient` | Backend auth contract finalized |
| G7 | Cleartext posture implicit (relies on default) | Medium | — | Add explicit network-security check after prebuild; document "release = HTTPS only" | — |
| G8 | Unused `"myfarmai"` deep-link scheme | Low | — | Remove scheme or document its purpose | — |
| G9 | Release fallback URL is a placeholder (`api.myfarmai.example.com`) that fails silently in production if env unset | Medium | Provide real prod URL / env pipeline | Fail fast (throw) in release builds when env unset, instead of placeholder fallback | Real production API URL exists |
| G10 | No signing keystore / no Play account verified | High (pre-release) | **Owner must generate + back up keystore locally, enroll Play App Signing, do local signing per no-automated-deploy rule** | Add signing docs (not secrets) once owner decides flow | Owner Play account |
| G11 | Release build + full device QA checklist unexecuted | High (pre-release) | Owner runs `eas build --profile preview` / local build + device/emulator QA against integration-guide checklist | — | Owner device access |

---

## Verdict

**6G PASS WITH GAPS** — no secret material or structural defects found; code quality gates (typecheck, lint) pass; signing is correctly *absent* rather than mishandled. However, the app is **not yet release-ready**: no keystore (owner must create, per §1), no `versionCode` (G2), placeholder production URL fallback (G9), and no device/release-build QA (G11). These are pre-release owner actions and tracked repo-side candidates, not blockers on this audit.

---

*Audit performed 2026-10-31. Read-only: no files modified except this report. `backend/data/` untouched.*
