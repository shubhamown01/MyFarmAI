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
- Feedback FK bug: `user_id` random-uuid violates users.id consistency on Postgres — now `NULL` for anonymous feedback.
- Migration chain: feedback migration was forked (2 heads) and missing its `id` PK column; re-chained, fixed, and applied to prod (`f4b2c3d4e5a7_fb_feedback1`).

### Security
- Verified live hardening: `ENVIRONMENT=production`, pinned `ALLOWED_HOSTS`, explicit CORS, `Secure` cookie, CSRF middleware, trusted-proxy rate-limit source.
- Keystore/passwords never enter Git; backup procedure documented in `./docs/release/ANDROID_SIGNING_AND_KEY_RECOVERY.md`.

### Known limitations
- User self-registration blocked on real SMTP (dev OTP only).
- No Google Play publication (registration fee ≠ ₹0; owner approval required).

## [Unreleased]
- `phase-01-foundation` → `main` fast-forward history preserved; ongoing features merge via `develop`.
