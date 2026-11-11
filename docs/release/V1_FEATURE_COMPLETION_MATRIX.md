# MyFarmAI v1.0.0 — Feature Completion Matrix

**Document ID:** MYFARMAI-REL-014
**Version:** 1.0
**Date:** 2026-11-11
**Repository state:** `phase-01-foundation` @ `6976a3f`
**Live web:** https://myfarmai-web-zwpytbwu.onslate.in
**Live API:** https://myfarmai-backend-50047414881.development.catalystappsail.in
**Live image:** `prod-c63d3963-v2` (built 2026-11-10)

## 1. How to read this matrix

Two environments are recorded separately because they are **not the same code**:

- **Repo** — what the committed source at `6976a3f` does, verified by the test suites.
- **Live** — what the deployed web build and API image actually serve. The live image
  predates the 2026-11-11 auth fix, and the web bundle predates MFAI-013/014/016/017.
  No deployment path exists from this host (see `docs/deployment/PRODUCTION_DEPLOYMENT_RUNBOOK.md` §6).

Status vocabulary:

| Status | Meaning |
|---|---|
| **PASS** | Working end-to-end, verified with the evidence cited |
| **PARTIAL** | Implemented, but at least one client path or environment is unverified or degraded |
| **MOCKED** | Placeholder or static content presented in place of the feature |
| **NOT IMPLEMENTED** | No code exists |
| **BLOCKED** | Code exists but a public user cannot use it (dependency, config, or deployment gap) |
| **NOT TESTED** | Code exists, no verification evidence |

A feature is only **PASS** when the complete user workflow was exercised — not because a
button, route, or endpoint exists.

## 2. Environment evidence baseline

| Check | Result | Date |
|---|---|---|
| Backend test suite (`pytest tests/`) | **313 passed**, 31 warnings, 94.87 s | 2026-11-11 |
| Web Jest (`npm test -- --runInBand`) | **44 passed** / 9 suites | 2026-11-11 |
| Web typecheck (`tsc --noEmit`) | clean | 2026-11-11 |
| Web lint (`next lint`) | no warnings or errors | 2026-11-11 |
| Web production build (`npm run build`) | passes, 15 routes | 2026-11-11 |
| Live web `/landing`, `/` | HTTP 200 | 2026-11-11 |
| Live API `/health/ready` | `{"database":"ok","ollama":"disabled"}` | 2026-11-11 |
| Live API `/` | `{"project":"My Farm AI","version":"0.1.0","status":"running"}` — stale version string | 2026-11-11 |
| Release APK download | 67,884,479 B, SHA-256 `352020c5…c465`, HTTP 200 | 2026-11-11 |
| Android emulator | **not viable on this host** (no KVM/GPU path, prior attempts failed) | 2026-11-10 |
| Physical Android device | none connected (`adb devices -l` empty) | 2026-11-11 |

## 3. Feature matrix

### 3.1 Access and identity

| # | Feature | Web | Android | Backend / DB | External | Auth | Status | Evidence |
|---|---|---|---|---|---|---|---|---|
| 1 | Public landing page | `/landing` implemented | n/a | none | none | public | **PASS (live)** | HTTP 200 live; content is the pre-fix build, so MFAI-014 copy defects remain |
| 2 | Email-OTP registration | 2-stage form + password field (repo) | **none** | `POST /register/email/request-otp`, `/verify`; `users`, `contact_verification` | SMTP (unset) | public | **BLOCKED** | Live API still runs the passwordless contract (image predates `6976a3f`); `EMAIL_DELIVERY_MODE=dev` writes the code to a server-side outbox no user can read |
| 3 | Web login (email + password) | `/auth/login` | n/a | `POST /auth/login`, Argon2id | none | public | **PASS (repo) / PARTIAL (live)** | 44 web tests + backend auth tests pass; live bundle is stale |
| 4 | Web logout / session revocation | Settings → Sign out | n/a | `POST /auth/logout` (204) | none | session | **PASS** | Backend tests; `apiClient.logout()` clears cookie |
| 5 | Android login | n/a | `SignInForm` on Dashboard | `POST /auth/login` with `android: true` → bearer + refresh | none | public | **PARTIAL** | Code path verified by tests; never exercised on a device or emulator |
| 6 | Android registration | n/a | **none** | same as #2 | SMTP | public | **NOT IMPLEMENTED** | No registration screen in `android/src` |
| 7 | Session recovery / token refresh | cookie session | refresh rotation + 401 auto-refresh | `POST /auth/token/refresh`, reuse detection | none | session | **PASS (repo)** | Backend rotation/reuse tests; Android client refresh branch present, not device-tested |
| 8 | Password reset | OTP verify doubles as reset | none | `POST /register/email/verify` with new password | SMTP | public | **PARTIAL** | Works only when OTP delivery works; no dedicated "forgot password" screen |
| 9 | OAuth (Google / Microsoft) | buttons on login | none | `/oauth/{provider}/authorize`, `/callback` | Google/Microsoft | public | **BLOCKED** | Client IDs present in `backend/.env`, but no provider app is confirmed configured for the live origin; UI falls back to "not configured yet" |

### 3.2 Onboarding and profile

| # | Feature | Web | Android | Backend / DB | External | Auth | Status | Evidence |
|---|---|---|---|---|---|---|---|---|
| 10 | Onboarding wizard | `/onboarding`: contact → verification → location → land → profile → done | none | `/me/onboarding`, `/me/home-location`, `/me/farmer-profile` | browser geolocation | session | **PARTIAL** | Implemented (484 lines); not executed end-to-end on the live build; selfie step needs a camera |
| 11 | Farmer profile | Settings → Profile | none | `GET/PATCH /me/farmer-profile` | none | session | **PASS (repo)** | Backend tests; settings form wired |
| 12 | Home location | map pin + "use my location" | none | `PATCH /me/home-location` | browser geolocation | session | **PARTIAL** | Code path present; not live-verified |
| 13 | Selfie identity verification | onboarding step is text + "Check again"; **no capture UI** | none | `/verification/*`; files re-encoded, EXIF stripped, 0700 dir | none | session | **BLOCKED** | 20 backend tests pass; `grep` finds no `getUserMedia`/selfie upload caller in any client. New users are `pending_verification`, the step only completes at `active`/`verified`, and wave 1 has no approve endpoint — so onboarding can never complete (MFAI-025) |

### 3.3 Farm data

| # | Feature | Web | Android | Backend / DB | External | Auth | Status | Evidence |
|---|---|---|---|---|---|---|---|---|
| 14 | Farm management | created in onboarding; no standalone farm page | none | `GET/POST/PATCH /farms` | none | owner role | **PARTIAL** | CRUD tested in backend; no UI to edit or delete a farm after onboarding |
| 15 | Land plots / boundaries | onboarding land step | none | `/farms/{id}/plots` CRUD | none | owner role | **PARTIAL** | Backend CRUD tested; no post-onboarding plot editor |
| 16 | Crop plans | `/crops` full planner | `CropPlanningScreen` | `/farms/{id}/crop-plans`, `/crop-plans/{id}` | none | session | **PARTIAL** | Web UI wired to create/update/read; Android screen present; no device verification |
| 17 | Plan revisions | revision history panel | none | `/crop-plans/{id}/revisions` | none | session | **PASS (repo)** | Backend tests + web query |
| 18 | Plan tasks | task list with status toggle | none | `PATCH /crop-plans/{id}/tasks/{task_id}` | none | session | **PASS (repo)** | Backend tests + web mutation |

### 3.4 Core features

| # | Feature | Web | Android | Backend / DB | External | Auth | Status | Evidence |
|---|---|---|---|---|---|---|---|---|
| 19 | AI assistant chat (web) | `/assistant` → `useChat` → `POST /chat` | n/a | chat router, quota 20/day · 10/hour | Ollama | session | **BLOCKED (live)** | Live readiness reports `"ollama":"disabled"`; every live chat request will return 503. Local stack with `qwen3:4b` passes the suite |
| 20 | AI assistant chat (Android) | n/a | `ChatInterface` | same | Ollama | session | **BLOCKED (live)** | Same backend dependency; no device test |
| 21 | Conversation history (server) | session-scoped, cleared on tab close | n/a | `/conversations`, `/conversations/{id}` | none | session | **PASS (repo)** | Backend tests; `useChat` passes `conversationId` |
| 22 | Conversation history (Android local) | n/a | `SecureStore`-backed | none | none | none | **PASS (repo)** | Unit tests on storage helpers |
| 23 | Weather | `/weather` | `WeatherCard` | `/weather`, `/weather/current` | Open-Meteo (non-commercial tier) | session | **PARTIAL** | Backend tests with mocked provider; live outbound call from Catalyst unverified; no staleness banner verified on live |
| 24 | Knowledge library / resources | `/knowledge` | `ResourcesList` | `/resources`, `/resources/categories` | none (DB-backed) | session | **PASS (repo)** | Backend tests; UI wired to the catalogue |
| 25 | Research + citations | no dedicated page; assistant uses it | none | `GET /research` (SearXNG, SSRF-safe) | SearXNG | session | **BLOCKED (live)** | No SearXNG instance is known to be deployed with the live API; provider failure maps to 503 `RESEARCH_UNAVAILABLE` |
| 26 | Vision / crop image analysis | **no UI** | **no UI** | `POST /vision/analyze` works (qwen3-vl:2b, 5 MiB, magic-byte check, in-memory) | Ollama vision model | session | **NOT IMPLEMENTED (client)** | Backend endpoint tested; `grep` finds no web or Android caller. `/pest-disease` copy claiming the endpoint does not exist is **inaccurate** (finding MFAI-023) |
| 27 | Voice input (web) | `QuestionComposer` uses browser `SpeechRecognition` | n/a | none | browser API | session | **PARTIAL** | Code present + unit test; browser support varies; not verified on live |
| 28 | Voice input / output (Android) | n/a | `useSpeechRecognition`, `useSpeechSynthesis` | `/voice/capabilities` | device TTS/STT | session | **PARTIAL** | Hooks present; requires a device with a speech engine; never device-tested |

### 3.5 Account, support and distribution

| # | Feature | Web | Android | Backend / DB | External | Auth | Status | Evidence |
|---|---|---|---|---|---|---|---|---|
| 29 | Settings | `/settings`: profile, account, appearance, notifications | **none** | `/me`, `/me/preferences` | none | session | **PASS (repo)** | 305-line page; backend tests |
| 30 | Notifications | honest "not connected" panel | none | **none** | none | n/a | **NOT IMPLEMENTED** | UI states this explicitly — accurate |
| 31 | Feedback submission | **no UI** | **no UI** | `POST /feedback/submit` works | none | optional | **NOT IMPLEMENTED (client)** | Endpoint tested; `grep` finds no caller on either client |
| 32 | Help / support page | none | none | none | none | n/a | **NOT IMPLEMENTED** | No route |
| 33 | Privacy policy | `/legal/privacy` | none | none | none | public | **PARTIAL** | Page exists; text describes data collection but is not owner-approved |
| 34 | Terms of service | `/legal/terms` | none | none | none | public | **PARTIAL** | Page exists; not owner-approved |
| 35 | Data export | none | none | none | none | n/a | **NOT IMPLEMENTED** | No endpoint |
| 36 | Account deletion | none | none | none | none | n/a | **NOT IMPLEMENTED** | No endpoint |
| 37 | In-app update check | none | **no UI** | `GET /app-updates/latest` live, returns 1.0.0 / min 0.9.0 | GitHub Releases | public | **NOT IMPLEMENTED (client)** | Endpoint verified live; Android has no Settings/About screen, contradicting the v1.0.0 release notes (finding MFAI-023) |
| 38 | Public APK download | n/a | n/a | `GET /downloads/app-release.apk` (GET only; HEAD → 405) | GitHub Releases | public | **PASS** | GitHub asset 67,884,479 B, SHA-256 `352020c5…c465`, anonymous HTTP 200 |
| 39 | Community | `/community` "Unavailable" placeholder | none | none | none | session | **MOCKED** | Honest placeholder — correctly not advertised |
| 40 | Pest & disease | `/pest-disease` "Unavailable" placeholder | none | vision endpoint exists | none | session | **MOCKED** | Placeholder is honest about the missing UI but wrong about the backend (MFAI-023) |

## 4. Summary

| Status | Count |
|---|---|
| PASS | 8 |
| PARTIAL | 12 |
| BLOCKED | 6 |
| NOT IMPLEMENTED (client) | 4 |
| NOT IMPLEMENTED | 4 |
| MOCKED | 2 |
| NOT TESTED | 0 |
| **Total** | **40** |

### Advertised-in-v1.0.0 core features

The v1.0.0 release notes advertise: registration, AI chat, weather, research with
citations, crop plans, dashboard, feedback, update check, APK download.

| Advertised feature | Honest status |
|---|---|
| Registration | **BLOCKED** live (dev-mode OTP; live image lacks the password fix) |
| AI chat | **BLOCKED** live (`ollama: disabled`) |
| Research + citations | **BLOCKED** live (no SearXNG) |
| Feedback | **NOT IMPLEMENTED** in any client |
| Update check | **NOT IMPLEMENTED** in any client |
| Weather | PARTIAL (unverified live outbound) |
| Crop plans | PARTIAL (repo-verified, not device/live-verified) |
| APK download | PASS |

**Conclusion:** v1.0.0 does not meet the "all advertised core features PASS" bar. See
`docs/testing/FINAL_RELEASE_TEST_RESULTS.md` for the gate table.

## 5. Discrepancies found while building this matrix

| ID | Finding | Severity | Action |
|---|---|---|---|
| MFAI-022 | OTP registration left an unknown random password; every login path is password-based; no reset endpoint. Self-registered users were permanently locked out, and could never sign in on Android. | Critical | **Fixed** in `6976a3f` (verify step now requires a password). Not yet deployed. |
| MFAI-023 | `/pest-disease` claims no image-analysis endpoint exists, but `POST /vision/analyze` is implemented and tested. Separately, the v1.0.0 release notes describe an in-app update check and a Settings → About screen that do not exist in the Android app. | Medium | Documentation corrected 2026-11-11; vision UI remains unimplemented |
| MFAI-024 | `web/src/components/Chat/ChatInterface.tsx.bak` is a stray backup file in the source tree. | Low | Remove before v1.0.1 |
| MFAI-025 | Onboarding cannot be completed by any self-registered user. New signups get `verification_status=pending_verification`; `ProfileService.ONBOARDING_STEPS` only marks `verification` complete at `active`/`verified`; the web step renders text and a "Check again" button that points at a verification screen which does not exist; the admin queue has no approve endpoint. The selfie backend is complete but unreachable from any client. | **Critical** | Documented; needs an owner decision (add a selfie capture UI, or make the step optional, or add an admin approval path). Not changed unilaterally — it is a security gate. |

## 6. Release impact

No feature in this matrix should be described as "working" in public communication unless
its status is **PASS**. The safe public claim for v1.0.0 is limited to: the landing page,
the Android APK download, and the checksum. Everything that requires an account is
**BLOCKED** on the live deployment.
