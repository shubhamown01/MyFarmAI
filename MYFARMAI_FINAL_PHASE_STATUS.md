# MYFARMAI — Final Phase Status & Execution Plan (Master Directive)

**Date:** 2026-11-01 · **Directive:** FINAL MASTER ENGINEERING DIRECTIVE (owner, 2026-11-01) — complete farmer onboarding (identity → selfie liveness → location → map land registration → profile) and public deployment. **Governance:** document-first policy + migration gate in `/data/MyFarmAI/AGENTS.md` remain in force.

## 1. Current phase status (evidence-based)

| Phase | Status | Evidence |
|---|---|---|
| 0 Foundation/governance | MOSTLY COMPLETE — license choice still open (gate) | AGENTS.md policy, DEPENDENCY_POLICY.md, ADR register |
| 1 Core backend | COMPLETE | gate 209 passed exit=0; ADR-009 envelope; rate limiting; request IDs |
| 2 Database | SUBSTANTIAL — 2 verified migrations; **PostGIS not used**; retention = ADR-015 PROPOSED | migrations `6cd2bffd9881`→`a7c1e409f2b3`; nightly backups active |
| 3 Authentication | PARTIAL — email+password + sessions/refresh/lockout/audit only. **NO OAuth, NO OTP verification flow, NO phone** | `app/services/auth.py`, `api/v1/auth.py`; no oauth/otp deps in any manifest |
| 4 AI Gateway | COMPLETE (local Ollama, registry, vision, research, graceful fallback) | Phase 4/6 evidence; Phase 7A/7B consumption |
| 5 Farmer experience | SUBSTANTIAL — dashboard, crops, planning, weather, chat, research, voice. **NO onboarding workflow, NO maps, NO farmer profile entity** | app/ surfaces; no leaflet/expo-location deps |
| 6 Production readiness | COMPLETE — RS-1 verdict READY WITH CONDITIONS (owner actions pending) | `PHASE_RS1_READINESS_REPORT.md` |
| 7 Advanced intelligence | 7A/7B COMPLETE; 7C+ deferred by owner | FCL-075..088 |
| 8 Zero-cost compliance | RECURRING — DEPENDENCY_POLICY.md current; new deps must be classified | FCL-072 |
| 9 Final deployment | NOT STARTED — blocked by 6K domain (owner) | RS-1 report |

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

## 5. Execution plan (staged, one capability at a time)

| Stage | Scope | Blocked by |
|---|---|---|
| E1 | Email-OTP verification flow (schema + adapter interface + dev-mode delivery + tests) — phone adapter stub with explicit "temporarily unavailable" | B2 choice, B4 schema approval |
| E2 | OAuth (Google/Microsoft) adapters, account linking, tests with mock IdP | B1 credentials for live verification only |
| E3 | Selfie capture + challenge + manual-review workflow + consent records + retention | B4, B6, B7 |
| E4 | Geolocation detect + geocoding adapter + map (Leaflet/OSM) + polygon draw/edit + geodesic area + land entities | B4, B5 |
| E5 | Farmer profile + onboarding state machine (resume incomplete onboarding) + progressive completion | B4 |
| E6 | Public deployment chain (6K→9) per RS-1 conditions | owner actions |
| E7 | End-to-end acceptance tests (§17) + final report + §18 documents | E1–E6 |

Every stage: implement → tests → docs (API/APP_FLOW/FCL) → independent QA. Zero-cost classification for every new dependency before installation.
