# Changelog

All notable changes to MyFarmAI are documented here. Format is
[Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `docs/deployment/MYFARMAI_OWNER_READINESS_CHECKLIST.md` — owner-readiness pass
  for the next deployment stage: verified local evidence (38 backend tests, frontend
  typecheck/lint/build, production SMTP gate, masked secret scans), the four owner
  decisions D1–D4 (Catalyst readings, Neon rotation, backup custody, release
  commit), and the gate order. No production change; no blocker closed.
- `docs/architecture/MYFARMAI_CLOUD_V1_LOCK.md` — the locked `MYFARMAI-CLOUD-V1`
  architecture: fixed stack, provider responsibilities, restrictions, financial
  policy, decision history and change-control rules. Records the open AppSail
  quota conflict (B1) and resolves R2 (not adopted), production email (Brevo) and
  production AI (Ollama/Qwen local only). No infrastructure was changed.
- `docs/deployment/MYFARMAI_POST_AUDIT_STAGE_2.md` — read-only resolution of the
  AppSail quota model (GB-minutes = memory × runtime), the deployed-image
  fingerprint (`0a75e26` + pre-commit `f9c5eeb`), the 146–149 MiB memory
  baseline, the SMTP gap (adapter on HEAD, absent from the deployed image), and
  Neon/R2 backup facts. No change was executed.
- `docs/deployment/MYFARMAI_PRODUCTION_BLOCKERS.md` — 13-item blocker register
  with severity, evidence, owner action, acceptance test and a dependency-ordered
  deployment gate.
- `docs/deployment/MYFARMAI_CLOUD_PROVIDER_AUDIT.md` — read-only 2026-11-12
  re-evaluation of AWS, Google Cloud, Cloudflare, Vercel, Render, Neon and
  Catalyst against the ₹0/no-card policy, with evidence URLs, a compatibility
  matrix, and the unresolved AppSail 2048 MB quota risk.
- `docs/deployment/MYFARMAI_CLOUD_DEPLOYMENT_RUNBOOK.md` — proposed exact
  resource list, env-var names, deploy/verify/rollback/backup procedure and
  owner-action gate for the recommended Catalyst + Neon topology.
- Cloudflare R2 free tier verified (10 GB-month, 1M Class A / 10M Class B ops,
  free egress); Stage 2 found R2 requires an R2 subscription checkout, so it is
  policy-blocked until the owner approves that billing surface.

### Changed
- Provider selection documentation superseded: `CLOUD_DEPLOYMENT_PLAN.md` and
  `FREE_TIER_COMPARISON.md` remain as historical records; the new audit is the
  current decision input. No deployment, resource, DNS, billing or data change
  was made.
- Corrected the prior audit's SMTP claim: the production startup gate exists on
  `HEAD` but not in the deployed image, which still logs OTP codes and delivers
  nothing (see `MYFARMAI_POST_AUDIT_STAGE_2.md`).

## [1.0.0] — 2026-11-10 — first stable public release

Published 2026-11-10 with owner approval after all gates. Tag `v1.0.0` on `main`; official page: https://github.com/shubhamown01/MyFarmAI/releases/tag/v1.0.0

### Added
- Email-OTP authentication, opaque session cookies (Argon2id, refresh rotation, reuse detection).
- Farmer profile, farms, land plots/boundaries; crop plans with revisions.
- AI chat assistant with per-user quota counters (20/day, 10/hour); cloud-only model path.
- Weather (Open-Meteo free tier) and web research with citations (SearXNG).
- Feedback endpoint (anonymous submit + optional reply email) — `POST /api/v1/feedback/submit`, admin `GET /api/v1/feedback`.
- Public APK download route (`GET /api/v1/downloads/app-release.apk`) and official GitHub Releases distribution (post-approval).
- In-app update-check service: latest-version + severity (optional/recommended/critical) + release notes URL; never auto-installs.
- Production live endpoints: web `https://myfarmai-web-zwpytbwu.onslate.in`, backend `https://myfarmai-backend-50047414881.development.catalystappsail.in`.
- `docs/release/` — versioning policy, release process, v1.0.0 checklist/notes, Android signing & recovery, app-update system, rollback procedure, release history.
- CI workflows: PR/push lint+tests+build gates; tag-triggered release validation pipeline (docs in `.github/workflows/`).

### Changed
- Android signing: release builds now use the production signing configuration (no debug key).
- Backend metadata/${pyproject} version synced 0.1.0 → 1.0.0 (single source of truth via `VERSION`).

### Fixed
- Public root endpoint reported `version: 0.1.0` while the release is 1.0.0.
  `app_version` now defaults to the installed package metadata (pyproject single
  source of truth) with an `unknown` fallback; `.env.example` updated. Regression
  test added.
- Web home page hydration mismatch (React #418) and a false "You're offline"
  banner: `useOnlineStatus` read `navigator.onLine` during render, and Node 21+
  defines `navigator` without `onLine`, so the server rendered the offline state
  while the client rendered online. The hook now starts online and applies the
  real status after mount (3 regression tests).
- Web home page greeted every anonymous visitor with the developer's name
  (`DEFAULT_PROFILE.name = 'Shubham'`). Default is now neutral (`Farmer`).
- Web page titles: `/settings`, `/history`, `/auth/login`, and `/auth/register`
  fell back to the generic site title. Nested layouts now set "Settings",
  "Question History", "Sign in", and "Create account" (WCAG 2.4.2).
- Web mobile navigation toggle had no `aria-expanded`, so screen readers could
  not tell whether the drawer was open (WCAG 4.1.2). `TopBar` now exposes the
  drawer state; verified false → true → false.
- Feedback FK bug: `user_id` random-uuid violates users.id consistency on Postgres — now `NULL` for anonymous feedback.
- Migration chain: feedback migration was forked (2 heads) and missing its `id` PK column; re-chained, fixed, and applied to prod (`f4b2c3d4e5a7_fb_feedback1`).

### Security
- Verified live hardening: `ENVIRONMENT=production`, pinned `ALLOWED_HOSTS`, explicit CORS, `Secure` cookie, CSRF middleware, trusted-proxy rate-limit source.
- Keystore/passwords never enter Git; backup procedure documented in `./docs/release/ANDROID_SIGNING_AND_KEY_RECOVERY.md`.

### Known limitations
- User self-registration blocked on real SMTP (dev OTP only).
- No Google Play publication (registration fee ≠ ₹0; owner approval required).

## [Unreleased]

### Added
- Canonical public download page at `/download`: version, package id, file size,
  SHA-256, Android requirements, install steps, honest limitations, support and
  legal links. Static (no API call) so it survives backend outages. The landing
  page now links to it instead of the API-proxied APK path.
- Release evidence set: `V1_FEATURE_COMPLETION_MATRIX.md` (40 features),
  `FINAL_RELEASE_TEST_RESULTS.md` (gates A–U), `PUBLIC_DOWNLOAD_PAGE.md`,
  `PRODUCTION_ARCHITECTURE.md`, `PRODUCTION_DEPLOYMENT_RUNBOOK.md`,
  `PRODUCTION_SECURITY_CHECKLIST.md`.
- Administrator approval of pending registrations (MFAI-025):
  `GET /api/v1/verification/admin/pending-users` and
  `POST /api/v1/verification/admin/users/{target_user_id}/decision`. Rejects
  self-approval, non-pending transitions, and rejections without a reason; every
  decision writes a `VerificationEvent` with `method: admin_approval`. 11 tests.
- Real SMTP delivery adapter (MFAI-026): stdlib `smtplib` + `EmailMessage` on
  `asyncio.to_thread`, STARTTLS, timeout, optional auth. Production startup now
  **fails** when email delivery is not configured. 17 tests against a fake relay.
- `backend/scripts/create_admin.py` — the only supported way to create or
  recover an administrator. Password prompted, never printed or passed in argv.
- `docs/security/ADMIN_ACCOUNT_PROCEDURE.md`, `docs/deployment/SMTP_SETUP.md`,
  `docs/deployment/BACKUP_AND_RESTORE.md`, `docs/release/V1_0_0_FINAL_RELEASE_STATUS.md`.
- Web feedback form on `/settings` (`submitFeedback` → `POST /feedback/submit`).

### Security
- Dev-mode OTP delivery no longer logs the verification code when
  `ENVIRONMENT=production` (MFAI-026). Because the OTP verify step can reset a
  password, a plaintext code in exported platform logs would have allowed
  account takeover. Unknown `EMAIL_DELIVERY_MODE` values now log at error level
  instead of a warning. Two regression tests added.
- Voice service hardened (SEC-014/SEC-028): `/transcribe` now requires a bearer
  token (`VOICE_SERVICE_TOKEN`, fails closed with 503 when unset), caps uploads
  at 25 MB (413), streams to a temp file removed on every error path; container
  runs as non-root `appuser` (uid 10001) with a `/health` healthcheck. Six
  regression tests added (`ai/voice/test_main.py`). Service remains
  loopback-only and outside Compose (no consumer wired yet).
- Rate-limit client-IP resolution ignores `X-Forwarded-For` unless the socket
  peer is in `TRUSTED_PROXY_CIDRS` (default empty); covered by 8 middleware
  tests.
- SearXNG secret externalized to `SEARXNG_SECRET` (template variable); real
  value lives only in git-ignored `infra/searxng/.env`.

### Changed
- `phase-01-foundation` → `main` fast-forward history preserved; ongoing features merge via `develop`.
- Web onboarding shows honest pending, pending-review, and rejected states
  instead of pointing at a verification screen that does not exist.
- Web `Content-Security-Policy` added in `next.config.js` (`default-src 'self'`,
  `object-src 'none'`, `frame-ancestors 'none'`, OSM tiles as the only external
  image source). `script-src` keeps `'unsafe-inline'` because Next injects inline
  bootstrap scripts and a nonce cannot apply to static pages. Verified against a
  local production build: 11 routes, zero console errors.
- `/pest-disease` copy no longer denies that `POST /vision/analyze` exists; it
  now says the capability is API-only with no user-facing UI.
- Android `app.json` declares `android.versionCode: 1` explicitly.
- Removed the stray `web/src/components/Chat/ChatInterface.tsx.bak` (MFAI-024).

### Fixed
- Public email-OTP registration left the account with an unknown random
  password, and every login path is password-based. A self-registered user was
  therefore locked out after logout and could never sign in on Android, which
  has no registration screen. The verify step now requires a password
  (8–128 chars) and stores it, so the account is usable on every client
  (audit finding MFAI-022). Regression tests cover register → logout → login.
- v1.0.0 release metadata published a checksum that did not match the attached
  APK: the release body and `v1.0.0.sha256` still described the pre-publication
  RC build (`631112be…e112`, 67,884,524 B) after the version-fix rebuild
  replaced the binary (`352020c5…c465`, 67,884,479 B). The release body and
  `v1.0.0.sha256` now match the APK (confirmed by GitHub's asset digest), and
  `docs/release/` notes, history and checklist were corrected. The APK was not
  rebuilt or re-signed (audit finding MFAI-021).
- Release notes described an in-app update check and a Settings → About screen
  that the Android app does not have, and `/pest-disease` claimed no
  image-analysis endpoint existed while `POST /vision/analyze` is implemented
  and tested. Both corrected (audit finding MFAI-023). The checklist also
  quoted the pre-fix APK size and checksum; corrected to 67,884,479 B /
  `352020c5…c465`, re-verified by downloading the public asset.

### Known issues
- Nothing above is deployed. The live web build predates `/download` and the CSP;
  the live API image predates the password fix, the SMTP adapter, and the
  administrator-approval endpoints. Deployment requires the Catalyst CLI from an
  authenticated machine — it cannot be done from the development host.
- SMTP credentials are not configured, and **no real verification email has ever
  been sent**. Registration is not operational until one is received and its
  code completes the flow.
- No administrator exists in production; `create_admin.py` must be run once
  against the production database.
- Administrator approval has no web UI — it is an authenticated API only.
- No physical Android device is available, so the APK has never been run on real
  hardware. The emulator is not viable on this host.
- Backup/restore (gate F) is unverified: a procedure exists, no restore drill has
  been run. OWASP ZAP baseline has not been run.
