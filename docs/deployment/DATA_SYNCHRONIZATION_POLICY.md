# Data Synchronization Policy

Status: PROPOSED (sync design for the hybrid local/cloud phase; nothing
implemented yet — no sync code exists today, and the canonical-DB governance
gate is still open).

## 1. Data classes and their authority

| Data class | Authority while offline | Cloud copy | Sync rule |
|---|---|---|---|
| Farmer profile, farm records, advisory lists | Local device DB | Neon (proposed; pending owner approval) | Optimistic local write → background push; server wins on conflict per field with `updated_at` compare |
| Chat/QA history | Local (append-only) | Neon | Append-only; no server cherry-wins — reconcile new rows only |
| Selfie verification artifacts | Transient only | **Never replicated** | Deleted after verification; see `PRODUCTION_SECURITY_CHECKLIST.md §4` |
| Weather cache | Local TTL cache | Regenerated from Open-Meteo (licensing gate open) | Cache is disposable; never conflicts |
| Cloud AI quota counters | none locally authoritative | Server-side only | Atomic server UPDATE; clients never compute remaining quota |

## 2. Conflict rules

- Field-level last-writer-wins using monotonic `updated_at` (server clock).
- Append-only data (messages, events) merges union-style; deletion of history
  is a tombstone, not a hard delete, while a client may be offline.
- If the server rejects a write (quota/pause/E6), the client keeps it queued in
  a local outbox table and retries with backoff on next connectivity — never
  silently drops farmer-entered data.

## 3. Sync triggers

1. App foreground / connectivity restored (immediate).
2. Periodic background (15 min when idle in foreground).
3. Manual "Sync now" in profile settings (visible last-sync timestamp).

## 4. Database provider separation (current state)

- Today: single local Compose Postgres. **No migration executed** — the
  canonical-DB location is an owner decision still pending (two SQLite files +
  Compose Postgres exist; see Phase 0 findings). This document does not change
  that gate.
- Post-proposal: Neon Postgres + local device cache + `BACKUP_MYFARMAI.sh`
  dumps to `/data/MyFarmAI-backups/`. Provider swap later = connection-string
  change only (per `CLOUD_DEPLOYMENT_PLAN.md §5.4`).

## 5. Backup/restore relationship

- `BACKUP_MYFARMAI.sh` (+ `--verify` restore drill) is the authoritative
  backup path for the server DB; sync is not a backup.
- Backup cadence before go-live: nightly local dump + the provider's own
  automatic backups verified by one restore drill (owner-approved when
  scheduled).
