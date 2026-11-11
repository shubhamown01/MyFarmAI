# Changelog

All notable changes to MyFarmAI are documented here. Format is
[Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

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

### Security
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
