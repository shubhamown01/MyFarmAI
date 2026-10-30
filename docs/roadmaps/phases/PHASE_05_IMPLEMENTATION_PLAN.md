# Phase 5 Implementation Plan — Intelligent Agricultural Assistance

**Date:** 2026-10-30 · **Status:** PROPOSED → owner-accepted Phase 4 unlocks planning; 5A implementation follows this plan · **Predecessor:** Phase 4 COMPLETE (owner-accepted 2026-10-30; FCL-029..044)

## Baseline (verified 2026-10-30 — not assumptions)

| Asset | State |
|---|---|
| Farm/FarmMember/FarmRole, Crop, CropCycle models | **Exist** (`app/db/models/farm.py`, `crop.py`) — ownership, members+roles, lat/long, cycles with dates/area/status |
| FarmRepository / CropRepository / CropCycleRepository | **Exist** (`app/db/repositories.py`) |
| User.preferred_language | Exists on the model |
| Weather service + API | Exists (provider adapter pattern); **Open-Meteo non-commercial restriction = owner-blocked for anything beyond dev use** (Phase 0 finding) |
| Chat + gateway + registry + prompts | Phase 4 COMPLETE; only `qwen3:0.6b` enabled |
| Farm/crop **API endpoints** | **MISSING** — router has only health/auth/chat/weather/resources |
| Conversation-history API | MISSING (FCL-044 finding) — needed by 5G |
| SearXNG | Infra present; **AGPL review + hardcoded-secret rotation pending** (Phase 0 findings) |
| Vision / ASR / TTS / translation | Not enabled; gates blocked on owner decisions (FCL-042/043) |

## Workstreams (one at a time, each: implement → test → secure → document → gate)

### P5A — Farm/crop context engine (FIRST)
1. ~~`P5A-01` Farm API~~ — **COMPLETE (2026-10-30, FCL-046)**: farm CRUD + membership, service-level role authz, 13 tests after FCL-049 security fixes; gate 155 passed. audit events emitted via AuditRepository (FARM_CREATED/UPDATED, FARM_MEMBER_ADDED/REMOVED/ROLE_CHANGED); ID-only descriptions — no coordinates logged.
2. ~~`P5A-02` Crop-cycle API~~ — **COMPLETE (2026-10-30, FCL-047)**: nested create/list + flat get/patch, forward-only status transitions, 9 tests; gate 151 passed (pre-FCL-049). Note: no CROP_CYCLE_* audit event types exist yet (owner decision at P5A gate).
3. ~~`P5A-03` Context assembly service~~ — **COMPLETE (2026-10-30, FCL-048)**: `FarmContextService.get_context` (read-only, membership-scoped) returns `FarmContext` (name/timezone/address/coords/active_crops); missing fields stay None/[]; wiring into `build_system_prompt` happens in P5B (template v2).
4. ~~`P5A-04` Privacy~~ — **COMPLETE (2026-10-30, FCL-048)**: audit descriptions ID-only; `FarmContext` docstring + FCL record the never-log-coordinates rule; cross-user exposure denied (404 tests). Interim retention: farm data retained until account/farm deletion (ADR-015 owner-pending).
- **Gate:** ~~ownership/authorization tests (cross-user → 404), validation tests, full regression, docs~~ — **PASSED (2026-10-30, FCL-049)**: qa-reviewer PASS (154 gate, no authz bypass, no PII in logs) + security-engineer APPROVE-WITH-CONDITIONS → both Medium conditions FIXED with tests (`is_active` owner-only; `notes` bounded) + Lows fixed (double-delete removed, UUID path params → 422). Final gate **155 passed**. Open owner decisions: CROP_CYCLE_* audit event types; deactivated-farm direct-ID visibility semantics; owner-adds-member-by-UUID (MVP-accepted)

### P5B — Agricultural intelligence engine — **COMPLETE (2026-10-31, FCL-050)**
- ~~Context-grounded answers~~ template v2 (safety rules: no invented doses/quantities/withdrawal periods, no ranges/typical values; context block labeled as data with newline-collision sanitization); `farm_id` on chat requests resolves authorized context (404 non-members); eval set extended (4 new items) — **live eval 10/10 PASS against qwen3:0.6b**; 8 new tests; gate 163 passed. Open: eval-p5b-context-groundedness human review (owner)
- Context-grounded answers via 5A context + Phase 4 prompts: understanding/context/actions/risks/missing-info/uncertainty; safety rules (no invented doses/quantities/withdrawal periods; local-assistance referral under uncertainty) enforced in the system prompt template (bump `PROMPT_TEMPLATE_VERSION`) + eval-set items.
- **Gate:** eval-set additions (groundedness human-review flags), safety-prompt tests, regression.

### P5C — Weather-aware assistance
- **BLOCKED until Open-Meteo licensing is resolved** (non-commercial restriction — Phase 0 finding). Safe prep: freshness metadata + staleness handling in the existing weather adapter (no new provider without owner approval).

### P5D — Knowledge/research
- **BLOCKED until SearXNG AGPL review + secret rotation complete** (Phase 0 findings). Planning for Phase 6 roadmap alignment.

### P5E — Crop image assistance
- **BLOCKED on Model 3 gate** (no image-upload API; owner decision pending).

### P5F — Voice-first experience
- **BLOCKED on Model 6 gate** (architecture decision: separate service vs backend-native; the `ai/voice/` service has no auth).

### P5G — Conversation memory & personalization — **COMPLETE (2026-10-31, FCL-051)**
- ~~Conversation-history API (FCL-044 finding)~~: read-only GET /conversations (limit 1–100) + GET /conversations/{id} with last-50 messages, user-scoped at repository level (P3-05); preferences API (PATCH /auth/preferences, own-only, `^[a-z]{2}$`). 7 tests — gate 170 passed. **Reviewer gate closed (FCL-052): QA PASS + security APPROVE** — repo-level user-scoping validated airtight; archived-conversation detail semantics documented; ordering-tie and limit-bound test gaps noted as Lows. Open: ADR-015 retention owner-pending
- Conversation-history API (FCL-044 finding): list/get user conversations + messages, user-scoped; preferences API (language). Privacy rules: user-scoped retrieval only; correction support; app data vs model output distinguishable.
- **Gate:** ownership tests, retention behavior per ADR-015, regression.

### P5H — Farmer-facing UX (web/Android)
- Loading/empty/error/offline states per workflow; existing design system unchanged; only after the backing APIs exist (5A/5C/5G).

### P5I — Notifications & action plans
- Only after weather + farm/crop data are reliable (explicitly last; likely Phase 6+).

## Sequencing & gates

5A → 5B → 5G are unblocked now. 5C/5D/5E/5F are approval-gated. 5H follows its APIs. 5I last. Every workstream: `bash scripts/check.sh` green + docs + FCL entry before the next starts. Schema changes only via owner-approved Alembic migrations (none anticipated for 5A — models exist).

## Verification commands

Backend gate from repo root: `bash scripts/check.sh` (expect 130+ tests). Web: `npm run typecheck && npm run lint && npm test` in `web/`. Android: `npm run typecheck && npm run lint` in `android/`.
