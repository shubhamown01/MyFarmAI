# Changelog

All notable changes to MyFarmAI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Android QA pass 1 complete (2026-11-08, commits `213fe80` + `e99fd89`)**: full android audit (Phase B) found **12 defects** including 3 Critical — the app previously could not bundle or boot (metro required an uninstalled svg-transformer; entry was expo-router with zero routes; no babel.config.js). All 3 Critical + 5 High + 2 Medium fixed: Metro/Expo config repairs, missing `babel.config.js` (also breaks jest+Metro flow stripping), Hermes-safe `makeId()` replacing `crypto.randomUUID()`, 401→refresh-rotation→single-retry in ApiClient (refresh token was stored but never used), offline conversation cache wired (restore-on-mount + persist-after-exchange + 200-msg/thread cap for SecureStore's 2 MB ceiling), chat error banner with farmer-language code mapping, chat accessibility roles/labels/48dp targets, TTS auto-speak now opt-in via header toggle. Verified: typecheck clean, lint 0/0, **jest 6/6**, `npx expo export --platform android` produces a Hermes bundle (~4.6 MB). Also verified earlier (2026-11-07): all 14 mobile client endpoints exist in the deployed staging OpenAPI — no contract drift; staging API ignores spoofed `X-Forwarded-For` (Phase 0 finding closed on staging). Blocked pending owner: on-device runtime verification (no Android SDK/adb/emulator; JDK is JRE-only; ~1.9 GiB free RAM), AND-012 location decision (hardcoded Delhi coords vs `expo-location` vs dropping the over-requested permission), EAS release build authorization. Docs: `docs/testing/ANDROID_TESTING_MASTER_PLAN.md`, `ANDROID_TEST_RESULTS.md` (defect table + evidence), `ANDROID_DEVICE_COMPATIBILITY.md`.
- **Go-live runbook drafted (2026-11-07, PROPOSED)**: `docs/deployment/GO_LIVE_RUNBOOK.md` — owner decisions D1–D4 (public exposure, domain, dashboard hosting, non-commercial confirmation), exact go-live env vars (`ENVIRONMENT=production`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`; production validation refuses boot without them), honest open item on `TRUSTED_PROXY_CIDRS` (staging spoof-proof because it's empty; setting it wrong re-opens the Phase 0 bypass), 7-step verification protocol, rollback procedure.
- **Neon Postgres wired to AppSail staging — VERIFIED 200 (2026-11-06, Phase 9 milestone COMPLETE)**: two root causes fixed en route. (1) SQLAlchemy's asyncpg dialect passes URL query params as `connect()` kwargs, so Neon's `?sslmode=require&channel_binding=require` suffix raised `TypeError: connect() got an unexpected keyword argument 'sslmode'`; raw asyncpg tolerates it, SQLAlchemy does not — fix: clean URL without query params (asyncpg negotiates TLS automatically). (2) `Settings.apply_profile_defaults()` silently rewrote the explicitly-set empty `OLLAMA_BASE_URL=""` back to the profile default `http://localhost:11434`, defeating the disabled-Ollama readiness path — fix: skip keys present in `model_fields_set` (explicit env values always win, even empty). All 7 migrations applied to Neon (28 tables, `alembic_version` = `c8d9e0f1a2b3`). Final state on AppSail: `/health/live` = 200, `/health/ready` = **200** `{"status":"ok","dependencies":{"database":"ok","ollama":"disabled"}}`. Execution memory scaled 2048→256 MB (free-tier burn ~4 GB/h → ~0.25 GB/h), re-verified healthy at 256 MB; endpoint smoke test green (`/api/v1/health` 200, `/docs` 200, OpenAPI 3.1.0 / 52 paths). Files touched (uncommitted, owner review pending): `backend/app/factory.py` (readiness Ollama-disabled path + earlier init_db_manager fix), `backend/app/core/config.py` (profile-defaults fix), `backend/Dockerfile` (chown fix, image 560→402 MB), `backend/tests/test_health.py` + `backend/tests/test_config_profiles.py` (3 new tests). Full suite **289 passed**. Details: `ACCOUNT_SETUP_LOG.md` 2026-11-06 entry.
- **Chunked-body 413 through AppSail proxy fixed (2026-11-06, security-reviewed)**: AppSail's edge proxy rewrites every POST to chunked, tripping the `RequestBodyLimitMiddleware` blanket rejection (2026-10-29 exit-gate) — all staging write endpoints returned 413. Superseded by stream-enforced cap with early abort (memory bounded), malformed-CL 400 guard; @security-engineer verdict PASS-with-fixes, both fixes applied, no-bypass guarantee confirmed for all framings. Tests: chunked-within-limit reaches route+auth (401), chunked-oversized → 413; **full suite 290 passed**. Files: `backend/app/factory.py`, `backend/tests/test_security_middleware.py`, `docs/engineering/AUTHZ_MATRIX.md`. **Deploy #11 succeeded; staging verification PASSED** — `POST /api/v1/chat` → 401 `NOT_AUTHENTICATED` (was 413), `/health/ready` stays 200.
- **Backend staging LIVE on Zoho Catalyst AppSail (2026-11-04, Phase 9 milestone)**: `myfarmai-backend` deployed as custom runtime via CLI docker-archive Path B; staging URL `https://myfarmai-backend-50047414881.development.catalystappsail.in` — `/health/live` **200** `{"status":"ok","service":"backend"}`, `/` 200, `/health/ready` 503 (expected: no `DATABASE_URL` until Neon wiring). Deploy pipeline proven by size bisection (127 MB tar failed ×3 with socket errors; 93 MB passed with a 25-min window). Throwaway `smoke-test`/`smoke-test-2` AppSails deleted via console (cost guard). Details: `ACCOUNT_SETUP_LOG.md` 2026-11-04 AppSail entry.
- **Two real bug fixes en route to staging (uncommitted, owner review pending)**: (1) `backend/app/factory.py` — `create_app()` passed the raw `database_path` (`data/app.db`) into `init_db_manager(database_url=...)`, bypassing the `sqlite+aiosqlite:///` prefixing in `db/session.py`; bare-container starts (AppSail) crashed at import with `Could not parse SQLAlchemy URL from string 'data/app.db'`. Fixed to call `init_db_manager(async_mode=not is_test)` with no URL argument; verified bare `docker run` boots, `/health/live` 200. (2) `backend/Dockerfile` — blanket `chown -R appuser:appuser /app` duplicated the whole venv into a 122 MB layer (confirmed via `docker history`); replaced with chown of `/app/data` only → image 560→402 MB, archive 127→93 MB.
- **§10 cloud-AI per-user quota implemented (MF-C-Q01, directive pre-public-exposure gate)**: server-side atomic counter — `ai_quota_counters` table (migration `c8d9e0f1a2b3`), `services/ai_quota.py` single-statement `INSERT ... ON CONFLICT ... WHERE used_count < limit` (no race, PG + SQLite), `/api/v1/chat` wiring before generation (429 `AI_QUOTA_EXCEEDED` on denial, fail-closed 503 `AI_QUOTA_UNAVAILABLE`), flags `cloud_ai_enabled` (**default False — zero change for the local-Ollama path**), `cloud_ai_quota_limit=20`, `cloud_ai_quota_window_hours=10`. Intent-vs-success limitation disclosed (decrement-on-failure lands with the cloud provider). Coverage: `tests/test_ai_quota.py` **14/14 pass**, `test_chat.py` **13/13 pass** (2026-11-04). Details: `CLOUD_COST_AND_QUOTA_POLICY.md` §4.1.
- **Admin AI-quota usage view added** (`GET /api/v1/admin/ai-quota`, §4 "admin-visible usage dashboard" at API level): admin-role-gated endpoint returning per-user `used`/`remaining`/`limit` for the current window plus window metadata; service query `ausage_rows()`. Also fixed a real bug caught by the new tests: `aconsume_slot()` did not await `session.connection()` before reading the dialect (`'coroutine' object has no attribute 'dialect'`) — would have failed every async quota check. UI dashboard deferred to pre-launch.
- **Open-Meteo CC-BY 4.0 attribution shipped in the web UI** (condition of license decision D-1, owner-approved): linked "Weather data by Open-Meteo (CC-BY 4.0)" note now renders in both weather surfaces — the dashboard Farm Intelligence weather card and the 7-day WeatherCard. Verification: `npm run typecheck`, `npm test` (40/40), `npm run lint`, `npm run build` all green. Evidence recorded in `LICENSING_DECISIONS.md` D-1 + `PRODUCTION_SECURITY_CHECKLIST.md`.
- **Licensing decision records for the two Phase-0 legal gates** (`docs/deployment/LICENSING_DECISIONS.md`, **owner-approved 2026-11-03 — both gates CLOSED-conditional**): D-1 Open-Meteo free tier confirmed non-commercial-only (official terms: private/non-profit apps WITHOUT subscriptions/ads qualify; tip jars allowed; 10k calls/day CC-BY 4.0; paid plan required on monetization) with attribution-note condition; D-2 SearXNG AGPL-3.0 workable conditions (internal-only exposure; network-§13 source link duty recorded if ever public). Also verified the "hardcoded SearXNG secret" Phase-0 finding was **already remediated** (commit `97f913e` — settings.yml now reads `${SEARXNG_SECRET}` env), reflected in `PRODUCTION_SECURITY_CHECKLIST.md`.
- **Neon agent-skills installed globally for OpenCode** (`npx neon skills -y --global --agent opencode`): 7 skills live at `~/.agents/skills/neon*` (neon, neon-postgres, neon-auth, neon-functions, neon-object-storage, neon-realtime, neon-ai-gateway) — future Neon work (empty-project dry run, migrations, branch workflows) gets first-party guidance. Tooling setup only; no repo code touched. Note: Neon Functions are Node.js-only — the FastAPI backend's host stays Zoho AppSail (Python/OCI) as researched.
- **Zoho Catalyst agent-skills + MCP server installed** (2026-11-04, tooling setup for Phase 9 deployment staging): 19 Catalyst skills copied to `.agents/skills/catalyst-*` (untracked vendor content — appsail, functions, datastore, slate, stratus, pricing, etc.) via `npx skills add catalystbyzoho/agent-skills`; MCP server `catalyst` added to `opencode.json` (`https://catalyst.zohomcp.in/mcp/message`, remote http). `CatalystbyZoho_*` MCP tools become available after an OpenCode config reload and will manage Catalyst infrastructure (tables, buckets, cache) conversationally — reducing console-automation need. No app code touched.
- **Zoho Catalyst CLI authenticated + AppSail staging deploy started** (2026-11-04): `npx -y zcatalyst-cli login --dc in -ni` → logged in as `sb95146@gmail.com` (OAuth consent completed in the owner's browser session — disclosed in `ACCOUNT_SETUP_LOG.md`); `deploy/catalyst-staging/` linked to Project-Rainfall (`90779000000015001`) via non-interactive init. `myfarmai-backend:latest` (amd64, 560 MB → 127 MB docker-archive) deploying as AppSail `myfarmai-backend` on port 8000 (skill Path B, no registry). Known limitation: no DATABASE_URL on AppSail until Neon wiring — health check passes, DB endpoints 503.
- **Deployment documentation set completed (9 docs in `docs/deployment/`)**: `SECURE_CREDENTIAL_MANAGEMENT.md` (credential storage rules + Phase-B GPG backup plan), `LOCAL_FIRST_AI_ARCHITECTURE.md` (offline ladder, Qwen/Ollama local stack), `DATA_SYNCHRONIZATION_POLICY.md` (data-class authority, conflict rules, outbox retention — sync itself is PROPOSED, not implemented), and `PRODUCTION_SECURITY_CHECKLIST.md` (binding gate from Phase 0 findings: auth, voice-service containment, XFF-proof rate limiting, selfie retention, AGPL/Open-Meteo legal gates). `CLOUD_DEPLOYMENT_PLAN.md` + `CLOUD_COST_AND_QUOTA_POLICY.md` remain PROPOSED pending owner approvals.
- **Cloudflare account created (Priority 1 of the zero-cost deployment directive)**: signed up via Google SSO (owner-approved; sb95146@gmail.com only, no duplicates, no card, no billing). Account ID `5b769d9f3898d979c35200c5c22fc897`; no terms screen appeared on the SSO path (disclosed in `docs/deployment/ACCOUNT_SETUP_LOG.md`). Free quotas verified from official Cloudflare limits docs and recorded in `docs/deployment/FREE_TIER_COMPARISON.md`: Pages 500 builds/mo + 100 projects; Workers 100k req/day + 10 ms CPU/request; **no Python in Workers** (frontend-only fit).
- **Zoho Catalyst eligibility research (backend-host crux resolved)**: official docs deep-fetched (AppSail, deployment-and-billing, free-tier pages). Verified: AppSail supports Python (managed Flask/Django runtimes + custom OCI images → existing FastAPI Docker image deploys as custom runtime); free tier = 900 GB-minutes AppSail (~60h/mo at 256 MB — insufficient for 24/7), Web Client Hosting 300k req free, no card for signup; the $250 credit path requires a payment method (BLOCKED by ₹0 policy); the student program is the only ₹0 route to a continuous backend — owner performs identity verification personally. Recorded in `FREE_TIER_COMPARISON.md`, `CLOUD_DEPLOYMENT_PLAN.md` (backend row updated), and `ACCOUNT_SETUP_LOG.md`.
- **Neon account created (Priority 3 of the zero-cost deployment directive)**: Google SSO (owner-approved; sb95146@gmail.com; no card, no billing; no verification screen — the signup page's ToS notice constitutes agreement, disclosed in the setup log). Console org id `org-fragrant-cell-14431918`; **no project/database created** — explicitly excluded from this approval, an empty-project dry run needs separate sign-off. Onboarding wizard untouched.
- **Backup & deploy runner scripts complete the §13 set (6/6)**: `BACKUP_MYFARMAI.sh` dumps the Compose PostgreSQL database (password never echoed, `.env` files deliberately excluded) plus a repo-state snapshot to `/data/MyFarmAI-backups/<timestamp>/`, retention keeps the newest 10, and `--verify` loads the dump into a throwaway postgres container to prove restorability. Evidence: dump written (EXIT 0 ×2) and 27 public tables restored into the throwaway container, prod untouched. `DEPLOY_MYFARMAI.sh` rebuilds the local stack with preflight, migrations and health gates, and hard-refuses `--public` (phase E6 gate — requires owner approval + configured host + security review). Evidence: full local run EXIT 0 (postgres healthy, backend ready, frontend responding, AI bridge OK). Documented in `docs/runner-guide.md`.
- **Free-tier provider comparison** (`docs/deployment/FREE_TIER_COMPARISON.md`): facts fetched from official pricing pages 2026-11-03 (Neon, Supabase, Prisma Postgres, Koyeb, Netlify, Vercel, HF Spaces, Zoho Catalyst). Highlights: Neon free = no card, no inactivity pause, 100 projects; Supabase = 1-week inactivity pause, 2-project cap; Vercel Hobby = personal/non-commercial clause; Koyeb = paid-only → BLOCKED (₹0 policy).

### Fixed
- **Voice service contained to loopback (Phase 0 finding S-03, owner-approved)**: `ai/voice/Dockerfile` CMD now binds `127.0.0.1:8001` instead of `0.0.0.0:8001` — a containerized voice service can no longer be reached from the LAN or public interface. Verified the service is currently not running (port 8001 not listening; not in compose), so this is preventive containment before any wiring. Auth/upload-limit remediation (S-03 full) remains the blocker for ever exposing or integrating it — documented in `docs/PERSONAPLEX_BOUNDARY.md`.
- **Email OTP dev delivery (blocker B2 evidence trail)**: the dev adapter silently dropped the OTP when its outbox directory was missing (fail-open) and again when the compose-provided string path was not a `Path` (500). The outbox now always writes to `backend/data/dev_otp_outbox.txt` on the host, with a regression test exercising the real `send_otp` (8/8 OTP tests pass).
- **Dev session cookies dropped**: `web/.env.local` used an absolute `http://localhost:8000` API URL (cross-origin from :3000), so the browser discarded the `SameSite=Lax` session cookie and `/onboarding` bounced to login. Dev now uses the relative `/api/v1` (same-origin proxy); `next.config.js` reads a server-only `MYFARMAI_API_ORIGIN` so the proxy target can no longer be broken by the client value.

### Added
- **Resend OTP button** on the register verify stage with a live 60 s cooldown countdown matching the backend, plus a "Use a different email" escape.
- **Honest dev-mode hint** on the register page — clearly states no real email is sent and where the code is written.
- **`delivery_mode` field** (additive) on `POST /auth/register/email/request-otp` responses so clients can distinguish dev outbox delivery from a real provider.
- **One-command runner docs**: `docs/runner-guide.md` troubleshooting entries for OTP delivery, send errors/cooldowns, and dev session-cookie behavior.
- **OAuth provider ramp (blocker B1)**: `docs/setup-guide.md` gains the owner steps to enable the already-implemented Google/Microsoft sign-in (client registration, redirect URIs, env vars). API docs document both OAuth endpoints and error codes. Current behavior verified live: unconfigured providers return `503 OAUTH_NOT_CONFIGURED` and the login buttons show an honest fallback message (backend OAuth tests 15/15, incl. mock-IdP JWKS signature verification).

### Verified (2026-11-03, real browser E2E — Google sign-in live)
- **Google sign-in now works end-to-end**: project `myfarmai-513615` + OAuth client + redirect URIs + test user created via the browser (with owner approvals for each ToS); credentials stored git-ignored in `backend/.env` (compose `env_file` added). Consent → real code → JWKS-verified id_token → session → `/onboarding` waiting-state; provider row `google` linked to the E1-registered account.
- **Claim-rule fix**: E1 OTP-verified users (`is_active=True`, `verification_status="pending_verification"`, backend-generated password) are now CLAIMED by OAuth provider sign-in (email control proven by the provider) instead of wrongly refused as "taken"; only users with full lifecycle status (`active`/`rejected`) are refused with `OAUTH_EMAIL_TAKEN`. Regression test added — OAuth suite 16/16, backend 272/272.
- Microsoft sign-in: backend plumbing ready and verified by tests; the Entra app registration (redirect URI `http://localhost:3000/auth/callback?provider=microsoft`) remains an owner action under blocker B1 — the button shows the honest fallback message until then.


### Verified (2026-11-03, real browser E2E)
- Full flow: register → request OTP → outbox code → verify → session cookie set → `/onboarding` waiting-state renders (pending_verification gate holds; no farm forms shown). Screenshots in `.playwright-mcp/`.

### Added
- One-command runner suite (owner directive §2026-11-03): `RUN_MYFARMAI.sh` (preflight → postgres → migrations → backend → web → integration + real AI inference smoke test → summary; modes local/development/public-demo/production — public modes refuse until E6 owner gates are met), `STOP_MYFARMAI.sh` (project-only stop, `down -v` never used, postgres_data preserved), `RESTART_MYFARMAI.sh`, `STATUS_MYFARMAI.sh` (read-only dashboard), shared `scripts/lib/myfarmai-common.sh`; `scripts/ollama-bridge.sh` fixed to bind the docker0 gateway (was stale network name); docker-compose backend now loopback-published on `127.0.0.1:8000` and reaches host Ollama via stable `host.docker.internal` (was hardcoded, stale bridge IP); `.vscode/tasks.json` + settings/extensions (11 tasks incl. logs and tests); `docs/runner-guide.md`; README/setup-guide quick-start updated. Web E4/E5 onboarding completed: auth pages (`/auth/login` incl. OAuth buttons, `/auth/register` email-OTP, `/auth/callback`), `/onboarding` wizard (location geolocation/map-pin, Leaflet polygon land registration with server-verified area + disclaimer, manual area entry, farmer profile), `FarmMap` component (react-leaflet@4 + OSM), 5 new unit tests; web gate green: typecheck/40 tests/lint/build
- E5 farmer profile + onboarding (FCL-095): migration `a5b6c7d8e9f0` — `farmer_profiles` (one per user; progressive optional fields per directive §8; farming_type/experience CHECK-constrained; cycle-verified on Compose postgres). `ProfileService` with upsert (`profile_completed` computed in code, never client-supplied) and a **computed onboarding state machine** — no separate state table; state derived from user/verification/home-location/farm-plot/profile records so it cannot drift. Endpoints: `GET /api/v1/me/onboarding` (auth-gate only — pending users can check their own progress, directive §12), `GET/PUT /api/v1/me/farmer-profile` (require_verified_user). 7 tests; gate 270 passed / mypy 111 (0 in E4/E5 files) / EXIT=0
- E4 land registration backend (FCL-094): migration `f4b2c3d4e5a6` — `home_locations` (one per user, never assumes farmer lives on farm), `farm_plots` (CHECK-constrained land types), `farm_boundaries` (lat/lon JSON, NO PostGIS per owner approval), `farm_area_measurements` (append-only history; cycle-verified on Compose postgres). `LandService` + 10 endpoints: plot CRUD under `/api/v1/farms/{farm_id}/plots`, `PUT .../plots/{id}/boundary` (server-side geodesic area via spherical-excess formula — client area never trusted; self-intersection/degenerate/bbox validation → 422 INVALID_POLYGON), `POST .../plots/{id}/area` (manual entry stored `user_reported`, optional farmer confirmation), `GET/PUT /api/v1/me/home-location`. `require_verified_user` (E3 gate) wired to all land endpoints (403 USER_NOT_VERIFIED). Map-measured vs user-reported never conflated. Exact unit constants: hectare=10,000 m², acre=4,046.8564224 m². Fixed `AuditRepository.log` signature (actor_id/subject_id are UUID). 13 tests; gate 263 passed / mypy 111 (122→111; 0 in E4 files) / EXIT=0
- Phase 3 authentication foundation (P3-01..P3-08): Argon2id password hashing (`app/core/security.py`, m=131072 t=3 p=4, ~114 ms verify); opaque session IDs / refresh tokens stored as SHA-256 hashes only; `AuthService` (login with audit, session validate with expiry+revocation+idle-timeout, logout, single-use refresh rotation with reuse detection that revokes the chain and all user sessions); `POST /auth/login` (web: HttpOnly/SameSite=Lax cookie; Android: bearer access + refresh tokens), `POST /auth/logout`, `GET /auth/me`, `POST /auth/token/refresh`, `POST /auth/admin/users` (admin-only account creation, no public registration per ADR-008 MVP policy)
- Ownership predicates (P3-05): all `ConversationRepository` single-record methods require `user_id` and filter in SQL (deny-by-default, cross-user = 404)
- Chat auth-gating (P3-09): `POST /api/v1/chat` requires authentication (401 otherwise); conversations attributed to the authenticated user instead of the legacy UUID; `get_current_user_id` principal dependency (cookie + bearer paths)
- Resource bounds (P3-12): rate-limit counters are bounded against memory exhaustion (stale-bucket eviction over 10k tracked IPs); new `ai_max_concurrent_requests` setting (default 2) caps in-flight AI requests via semaphore in the async chat path
- Security middleware (P3-10/P3-11): trusted-proxy-aware client IP (`app/core/client_ip.py` — spoofed `X-Forwarded-For` no longer bypasses rate limits); CSRF/Origin enforcement for cookie-authenticated state changes (mismatched Origin/Referer → 403); stricter per-IP limit on auth endpoints (10 req/min); per-account failed-login lockout (5 failures / 15 min → 429)
- Auth tests: 9 security-primitive + 17 service + 16 API + 6 ownership-predicate + 6 middleware + 2 auth-matrix/async-regression integration tests
- CRITICAL repo fix: .gitignore's over-broad models/ patterns had silently excluded the ENTIRE backend/app/db/models source package (fresh clones could not build) — patterns scoped to weight paths; ORM layer now tracked
- E3 wave 2 admin manual review (FCL-093): admin-only review queue + approve/reject (decision final, raw selfie deleted immediately — kept only until decision or 30-day retention purge), audited admin-only raw streaming; retention purge runs with queue listing (scheduled job deferred to ops); fixed purge visibility under autoflush=False + widened argon2 timing-test jitter band (code unchanged); gate 250 passed / EXIT=0
- E3 wave 1 selfie verification (FCL-092): consent → randomized 2-action liveness challenge (single-use, session-bound, 300s, rate-capped) → upload with magic-byte/size/dimension validation, Pillow re-encode stripping all EXIF/GPS, 0700/0600 storage outside web roots — NEVER any URL/path in responses, NO auto-approval (manual-review queue = wave 2); E1/E2 signups now enter pending_verification (directive §4.2: selfie mandatory for all methods); new tables migration cycle-verified on isolated postgres; pillow classified; gate 243 passed / EXIT=0
- E2 OAuth login/signup (FCL-091): Google + Microsoft OIDC authorization-code adapters — id_token signature (JWKS)/audience/issuer/nonce verification, account-linking protection (409 for active accounts, never silently merged; pending users claimed), in-memory single-use state store; mocked-IdP tests with real in-test RSA keypair (zero network); pyjwt+cryptography classified (MIT/Apache-2.0); providers 503-unconfigured until owner creates OAuth apps; gate 231 passed / EXIT=0
- E1 passwordless email-OTP registration (FCL-090): public signup via email one-time codes — pending-user model, argon2-hashed 6-digit codes (10-min expiry, 5 attempts persisted, 60s resend cooldown → 429), dev-mode delivery adapter (codes logged, clearly marked not delivered), new identity tables (migration b3f2a5d1c7e4, cycle-verified on isolated postgres); gate 216 passed / mypy 71 ≤ 85 / EXIT=0
- Readiness sprint 3 (FCL-089): full verification sweep (backend 209/mypy-71, web 35/35+build, android clean) + production-readiness report — verdict READY WITH CONDITIONS (owner actions: domain/TLS, device+e2e QA, LICENSE, ADR-015/016, rotation authorization)
- Readiness sprint 2 (FCL-088): fixed malformed stored argon2 hash returning 500 — now a clean 401 invalid-credentials (queued bug from Phase 6 backlog)
- Readiness sprint 1 (FCL-087): mypy threshold gate in check.sh (baseline 85, was silently suppressed) — errors driven 99 → 71, zero in 7B files; fixed a real schema-type bug in the crop-plans response
- Phase 7B COMPLETE (FCL-086): independent QA verdict CONFIRMED WITH EXCEPTIONS — all areas verified with re-executed evidence (gate 209 passed, migration cycle re-run on isolated postgres, web 35/35, zero dependency changes); exceptions: android device QA untested, mypy non-blocking gate weakness (99 suppressed errors)
- Phase 7B-5 (FCL-085): crop planning documented in API.md (endpoint contract + farmer-protection semantics) and APP_FLOW.md (§3b planning flow)
- Phase 7B-4 (FCL-084): Android crop-planning screen (same endpoints as web — flow parity); typecheck/lint clean; device QA still pending
- Phase 7B-3 (FCL-083): web crop-planning UI on the Crops page — create/manage plans, milestones with verbatim assumptions, soft-cancel tasks, revision history; 35/35 web tests, typecheck/lint/build clean
- Phase 7B-2 (FCL-082): crop-plan API live — /api/v1/farms/{farm_id}/crop-plans + /api/v1/crop-plans/{id} (tasks, revisions); milestones from planting_date + growing-day ranges with displayed assumptions; farmer tasks never system-modified; 9 new tests, gate 209 passed
- Phase 7B-1 (FCL-081): crop-plan models + Alembic migration (owner-approved schema) — migration cycle verified clean on an isolated Postgres instance
- Phase 7B opened (FCL-080): crop-planning plan issued; owner APPROVED the first Alembic migration (crop_plans, crop_plan_tasks, crop_plan_revisions — farmer-controlled plans with change history; milestones from existing growing-day ranges only)
- Phase 7A COMPLETE (FCL-079): independent QA verdict CONFIRMED WITH EXCEPTIONS — all 20 claims reproduced (backend 200-passed gate, web 25/25, android typecheck/lint, no dependency changes); exceptions: android device QA not tested, mypy non-blocking gate weakness
- Phase 7A-4 (FCL-078): Android farm-intelligence dashboard consuming the same /dashboard endpoint (first Android auth wiring: SecureStore bearer tokens + inline sign-in); typecheck/lint clean — device QA still pending
- Phase 7A-3 (FCL-077): dashboard documented in API.md (endpoint contract) and APP_FLOW.md (§3a dashboard flow with degradation semantics)
- Phase 7A-2 (FCL-076): web farm-intelligence dashboard — live blocks from the new /dashboard endpoint with loading/empty/error/offline states, explicit unavailable reasons and last-updated timestamps; 25/25 web tests, typecheck/lint/build clean
- Phase 7A-1 (FCL-075): new auth-gated GET /api/v1/dashboard aggregation endpoint (farm/crops/weather/tasks/alerts/recommendations/activity) with per-block availability + fail-open weather; 5 new tests — gate 200 passed
- Owner ACCEPTED Phase 6 (2026-11-01); Phase 7 opened with the 7A farm-intelligence-dashboard implementation plan (single auth-gated aggregation endpoint on existing services; no new tables, no invented metrics)
- Report 1 re-issued (FCL-073): Phase 6 verdict READY FOR OWNER RELEASE APPROVAL — full testing battery evidence, 0 unresolved findings, named deployment-track blockers
- Zero-cost & open-source policy applied (FCL-072): docs/engineering/DEPENDENCY_POLICY.md classifies every external service and code stack (no paid dependencies; Open-Meteo fail-open verified; SearXNG AGPL posture documented)
- Request-ID now rendered in log lines (FCL-071): formatter fix in factory.py — IDs previously echoed in responses but dropped from logs; graceful-shutdown smoke verified (SIGTERM -> clean exit, port released)
- Fixed live chat regression (FCL-070): async endpoint path crashed with UnboundLocalError on farm-less messages (unreachable by pytest's test-mode routing); 500 handler now logs unexpected errors; live chat verified 3x 200 on qwen3:0.6b
- Phase 6 final testing opened: baseline inspection report, timed DR exercise (backup 1s -> restore 7s -> app boots on restored DB -> login 200), QA-caught auth gap on /resources/categories + /resources/{category} closed — gate 195 passed
- Owner decisions executed (FCL-068): /weather + /resources now require authentication (6C M1 closed, 2 new 401 tests); nightly pg_dump backup ACTIVE (cron 02:00, owner-approved, integrity-checked runs verified)
- Report 2 (Phase 6 Production Readiness) issued: verdict PARTIAL — repo-ready, deployment track awaits owner decisions (hosting, domain, backup schedule, M1) — docs/backend/PHASE_6_PRODUCTION_READINESS_REPORT.md
- Phase 6D/6L pre-work: backup.sh (pg_dump, integrity-checked, UNSCHEDULED pending owner approval) + restore drill PASSED — 14/14 tables restored into an isolated throwaway container; live DB touched read-only only
- Phase 6F web standalone production build verified locally (output: standalone, API URL baked at build, server boots 200) + Phase 6G Android release audit delivered (PASS WITH GAPS: no keystore material in git, signing/versionCode/prod-URL/device-QA are owner-side; .gitignore now blocks *.keystore/*.jks/*.pem)
- 6C audit fixes: production validator requires explicit allowed_hosts (M2) and drops a dead secret_key check (L1); logout delete_cookie now matches login cookie attributes so the session cookie is reliably cleared (L2) — gate 192 passed
- Live research evidence (FCL-063): one-shot SearXNG loopback container + live GET /research → 200 with official gov.in domains ranked first (two-tier ranking demonstrated live); Docker/containerd storage verified already on /data — no relocation needed
- Phase 6C/6E production-readiness audits delivered (PASS WITH GAPS, no Critical/High) + live vision evidence: POST /vision/analyze 200 from live qwen3-vl:2b (G2 closed); vision now gated through the model registry (6E G1 fix); cold-start 504 finding: warm VL model before serving or raise OLLAMA_TIMEOUT_SECONDS>=300
- Phase 6I incident runbooks (10 scenarios) + Phase 6N legal/privacy/licensing inventory delivered — public launch gated on privacy policy/ToS/consent/retention + qualified legal review (AGPL, Open-Meteo, DPDP, codebase license choice)
- Phase 6B environment separation verified (production validator, secrets hygiene) + Phase 6J CI pipeline added (.github/workflows/ci.yml: backend/web/android/compose gates, no automated deploy)
- Phase 6A architecture review delivered (read-only): single-host Caddy/proposal, risk register (backups + TLS top risks); awaiting owner approvals before 6B (`docs/backend/PHASE_6A_ARCHITECTURE_REVIEW.md`)
- P5F voice: architecture decision ADR-016 (PROPOSED) — client-platform speech APIs for MVP, no server-side voice service (Phase 0 unauthenticated-voice finding class eliminated); GET /voice/capabilities endpoint; 2 new tests — gate 188 passed
- P5E crop-image assistance: POST /api/v1/vision/analyze (multipart, magic-byte validation, 5 MiB cap, in-memory-only processing) via qwen3-vl:2b — enabled in registry (Model 3 gate resolved); outputs observations/uncertainty/next-steps only, no diagnosis-accuracy claims; 6 new tests — gate 186 passed
- P5D research API: GET /api/v1/research via SearXNG — verbatim http/https citations, official agri-source prioritization, freshness stamps, auth + bounded query, 503 provider-failure mapping; SSRF-safe by construction; 7 new tests — gate 180 passed
- P5C weather-aware chat: prompt template v3 attaches provider-observed, timestamped weather (Open-Meteo) for authorized farm coordinates — fail-open, never invented; 2 new tests — gate 173 passed
- Phase 5 final testing: full regression green (backend 171, web 19/19 + build, android typecheck/lint, compose OK), live API smoke pass, security conditions fixed (prompt-slot sanitization, crop-cycle bounds, no error echo) — **verdict PARTIAL: 5C/5D/5E/5F/5I not implemented** (`docs/backend/PHASE_5_FINAL_TESTING_REPORT.md`)
- Phase 5A/5B/5G committed (`7dafc8a`) together with previously-uncommitted owner work (`d39cb47`); SearXNG hardcoded-secret Phase 0 finding closed (already env-substituted in repo; service not deployed)
- P5G reviewer gate closed: independent QA (PASS) + security review (APPROVE, no conditions) — repo-level user-scoping validated; archived-conversation detail semantics documented; one lint fix (typed user param). Full gate 170 passed
- P5G conversation-history API (read-only, user-scoped: GET /conversations, GET /conversations/{id} with messages) + preferences endpoint (PATCH /auth/preferences, own-only); resolves the Phase 4 FCL-044 product-gap finding; 7 new tests — gate 170 passed
- P5B prompt template v2: safety rules (no invented doses/quantities/withdrawal periods) + farm-context block with injection sanitization; chat accepts farm_id (authorized context, 404 non-members); eval runner now evaluates the shipped system prompt — **live eval 10/10 against qwen3:0.6b**; 8 new tests — gate 163 passed
- P5A gate closed: independent qa (PASS) + security review (APPROVE-WITH-CONDITIONS) — both Medium conditions fixed (farm deactivation owner-only; notes bounded), Lows fixed (double-delete, UUID path params → 422); 1 new test — full gate 155 passed
- P5A-03/04 Farm context assembly service (read-only, membership-scoped; unknown fields never fabricated) + privacy pass (coordinates never logged/leaked); 3 new tests — full gate 154 passed
- P5A-02 Crop-cycle API implemented (`/api/v1/farms/{id}/crop-cycles`, `/api/v1/crop-cycles/{id}`): farm-scoped authz, forward-only status transitions, duplicate-season 409; 9 new tests — full gate 151 passed
- P5A-01 Farm API implemented (`/api/v1/farms*`): farm CRUD + membership with service-level role authz (owner/member/viewer, deny-by-default 404 for non-members) + audit events (ID-only, no coordinates); 12 new tests — full gate 142 passed
- Phase 5 implementation plan written (`docs/roadmaps/phases/PHASE_05_IMPLEMENTATION_PLAN.md`): 5A context engine first — farm/crop models + repositories already exist, only API/service surface missing; 5C/5D/5E/5F approval-gated
- Phase 4 final verification: project work committed (`3b2be0c`); live API matrix 15/16 through the real stack (gateway + Ollama + temp DB) — warm avg 10.6 s; finding recorded (no conversation-history API, Low, Phase 5G); final verification report written — awaiting owner acceptance for Phase 5
- Phase 4 execution report amended with post-report model-gate evidence (Models 3/4/6 states, FCL-042/043); mypy auth fast-follow recorded as PROPOSED
- Model 6 (ASR) asset evaluation (read-only): `ai/voice/` is faster-whisper "small", no local weights, no auth, port 8001 not listening (Phase 0 containment finding not live) — integration blocked on architecture decision + owner input
- Model gates post-exit: Model 3 (vision) BLOCKED on product scope (no image-upload API); Model 4 embedding candidates benchmarked (`qwen3-embedding` 1024d/0.4s, `nomic-embed-text` 768d/0.07s) — decision deferred pending retrieval eval + vector-store approval
- Phase 4 execution report: `docs/backend/PHASE_04_EXECUTION_REPORT.md` — status PARTIAL-by-design, model integration matrix, security findings, test/performance summaries, 3 blockers, 5 owner decisions, next safe step
- Phase 4 exit gate: security-engineer APPROVE-WITH-CONDITIONS (zero Critical/High) — all three conditions closed: local secret/artifact git-ignored, crop/location slot-injection covering test, client-facing error text genericized (no internal detail leakage). qa-reviewer independently verified 129-test gate (now 130)
- Phase 4F integration verification: web (typecheck/lint clean, 19/19 tests, production build OK) and android (typecheck/lint clean) both compile against the flat error envelope — no contract drift
- Phase 4D security pass: prompt-injection containment test at the gateway boundary (injection text stays user-role; system prompt never contaminated); secrets scan clean; full security inventory documented (FCL-039)
- Phase 4 docs pass (P4-09): openapi.json regenerated with `AI_BUSY` 503 documented; API.md error table updated (AI_BUSY/UNAUTHORIZED/TOKEN_EXPIRED/HTTP_ERROR); new `docs/backend/RESOURCE_BUDGET.md` (host limits, serial-inference rules, degradation contract); AGRICULTURAL_QA_FLOW error table aligned with gateway codes
- Eval set + runner (P4-08): `backend/evals/eval_set_v1.json` (versioned, machine-checkable criteria + human-review flags) and `backend/scripts/run_evals.py` — `qwen3:0.6b` passes 4/4 machine checks; groundedness items deferred to human review. Model 2 (`qwen3:4b`) benchmarked: 1/5 OK, stays disabled (does not fit 2 GB VRAM). Model 1 acceptance recorded
- Versioned prompt templates (P4-05): system prompt moved to `app/ai/prompts.py` with `PROMPT_TEMPLATE_VERSION`; system policy separated from user content (no user-text interpolation)
- Model registry (Phase 4B): `app/ai/registry.py` — capability/status/license metadata per model; only `qwen3:0.6b` enabled for per-request selection; gateway validates explicitly requested models before any Ollama call; drift detection vs live tags
- Model benchmarks (P4-04): 4 VRAM-fitting chat candidates measured on the live host (`docs/backend/MODEL_BENCHMARKS.md`) — `qwen3:0.6b` 5/5 prompts OK (avg 11.8 s), remains default; quality claims deferred to the P4-08 evaluation set
- Phase 4 preflight report (all 9 gates PASS) + Model 1 acceptance-matrix tests: empty/missing/oversized message → 422; model context bounded to 10 most recent messages; benchmark harness for chat candidates (`backend/scripts/benchmark_models.py`)
- Model inventory (P4-03): `docs/backend/MODEL_INVENTORY.md` — 16 models (44 GB) verified on `/data` HDD storage (HDD-first compliant); VRAM-fitting chat candidates identified; Gemma license flagged
- AI reliability bounds (P4-02): bounded queue depth (`ai_max_queue_depth`, default 10) — excess requests get 503 `AI_BUSY` instead of unbounded waits; degraded-mode contract documented in `ERROR_RECOVERY_FLOW.md` (no automatic paid-provider fallback; client-disconnect cancellation propagates into gateway calls)
- AI gateway interface (P4-01): provider-independent `AIGateway` protocol + Ollama adapter (`app/ai/gateway.py`); chat path depends on the interface; Ollama errors mapped to gateway types; provider specifics confined to the adapter
- `openapi.json` regenerated after the envelope change (FCL-028); Phase 4 implementation plan drafted (`docs/roadmaps/phases/PHASE_04_IMPLEMENTATION_PLAN.md` — 9 tasks P4-01..P4-09 with absorbed exit-gate fast-follows marked complete)
- Phase 4 fast-follows (from exit-gate review): refresh-token reuse now revokes **all** of the user's refresh tokens (chain-walking left tokens ≥2 generations old live); unified flat error envelope `{detail, error_code}` across endpoints and middlewares via a single exception handler (breaking: nested error bodies no longer returned)
- Exit-gate remediation (security-engineer APPROVE-WITH-CONDITIONS): configurable `ALLOWED_HOSTS` (production must declare real hostnames), chunked `Transfer-Encoding` rejected with 413, bounded lockout-tracking memory, admin account-creation audit now records `actor_id`
- Documentation pass (P3-16/P3-17): `openapi.json` regenerated with auth endpoints; `AUTHENTICATION_FLOW.md` finalized as implemented per ADR-008; new `docs/engineering/AUTHZ_MATRIX.md` (endpoint authorization matrix + STRIDE threat model); API/audit/architecture docs aligned; DECISION_REGISTER Phase 3 gate row added (cookie attributes, bearer path, refresh rotation/reuse-kill, admin gate, no account-enumeration) — `bash scripts/check.sh` 98 tests PASS
- New dependencies: `argon2-cffi` (BSD), `email-validator` (for pydantic `EmailStr`)
- Phase 1 authorization: all six governance gates (G1–G6) formally approved and recorded in `docs/engineering/DECISION_REGISTER.md`
- Owner blanket approval (2026-10-28) recorded: ADR-008/Phase 3 auth, production cutover, P1-17, P1-12
- ADR-008 review (opaque sessions, Argon2id, service-layer authZ) written in `docs/engineering/ADR_REVIEWS.md` — APPROVE; Phase 3 unblocked
- P1-14 container baseline completed: `backend/Dockerfile` rewritten (uv 0.5, `uv sync --frozen --no-dev` from `pyproject.toml`+`uv.lock`, non-root uid 10001, `HEALTHCHECK` on `/health/live`, uvicorn `--factory`); backend container verified healthy against PostgreSQL with real end-to-end chat (qwen3:0.6b) persisting to PostgreSQL (236/577 → 238/581 rows)
- `scripts/ollama-bridge.sh` + user `@reboot` crontab: rootless socat forwarder bridging the Docker bridge gateway → host-loopback Ollama
- Real `/health/ready` dependency checks (DB `SELECT 1` + Ollama health ping; 503 with per-dependency status when degraded) replacing a hardcoded stub
- Phase 1 Readiness Report v2.0 (`docs/engineering/PHASE_1_READINESS_REPORT.md`) — status changed from BLOCKED to APPROVED
- Stage 1 AI integration: `qwen3:0.6b` (522 MB, Q4_K_M) selected as default model — fits 2 GiB VRAM, verified on hardware
- `qwen3:0.6b` Ollama smoke tests: 3/3 agricultural prompts coherent, latency < 10 s
- Backend integration test: `/api/v1/chat` endpoint validated with real model — responses persisted to canonical DB
- End-to-end verification: Web → Backend → Ollama → Response confirmed working
- OpenAPI artifact: `docs/api/openapi.json` generated and committed (CI-validated)
- Documentation updates: `docs/backend/BACKEND_AUDIT.md`, `ARCHITECTURE.md`, `API.md`, `ROADMAP.md` synchronized with Phase 1 implementation
- Phase 2 migration rehearsal completed: `backend/scripts/migrate_sqlite_to_pg.py` (export/load/validate); 236 conversations + 577 messages migrated to disposable PostgreSQL 17 with all validation checks passing
- `docs/backend/DATABASE_SCHEMA.md`: ER diagram + data dictionary for the SQLAlchemy 2 schema
- `docs/backend/BACKUP_RUNBOOK.md`: verified `pg_dump -Fc` backup + restore drill procedure

### Changed
- `backend/app/api/v1/chat.py`: Fixed production-blocking 500 — the sync-session dependency crashed every async-mode request (`RuntimeError: Cannot use sync session in async mode`) before the endpoint body; replaced with `get_db_session_optional` (None in async mode, real session in test mode)
- `backend/app/services/chat.py`: **Data-loss fix** — `generate_chat_response`, `get_conversation_history`, `list_user_conversations` used `async for session in get_db_session()` whose post-yield `commit()` was skipped on `return` (silent rollback); converted to `async with db_manager.session()` which commits on clean exit. Chat writes now persist (verified 238/581 rows)
- `backend/app/core/config.py`: Validator now also normalizes bare `postgresql://` → `postgresql+asyncpg://` (psycopg2 not installed); password injection unchanged
- `backend/app/factory.py`: Alembic startup migrations escape `%` for configparser and run via `asyncio.to_thread` (async env.py `asyncio.run()` crashed inside the lifespan loop); startup DSN log redacted (password leak fixed)
- `docker-compose.yml`: Removed unreadable `.env` mount (12-factor config); backend runs as `${MYFARMAI_UID:-1000}:${MYFARMAI_GID:-1000}` (non-root, bind-mount ownership preserved); `OLLAMA_BASE_URL` + `extra_hosts` added for container→host Ollama
- `docker-compose.yml`: Fixed volume mount to use canonical database (`./backend/data:/app/data` instead of `./data:/app/data`) — resolves dual-DB write split (F2)
- `docker-compose.yml`: Backend now uses passwordless DSN + `DATABASE_PASSWORD_FILE` secret mount — fixes auth failure (hardcoded `myfarmai` password did not match the actual secret)
- `backend/alembic/env.py`: `DATABASE_URL` env var now overrides `alembic.ini` `sqlalchemy.url` (dev URL was hardcoded)
- `backend/app/core/config.py`: `database_password_file` setting with validator injecting the password into passwordless PostgreSQL URLs
- `backend/app/core/config.py`: Default model changed from `qwen3:4b` (2.5 GB) to `qwen3:0.6b` (522 MB) — matches `.env` and hardware constraints
- Governance documentation: All gates updated to APPROVED with owner signatures (2026-10-24)
- Backend documentation: Full synchronization of BACKEND_AUDIT.md, ARCHITECTURE.md, API.md, ROADMAP.md to reflect Phase 1 actual state
- `THIRD_PARTY_NOTICES.md`: SearXNG attribution corrected; versions verified against `uv.lock`

### Fixed
- Removed four dead MCP entries from `opencode.json` (`postgres`, `linear`, `aws`, `axiom`). `postgres` crashed at startup because `{env:DATABASE_URL}` expanded empty (no `DATABASE_URL` in env or `.env`) → `ERR_INVALID_URL`; no host-reachable DSN exists anyway (compose Postgres is only on `myfarmai-internal`, no published port). `aws`/`axiom` reference nonexistent npm packages (E404); `linear` has no API key. Root cause of the recurring failures: OpenCode v2.2.5 honors `disabled: true` on cold start but **ignores it on config hot-reload**, so disabled servers respawn after any edit until a service restart. Verified: `opencode mcp list` → 24/24 connected, 0 failed
- Canonical database ambiguity resolved: `backend/data/app.db` (234 conv / 573 msg) confirmed as single source of truth
- Model config split-brain resolved: code default, `.env`, and docs now all specify `qwen3:0.6b`
- Swap saturation risk mitigated: default model now fits in available RAM without swap pressure
- All mypy type errors resolved (32 errors across session.py, base.py, chat.py, repositories.py, API)
- Ruff lint/format clean across entire backend

### Added
- Apache-2.0 LICENSE (governance gate G2 approved; decision recorded in `docs/engineering/DECISION_REGISTER.md`)
- `docs/repository-audit.md` — full 2026-10-23 audit: structure, governance status, risks, staged mapping plan
- Phase 6 documentation set verified against code: `docs/project-overview.md`, `docs/architecture.md`, `docs/setup-guide.md`, `docs/api-documentation.md`, `docs/database-design.md`, `docs/demo-guide.md`
- Root `Makefile` (backend-check/dev, web-check/build, android-check, docker up/down/logs, graph-update)
- VS Code workspace config: `.vscode/{settings,tasks,launch,extensions}.json` (tracked via .gitignore exceptions)
- Historical: `REPOSITORY_AUDIT.md` (2026-10-21 audit), `.agents/` project skills, `.opencode/` skills + agents config
- Baseline commits: `ea9d109` (docs/governance/tooling), `c4aece2` (web: Next.js 15 dashboard), `1f543a9` (android: Expo 51 + brand assets)

### Changed
- README: corrected voice-service containment status, Python 3.12 + uv tooling, `CORS_ALLOWED_ORIGINS`, backend uv commands, Apache-2.0 license reference
- `.gitignore`: track selected `.vscode` files; ignore `*.egg-info/`, `*.tsbuildinfo`, entire `graphify-out/` (rebuildable)

### Removed
- Stray scratch files `web/test.ts`, `web/test.tsx`, `web/test-component.tsx`
- Stale `opencode.json` backup files (consistent with prior CHANGELOG claim)
- Root maintenance reports relocated to `docs/engineering/`

### Added
- Repository audit and maintenance workflow (2026-10-21)
- README.md with project overview and quick start
- CONTRIBUTING.md with development workflow
- SECURITY.md with vulnerability reporting
- Maintenance script (scripts/maintenance.sh)
- Extended pre-commit hooks (ruff, mypy, graphify-update)
- Graphify generated artifacts added to .gitignore
- data/.gitkeep placeholder

### Changed
- Updated .gitignore to exclude generated graph files
- Dashboard/web: removed oversized hero and decorative Smart Farming illustrations from the Home dashboard; added compact welcome with "Ask the AI Assistant" and "Check Crop Health" actions (`docs/ui/MODERN_DASHBOARD_AND_UX.md`)

### Fixed
- Removed obsolete opencode.json backup files
- Removed empty resources/ directory

## [0.1.0] - 2026-10-18

### Added
- Initial backend architecture with FastAPI
- Chat endpoint with Ollama integration
- Weather endpoint with Open-Meteo integration
- Agricultural resources catalogue (12 verified Indian resources)
- SQLite async database with conversation persistence
- Voice service with faster-whisper (Hindi/English)
- Docker Compose development environment
- Web frontend foundation (Next.js 15, Tailwind, TanStack Query)
- Android app foundation (Expo, React Native Paper)
- Design system documentation (principles, tokens, components)
- Graphify knowledge graph initialization

### Backend
- REST API v1 with health, chat, weather, resources endpoints
- Pydantic Settings configuration with .env support
- Ollama client with connection pooling and error handling
- Weather client with WMO code mapping
- Conversation CRUD with SQLite

### Frontend (Web)
- Next.js 15 App Router with TypeScript
- Tailwind CSS 3.4 with custom primary scale
- Chat interface with voice input/output
- Weather card component
- Resources list with category filtering
- TanStack Query v5 for server state
- Zustand for client state

### Frontend (Android)
- Expo Router v3 file-based routing
- React Native Paper v5 (Material 3)
- React Native Reanimated 3 for animations
- Expo Speech / Speech Recognition for voice
- Expo SecureStore for local persistence
- Shared API client and types with web

### Documentation
- Backend architecture, API reference, roadmap
- Frontend design system, color system, interaction guidelines
- Integration guides for web and Android
- Frontend dashboard development roadmap

## [0.0.1] - 2026-10-17

### Added
- Initial project structure
- Basic FastAPI application skeleton
- Docker Compose with backend service
- Basic Next.js web application
- Basic Expo Android application