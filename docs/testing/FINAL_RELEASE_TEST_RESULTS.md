# MyFarmAI v1.0.0 — Final Release Test Results

**Document ID:** MYFARMAI-TEST-012
**Version:** 1.0
**Date:** 2026-11-11
**Repository:** `phase-01-foundation` @ `6976a3f`
**Live web:** https://myfarmai-web-zwpytbwu.onslate.in
**Live API:** https://myfarmai-backend-50047414881.development.catalystappsail.in
**Release APK:** https://github.com/shubhamown01/MyFarmAI/releases/download/v1.0.0/app-release.apk

## 1. Release gate table (A–U)

| Gate | Criterion | Status | Evidence |
|---|---|---|---|
| **A** | Git/source recoverable | **PASS** | Git repo, branch in sync with `origin/phase-01-foundation`, 8 commits ahead of `main`, clean tree. All work pushed. |
| **B** | Feature completion matrix reviewed | **PASS** | `docs/release/V1_FEATURE_COMPLETION_MATRIX.md` — 40 features, 8 PASS / 13 PARTIAL / 5 BLOCKED / 4 NOT IMPLEMENTED (client) / 4 NOT IMPLEMENTED / 2 MOCKED |
| **C** | Frontend production build passes | **PASS** | `npm run build` — 16 routes incl. new `/download` (static, 162 B); typecheck clean; lint clean; 44 Jest tests pass |
| **D** | Backend production build/startup passes | **PASS** | 313 tests pass (94.87 s); app factory starts; live `/health/ready` → `database: ok`. Docker image **not rebuilt** this session. |
| **E** | Database persists across restart | **PASS (indirect)** | Managed Neon PostgreSQL survives AppSail redeploys; no data loss observed across the 2026-11-09/10 redeploys. No restart drill run this session. |
| **F** | Backup and restore verified | **BLOCKED** | No automated `pg_dump`; no restore drill performed. Recorded as pending in `docs/security/V1_RELEASE_SECURITY_CHECKLIST.md`. |
| **G** | Authentication and user isolation pass | **PASS (repo) / NOT TESTED (live)** | 313 backend tests incl. `test_auth_matrix`, `test_conversation_ownership`, per-resource ownership tests. New regression `test_registration_password_enables_login` covers register → logout → login. Live two-account isolation **not** exercised. |
| **H** | All advertised core features pass end-to-end | **FAIL** | Registration BLOCKED (dev-mode OTP); onboarding dead-ends at the selfie step with no client capture UI (MFAI-025); AI and research BLOCKED live (`ollama: disabled`, no SearXNG); feedback and update-check have no client UI. See matrix §4. |
| **I** | External APIs/providers verified with failure states | **PARTIAL** | Open-Meteo and SearXNG covered by mocked failure-state tests. Live outbound from AppSail unverified. SearXNG not deployed with the live API. |
| **J** | AI works end-to-end or limitations disclosed | **PARTIAL** | Works locally with `qwen3:4b` (backend suite). Disabled on the live deployment; disclosed in release notes, feature matrix and `/download`. |
| **K** | Android release build succeeds | **PASS** | Signed `app-release.apk` built 2026-11-09 via `expo prebuild` + Gradle release. Not rebuilt this session (no source change affecting Android). |
| **L** | APK signature verified | **PASS** | Fresh `apksigner verify`: **SIGNATURE VALID**. `CN=MyFarmAI Release, OU=MyFarmAI, O=MyFarmAI`; cert SHA-256 `cfa4f1d7…3bdf48`. |
| **M** | APK installs and runs in emulator | **BLOCKED** | Emulator not viable on this host; no physical device (`adb devices -l` empty). Never claimed otherwise. |
| **N** | Production API URL configured correctly | **PASS** | APK bundle (`assets/index.android.bundle`) contains exactly one backend host: `myfarmai-backend-50047414881.development.catalystappsail.in`. **Zero** occurrences of `10.0.2.2`, `localhost:8000`, or `example.com`. |
| **O** | HTTPS and DNS work | **PASS** | Both live hosts serve HTTPS 200 with valid certificates |
| **P** | Public web app independently reachable | **PASS (with caveat)** | `GET /landing` and `GET /` → 200 over the public internet from this host. Not tested from a second independent network. |
| **Q** | Public APK download independently reachable | **PASS** | Anonymous `GET` → 200, 67,884,479 B, SHA-256 `352020c5…c465`, byte-identical to the published checksum |
| **R** | Security gates pass | **PARTIAL** | No unresolved Critical/High open finding in the repo; gitleaks clean on the staged diff; dependency remediation applied (see `docs/security/DEPENDENCY_AUDIT.md`). Open: backup/restore gate, residual Starlette advisories (owner-accepted), OWASP ZAP not run. |
| **S** | Privacy/support/release notes published | **PARTIAL** | Release notes published on GitHub; `/legal/privacy` and `/legal/terms` exist but are not owner-approved; support channel is GitHub Issues; `/download` not live |
| **T** | Update and rollback procedures verified | **PARTIAL** | `GET /app-updates/latest` live (1.0.0, min 0.9.0); no client UI consumes it. Rollback documented; not drilled this session. |
| **U** | External tester workflow passes | **FAIL** | A new tester cannot self-register (no email delivery), so the workflow stops at step 3. |

### Summary

| Status | Gates |
|---|---|
| PASS | A, B, C, D, E, G(repo), K, L, N, O, P, Q — **12** |
| PARTIAL | I, J, R, S, T — **5** |
| FAIL | H, U — **2** |
| BLOCKED | F, M — **2** |
| NOT TESTED | none |

**Release verdict: NOT APPROVED for public launch.** Gates H and U fail, and F and M
are blocked. Per the release policy, v1.0.0 cannot be described as fully working.

## 2. Test results by platform

### 2.1 Backend (Python 3.12, pytest 8.3.4)

```
313 passed, 31 warnings in 94.87s
```

Covers: auth (login/logout/refresh/reuse detection/lockout/CSRF/rate limits), OTP
registration incl. the new password regression, selfie verification and admin queue,
farms/plots/crop cycles/crop plans/tasks/revisions ownership, conversations ownership,
dashboard, weather (mocked provider), research (mocked SearXNG), resources, feedback,
vision, voice capabilities, app updates, downloads, health.

### 2.2 Web (Next.js, Jest)

| Check | Result |
|---|---|
| `npm test -- --runInBand` | 44 passed / 9 suites |
| `npm run typecheck` | clean |
| `npm run lint` | no warnings or errors |
| `npm run build` | passes; `/download` emitted as static |

### 2.3 Android

| Check | Result |
|---|---|
| Release APK exists | yes — 67,884,479 B |
| Signature | valid (`apksigner verify`) |
| Bundle API host | production AppSail host, no dev URLs |
| Bundle version | 1.0.0 / versionCode 1 |
| `npm run typecheck` / `npm run lint` | **NOT RUN this session** (no Android source changed); prior results in `docs/testing/ANDROID_TEST_RESULTS.md` |
| Emulator install + launch | **BLOCKED** — emulator not viable on this host |
| Physical device | **NOT TESTED** — none connected |
| Session persistence / upgrade path | **NOT TESTED** on a device |

### 2.4 Live deployment probes (2026-11-11)

| Probe | Result |
|---|---|
| `GET /landing` | 200 |
| `GET /` | 200 |
| `GET /health/ready` | `{"status":"ok","database":"ok","ollama":"disabled"}` |
| `GET /` (API) | `{"project":"My Farm AI","version":"0.1.0","status":"running"}` — **stale version string**, confirms the live image predates the release metadata fix |
| APK asset | 200, 67,884,479 B, hash matches |

### 2.5 Artifact forensics (new this session)

| Check | Result |
|---|---|
| Downloaded public APK and hashed it | `352020c5…c465` — matches `docs/release/v1.0.0.sha256` |
| Extracted `assets/index.android.bundle` | present, 1,760,180 B |
| Backend host occurrences in bundle | 1 — the real AppSail host |
| Dev/placeholder URLs in bundle | 0 |
| `apksigner verify --print-certs` | SIGNATURE VALID, `CN=MyFarmAI Release` |

## 3. Security test status

| Tool | Scope | Result |
|---|---|---|
| gitleaks | staged diff for `6976a3f` | no leaks (one test fixture allow-listed with `# gitleaks:allow`) |
| pip-audit / osv-scanner / npm audit / Trivy | dependencies + images | remediated; see `docs/security/DEPENDENCY_AUDIT.md` |
| Semgrep | backend + web | prior run recorded in `docs/security/SECURITY_FINDINGS.md`; not re-run |
| OWASP ZAP | live web | **NOT RUN** |
| PentAGI | n/a | not used this release |

No unresolved Critical or High finding is open in the repository. Residual Medium/Low
items are listed with owner acceptance in `docs/security/V1_RELEASE_SECURITY_CHECKLIST.md`.

## 4. What an ordinary person experiences today

1. Open `https://myfarmai-web-zwpytbwu.onslate.in/landing` → **works**.
2. Click "Start testing — create an account" → asks for an email; the code is written to
   a file on the server → **stops here**.
3. Even with a working code: onboarding asks for a selfie at the `verification` step, but
   no client can capture or upload one, and there is no approval endpoint → **stops here**.
4. Download the APK → **works**, checksum verifies.
5. Install and open → sign-in screen appears, but the user has no account → **stops here**.

That is the honest end-to-end result: the distribution works, the account lifecycle does
not.

## 5. Conditions for re-running this gate table

Re-run gates C–U after:

1. The current tree is deployed to Slate and AppSail (see
   `docs/deployment/PRODUCTION_DEPLOYMENT_RUNBOOK.md`).
2. `EMAIL_DELIVERY_MODE` is switched to a working provider (owner decision).
3. A device or a working emulator is available for gates M and the Android rows.

Gate F additionally requires a Neon `pg_dump` plus a restore drill.
