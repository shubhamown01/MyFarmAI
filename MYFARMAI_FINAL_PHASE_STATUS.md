# MYFARMAI — Final Phase Status & Execution Plan (Master Directive)

**Date:** 2026-11-01 · **Directive:** FINAL MASTER ENGINEERING DIRECTIVE (owner, 2026-11-01) — complete farmer onboarding (identity → selfie liveness → location → map land registration → profile) and public deployment. **Governance:** document-first policy + migration gate in `/data/MyFarmAI/AGENTS.md` remain in force.

## 1. Current phase status (evidence-based)

| Phase | Status | Evidence |
|---|---|---|
| 0 Foundation/governance | MOSTLY COMPLETE — license choice still open (gate) | AGENTS.md policy, DEPENDENCY_POLICY.md, ADR register |
| 1 Core backend | COMPLETE | gate 209 passed exit=0; ADR-009 envelope; rate limiting; request IDs |
| 2 Database | SUBSTANTIAL — 2 verified migrations; **PostGIS not used**; retention = ADR-015 PROPOSED | migrations `6cd2bffd9881`→`a7c1e409f2b3`; nightly backups active |
| 3 Authentication | COMPLETE — email+password, sessions/refresh/lockout/audit, **Google OAuth (E2E 16/16 tests)**, email OTP verification flow. Phone stays unexposed | `tests/test_oauth_api.py` 16/16; backend baseline 272→283 passed 2026-11-04 |
| 4 AI Gateway | COMPLETE (local Ollama, registry, vision, research, graceful fallback; **§10 cloud-AI quota counter implemented 2026-11-04, flag-off until cloud provider is wired**) | Phase 4/6 evidence; `services/ai_quota.py` + tests 11/11; `CLOUD_COST_AND_QUOTA_POLICY.md` §4.1 |
| 5 Farmer experience | SUBSTANTIAL → onboarding stack COMPLETE (identity → selfie liveness → location → land registration → profile; migrations `e3a1b2c3d4e5`/`f4b2c3d4e5a6`/`a5b6c7d8e9f0`), dashboard/weather/research/voice done; Open-Meteo CC-BY attribution shipped in both weather UIs | gate 283 passed 2026-11-04; `LICENSING_DECISIONS.md` D-1 |
| 6 Production readiness | COMPLETE — RS-1 verdict READY WITH CONDITIONS (owner actions pending) | `PHASE_RS1_READINESS_REPORT.md` |
| 7 Advanced intelligence | 7A/7B COMPLETE; 7C+ deferred by owner | FCL-075..088 |
| 8 Zero-cost compliance | RECURRING — DEPENDENCY_POLICY.md current; new deps must be classified | FCL-072 |
| 9 Final deployment | PREP — cloud accounts live (GCP project, Cloudflare, Neon org, GitHub `shubhamown01`, **Zoho Catalyst verified 2026-11-04: org `60094539808`, Project-Rainfall `90779000000015001` created, no card/subscription — student path: $250/6mo, app stopped not charged at threshold**), runners 6/6 verified, deploy plan PROPOSED; **✅ STAGING MILESTONE COMPLETE 2026-11-06: AppSail `myfarmai-backend` at `https://myfarmai-backend-50047414881.development.catalystappsail.in` — `/health/live` = 200, `/health/ready` = 200 `{"database":"ok","ollama":"disabled"}`, `POST /api/v1/chat` = 401 (auth gate works through the proxy); Neon Postgres fully wired (28 tables, alembic head `c8d9e0f1a2b3`); three root causes fixed en route (asyncpg `sslmode` kwarg; profile-defaults overriding explicit empty env; chunked-body 413 via AppSail proxy — security-reviewed); memory 2048→256 MB; full suite 290 passed; public exposure still blocked by owner gates (domain approval)** | `docs/deployment/` (9 docs, LICENSING_DECISIONS owner-approved); `DEPLOY_MYFARMAI.sh` EXIT 0 2026-11-04; `ACCOUNT_SETUP_LOG.md` 2026-11-06 Neon entry (final verification recorded) |

## 2. Missing features (directive → gap)

1. **OAuth signup/login** (Google, Microsoft) — nothing exists; needs adapter + account-linking protection + state/nonce validation.
2. **Email OTP verification** — `email_verified` column exists; no OTP issue/verify/expiry/resend/attempt-limit flow; no email-delivery provider configured.
3. **Phone OTP (SMS)** — no phone field, no E.164 normalization, no SMS adapter. **No zero-cost SMS provider exists** — per directive §4.1, phone verification will be implemented as a modular adapter that reports "temporarily unavailable" until an approved provider is configured.
4. **Mandatory live selfie + liveness** — nothing exists. Local-AI-first reality: no reliable automated liveness on 2 GiB VRAM; directive permits a documented **manual-review workflow** instead of false success. Design: fresh camera capture + randomized challenge prompt + local-VL sanity assist + manual-review queue; account stays `pending_verification` on any failure; never auto-approve.
5. **Geolocation detection + geocoding** — no expo-location / browser geolocation usage; no geocoding adapter (target: self-hostable Nominatim, graceful manual entry).
6. **Map-based land registration** — no Leaflet/OSM, no polygon drawing, no geodesic area calculation, no boundary/plot entities.
7. **Farmer profile + multiple farms/plots** — farms exist (P5A) but no home location, plot, boundary, area-measurement, consent, or verification-status entities.
8. **Public deployment** — blocked on owner: DuckDNS registration, then 6K/6H/6N.

## 3. Technical blockers (require owner input)

| # | Blocker | Why owner input is needed |
|---|---|---|
| B1 | Google/Microsoft OAuth apps | Owner must create the OAuth apps (cloud consoles, redirect URIs) — credentials cannot be self-hosted. Adapter + tests can be built first with env-based config |
| B2 | Email delivery for OTP | No configured provider. Zero-cost options: (a) self-hosted SMTP via owner's own mail server/domain, (b) console/file dev-mode now + provider later, (c) owner-operated Gmail app-password (free tier, not unlimited — must be documented). Decision required |
| B3 | SMS provider | No zero-cost SMS exists. Approve adapter + "temporarily unavailable" mode, or supply an approved provider |
| B4 | New schema (migration gate) | §9 entities are a large multi-migration program; each migration needs owner approval with the staged plan |
| B5 | PostGIS | Adds image/deps weight to the host. Area math does NOT require PostGIS (geodesic polygon area in Python). Recommend: defer PostGIS, store polygons as lat/lon JSON + computed areas; revisit if spatial queries emerge |
| B6 | Liveness approach | Automated liveness is not trustworthy at this hardware tier; recommend capture + challenge + manual-review queue (directive-compliant). Confirm |
| B7 | DPDP privacy review | Mandatory selfie = biometric-adjacent data; consent + retention design must be reviewed before production (ADR-015 ties in) |

## 4. Owner approvals — GRANTED 2026-11-01 (interactive)

1. **Staged schema program approved, NO PostGIS** — polygons as lat/lon JSON, geodesic area computed in Python.
2. **Email delivery: dev-mode adapter now** (OTP to server log/file, clearly marked, never pretends to send), provider-swappable via config.
3. **SMS: adapter interface + E.164 normalization + explicit 'temporarily unavailable' mode** (never pretend delivery).
4. **Liveness: fresh capture + randomized challenge + manual-review queue** — accounts stay pending until human approval; never auto-approve.
5. **OAuth adapters built now with mocked-IdP tests**; owner creates Google/Microsoft apps in parallel; live verification when credentials exist.

### Security-review gate (E3) — 2026-11-02
`docs/backend/E3_SELFIE_SECURITY_REVIEW.md` (security-engineer, read-only) reviewed the proposed selfie/liveness flow before implementation. Key binding corrections: separate `verification_status` lifecycle on users (E1/E2 currently activate with `is_active=True` — reusing it would break sessions); single-use session-bound challenges (5-min TTL, randomized combos, pool ≥6); qwen assist = fixed-enum hint only, never decisive; storage outside repo/web roots, 0700/0600, EXIF stripped, image bytes only via authenticated admin streaming (no URLs ever minted); encrypted-volume-at-rest recommendation; 14 testable requirements + 14 mandatory negative tests.
**Q1 decision (derived from directive §4.2, verbatim text now at docs/governance/FINAL_MASTER_DIRECTIVE_2026-11-01.md):** the §4.2 lifecycle applies to EVERY registration method — OAuth accounts also enter `pending_verification` (selfie mandatory for all); E2 OAuth signup changes from instant-active to pending-verification. Email-OTP accounts likewise stay pending-for-selfie after email verification.

### E3 wave 1 — IMPLEMENTED (FCL-092, 2026-11-02)

Backend selfie pipeline: migration `e3a1b2c3d4e5` (consent_records, selfie_verifications, verification_events, users.verification_status — cycle-verified on isolated postgres); consent → randomized 2-action challenge (single-use, session-bound, 300s, 10/hour cap) → upload with full validation chain (magic-byte sniff, 5 MiB, 512–4096 px, Pillow re-encode stripping ALL metadata, 0700/0600 storage outside repo/web roots) → pending_review. Q1 applied: E1/E2 activation points now set `pending_verification` (is_active/sessions unchanged). NO auto-approval — manual review queue is wave 2 (admin queue + approve/reject + retention deletion + admin streaming endpoint). pillow classified (HPND/MIT-style). Tests: 12 selfie + 22 E1/E2 regression; gate 243 passed / mypy 74 ≤ 85 / EXIT=0.

**E3 wave 2 — COMPLETE (FCL-093, 2026-11-03):** admin manual-review queue + approve/reject (decision final, raw file deleted immediately — kept only until decision), admin-only raw streaming (audited), retention purge (30 days, runs at queue-list start; scheduled job deferred to ops). User approval flips `verification_status` → 'verified' (column is plain String(20), no CHECK — closed-enum decision available for owner). Fixed: retention purge visibility under autoflush=False (flush before same-session re-query); argon2 timing-test band widened for host-load jitter (code unchanged). Tests: 41 combined (7 admin + 12 selfie + 22 E1/E2); gate 250 passed / mypy 74 ≤ 85 / EXIT=0. No new migration.

## 5. Execution plan (staged, one capability at a time)

| Stage | Scope | Blocked by |
|---|---|---|
| E1 | **COMPLETE (FCL-090, 2026-11-02)** — passwordless email-OTP registration: migration b3f2a5d1c7e4 (auth_accounts + contact_verifications), dev-mode delivery adapter, verification service, 2 API routes, 7 tests; gate 216 passed / mypy 71 ≤ 85 / EXIT=0; migration cycle verified on isolated postgres. Phone/SMS stays unexposed (adapter reports "temporarily unavailable") | — |
| E2 | **COMPLETE (FCL-091, 2026-11-02)** — OIDC authorization-code adapters for Google/Microsoft (signature/audience/issuer/nonce/expiry verified via JWKS + PyJWT), account-linking protection (409 OAUTH_EMAIL_TAKEN — never silently merged; pending users claimed), in-memory single-use state store (single-process limitation documented), mocked-IdP tests with real in-test RSA keypair (zero network); pyjwt+cryptography classified and added; 22 tests; gate 231 passed / EXIT=0. **Live IdP verification deferred until owner creates the OAuth apps** (503 OAUTH_NOT_CONFIGURED until then) | B1 credentials for live verification only |
| E3 | **COMPLETE (FCL-092/093, 2026-11-02/03)** — see §4 above (selfie pipeline + admin manual review); gate 250 passed / mypy 74 | — |
| E4 | **BACKEND COMPLETE (FCL-094, 2026-11-03)** — land tables migration `f4b2c3d4e5a6` (home_locations, farm_plots, farm_boundaries, farm_area_measurements; NO PostGIS — polygons as lat/lon JSON per owner approval), applied to Compose postgres with verified downgrade→upgrade cycle; `LandService` + 10 endpoints (`/farms/{farm_id}/plots[... boundary, area]`, `/me/home-location`) reusing FarmService deny-by-default authz; `require_verified_user` (E3 gate) first wired to all land endpoints; server-side geodesic area (spherical-excess, turf.js-style) — client area never trusted; map_drawn → `map_measured`, manual → `user_reported` (never conflated); boundary validation (self-intersection, degenerate, bbox-span) → 422 INVALID_POLYGON; `to_sq_m`/`convert_sq_m` with exact constants (hectare=10,000 m², acre=4,046.8564224 m²); 13 tests; gate 263 passed / mypy 111 (0 in E4 files; repositories.py AuditRepository.log signature corrected to UUID) / EXIT=0. **REMAINING: frontend map UI (web Leaflet + Android), geocoding adapter** | frontend work unblocked; E6 needs owner actions |
| E5 | **BACKEND COMPLETE (FCL-095, 2026-11-03)** — `farmer_profiles` migration `a5b6c7d8e9f0` (progressive optional fields per §8; farming_type/experience CHECK-constrained), applied to Compose postgres with verified downgrade→upgrade cycle; `ProfileService`: profile upsert (`profile_completed` flips in code when `full_name`+`farming_type` set — never client-supplied) + **computed onboarding state machine** (no state table — derived from user/verification/home-location/farm-plot/profile records so it cannot drift; step order contact_verified→verification→location→land→profile); 3 endpoints: `GET /me/onboarding` (auth-gate only — pending users can see their own progress per §12), `GET/PUT /me/farmer-profile` (verified-gate); 7 tests; gate 270 passed / mypy 111 (0 in E4/E5 files) / EXIT=0. **REMAINING: frontend onboarding wizard** | frontend work unblocked; E6 needs owner actions |
| E6 | Public deployment chain (6K→9) per RS-1 conditions | owner actions |
| E7 | End-to-end acceptance tests (§17) + final report + §18 documents | E1–E6 |

Every stage: implement → tests → docs (API/APP_FLOW/FCL) → independent QA. Zero-cost classification for every new dependency before installation.
