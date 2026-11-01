# Phase 7B — Crop Planning & Seasonal Calendar: Implementation Plan

**Date:** 2026-11-01 · **Schema approval:** OWNER APPROVED 2026-11-01 (interactive, "Approve as proposed") — first schema change since the migration gate; canonical SQLite DBs untouched; migration targets Postgres via Alembic only.

## Scope (master prompt §17)
Crop selection, sowing schedule, growth-stage calendar, expected milestones, harvest planning, user-defined tasks; account for variety and planting date; show assumptions; farmer edits are never silently overwritten; plan-change history. **Deferred as not-yet-supported:** irrigation/fertilizer/pest SCHEDULES with doses (rule: no prescriptions without verified regional evidence — a later sub-phase with sourced data; the model below does not preclude them).

## Data model (one Alembic migration, 3 tables)
- **crop_plans** — `id` UUID PK, `user_id` FK users (CASCADE), `farm_id` FK farms (CASCADE), `crop_cycle_id` FK crop_cycles nullable SET NULL, `variety` str(100) nullable, `planting_date` date nullable, `assumptions` text nullable (displayed verbatim), timestamps. One active plan per cycle is NOT enforced in v1 (plans are user documents).
- **crop_plan_tasks** — `id` PK, `plan_id` FK crop_plans (CASCADE), `title` str(200), `due_date` date, `source` enum `user | suggested` (user tasks are never auto-modified or deleted by the system), `status` enum `pending | done | cancelled`, timestamps.
- **crop_plan_revisions** — `id` PK, `plan_id` FK (CASCADE), `changed_by` FK users, `summary` str(500) (what changed), `snapshot` JSON (plan+tasks before change), `created_at`. Append-only; no updates/deletes in code.

## Milestone derivation (assumptions shown, never prescribed)
- Expected milestones derive ONLY from `planting_date + Crop.growing_days_min/max` (existing column, `models/crop.py:68`) → sowing window, expected harvest window (min/max range displayed as a range).
- Every plan response includes the `assumptions` text: "Milestones are estimates from generic growing-day ranges for the crop — variety, local climate and soil are not accounted for unless data exists."
- No fertilizer/chemical quantities — ever — in this sub-phase.

## API (`/api/v1/farms/{farm_id}/crop-plans`, auth + farm-member authorization via `FarmService._authorized_farm`)
- `POST` create plan (user tasks in same payload allowed) → 201; revision 0 recorded ("plan created").
- `GET` list plans for farm; `GET /{plan_id}` (with tasks); `PATCH /{plan_id}` (variety/planting_date/notes — auto-revision with diff summary).
- `POST /{plan_id}/tasks` add task; `PATCH /tasks/{task_id}` status/title/due_date (user tasks freely editable — farmer decisions preserved); task deletion → soft cancel (status), not hard delete.
- `GET /{plan_id}/revisions` history.
- Errors: flat ADR-009 envelope; non-members 404.

## Task breakdown (one owner per file group)
| # | Task | Files | Verification |
|---|---|---|---|
| 7B-1 | Models + Alembic migration | `app/db/models/crop_plan.py`, `app/db/models/__init__.py`, `alembic/versions/` | Migration `upgrade`/`downgrade` clean on a scratch DB; models import cleanly |
| 7B-2 | Repository + service + API | `app/db/repositories.py` (CropPlanRepository), `app/services/crop_plan.py`, `app/api/v1/crop_plans.py`, router | New pytest suite: auth 401, non-member 404, create/get/patch/task lifecycle, revision history recorded, suggested tasks not overwriting user tasks, milestone assumptions present |
| 7B-3 | Web UI (planning screen) | web/src (frontend-engineer) | typecheck/test/lint/build pass |
| 7B-4 | Android UI | android/ (android-engineer) | typecheck + lint pass |
| 7B-5 | Docs + FCL + CHANGELOG | docs/ | API.md section, APP_FLOW §, plan-status update |
| 7B-6 | Independent QA | read-only | qa-reviewer confirms evidence |

## Constraints
- Zero-cost policy: no external calendar/data APIs; milestones are local computations.
- Migration applies to Postgres only; dev SQLite via `create_all` for tests (existing pattern).
- No reminders/notifications in 7B (5I notifications deferred by plan).
