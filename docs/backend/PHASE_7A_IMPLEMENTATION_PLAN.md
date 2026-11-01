# Phase 7A — Farm Intelligence Dashboard: Implementation Plan

**Date:** 2026-11-01 · **Owner approval of Phase 6:** recorded 2026-11-01 (Report 1, commit `04ebdb5`) · **Governing policy:** `docs/engineering/DEPENDENCY_POLICY.md` (zero-cost, open-source, self-host, local-AI)

## Mission (master prompt §16)
An integrated farm intelligence dashboard using existing design conventions: farm overview, crop overview, crop growth stages, weather overview, farm alerts, saved recommendations, farm activity history, upcoming tasks, and relevant agricultural insights. Web and Android must use the same backend business logic.

## Hard requirements
1. Data only from authorized backend sources — no invented statistics; explicit "last updated" timestamps; explicit unavailable-data states.
2. Loading / empty / error / offline states in the UI; approved branding preserved.
3. Zero-cost policy: no new external dependencies; weather stays OPTIONAL-FREE-EXTERNAL with explicit unavailable state.
4. Same business logic for web and Android: both consume one backend endpoint.

## Architecture (builds strictly on existing services)
- **One aggregation endpoint:** `GET /api/v1/dashboard?farm_id=<uuid>` (auth-gated, user-scoped ownership check like farms.py). Response blocks, each with `available: bool`, `updated_at`, and an explicit `unavailable_reason` when data is missing:
  - `farm` — name, address, coordinates (FarmService — existing)
  - `crops` — active crop cycles + current growth stage (CropCycleService — existing)
  - `weather` — current conditions via `weather_client` (fail-open: unavailable on provider failure, reason recorded; never blocks the dashboard)
  - `alerts` — derived locally only (e.g., AI service unavailable, weather unavailable, cycle overdue per existing data) — no invented metrics
  - `activity` — recent audit events for the user's farms (AuditRepository — existing), capped (e.g., 20)
  - `tasks` — upcoming items from crop-cycle milestones (only what already exists in data)
  - `recommendations` / `insights` — from saved chat conversations flagged by the user if such a marker exists; otherwise an explicit empty state (do not fabricate)
- **No new tables.** No Alembic migration unless the owner approves one (schema changes stay gated).
- **Frontend (web first):** one dashboard page following existing Tailwind/shadcn conventions + design-system skills; data via react-query; loading/empty/error/offline states; Android consumes the same endpoint in a later sub-step (7A-android).
- **AI integration (optional insight):** none in 7A v1 — insights from models come only after 7B+ evaluation infrastructure exists (prevents invented statistics).

## Task breakdown (one owner per file group, sequential to avoid conflicts)
| # | Task | Files | Verification |
|---|---|---|---|
| 7A-1 | Dashboard service + endpoint + ownership tests | `backend/app/services/dashboard.py`, `backend/app/api/v1/dashboard.py`, `backend/app/api/v1/router.py`, `backend/tests/test_dashboard.py` | New pytest tests incl. auth 401, cross-user 404, weather-outage degradation; gate 195+ passed, exit=0 |
| 7A-2 | Web dashboard page + states | `web/src/app/(dashboard)/...`, components, react-query hooks | typecheck/test/lint/build pass; axe checks pass |
| 7A-3 | Docs: APP_FLOW, UI_UX docs touch points, FCL, CHANGELOG, graphify update | docs/ | Documented before merge |
| 7A-4 | Android consumption of same endpoint | android/ | typecheck + lint pass |
| 7A-5 | Independent QA verification of 7A evidence | read-only | qa-reviewer confirms |

## Constraints
- 7 GiB RAM / 2 GiB VRAM host — dashboard endpoint is plain DB + optional weather; no model calls in v1.
- Canonical DB untouched; no migration without owner approval.
- Every response block must degrade independently — one unavailable source never blanks the dashboard.
