# Phase 6D/6L — Backup Script + Restore Drill (Pre-Work)

**Date:** 2026-10-31 · **Status:** Script + one-shot drill complete. **The nightly schedule is NOT activated** — pending owner approval (the 6D gate).

## What was done

1. **`scripts/backup.sh`** (new, UNSCHEDULED): `pg_dump -Fc` of the Dockerized `myfarmai-postgres` (read-only against the live DB) → `/data/MyFarmAI-backups/postgres/myfarmai-<stamp>.dump` (HDD), integrity-checked with `pg_restore --list` before reporting success, retention of 14 nightly dumps (first-of-month dumps kept). Cron/wiring happens **only after owner approval**.
2. **One-shot backup verified:** `myfarmai-20261031-111627.dump` (44 KB) — integrity check passed (28 TABLE entries).
3. **Restore drill (6L) PASSED:** dump restored via `pg_restore` into an **isolated, temporary postgres:17 container** (`pg-drill`, no volumes, removed after) — **14/14 public tables restored**, matching the live DB's 14. Expected warning: `role "myfarmai" does not exist` (object ownership is not preserved cross-cluster; harmless and standard).

## Honest scope

- The live DB is small (8.5 MB, 0 users — pre-launch). The drill proves the mechanism, not production-scale timing.
- Drill used a per-drill throwaway container with an ephemeral password; nothing touched the live instance beyond the read-only dump.
- Offsite copy of backups: not implemented (owner decision).
- RPO with the proposed nightly schedule: ≤ 24 h; RTO: minutes (drill took seconds at this scale).

## Remaining owner gates

- Approve the nightly schedule (cron entry / compose-side timer) → activates 6D.
- Decide on offsite/second-copy storage.
- Re-run the drill after any schema change (via Alembic migration) and once post-launch at production scale.
