# MyFarm AI — PostgreSQL Backup & Restore Runbook

**Version:** 0.1.0
**Date:** 2026-10-28
**Scope:** PostgreSQL 17 running in Docker Compose (`myfarmai-postgres`, database `myfarmai`, user `myfarmai`)
**Status:** Verified by restore drill on 2026-10-28 (P2-28/P2-29)

---

## 1. Backup procedure

### Full logical backup (`pg_dump -Fc`)

```bash
# From the host — writes to the /data backup area (HDD-first policy)
TS=$(date +%Y%m%d_%H%M%S)
docker exec myfarmai-postgres pg_dump -U myfarmai -Fc myfarmai \
  > /data/MyFarmAI-backups/phase02-rehearsal/myfarmai_${TS}.dump
sha256sum /data/MyFarmAI-backups/phase02-rehearsal/myfarmai_${TS}.dump
```

- Format: custom (`-Fc`) — compressed, supports selective restore and parallel restore.
- Record the SHA-256 alongside the dump; verify before any restore.
- Recommended cadence: daily, plus immediately before any migration or upgrade.
- Retention: keep at least 7 daily dumps; prune older dumps only after a successful restore test of a newer dump.

### Verified evidence (2026-10-28)

| Item | Value |
|------|-------|
| Dump file | `/data/MyFarmAI-backups/phase02-rehearsal/myfarmai_rehearsal_20261028_153133.dump` |
| Size | 64,058 bytes |
| SHA-256 | `9642d3301af461f6d35b64e74320f6217a8d5b7bad4f34ad05b928ff6a4d9bdd` |
| Source state | 1 user / 236 conversations / 577 messages |

---

## 2. Restore procedure

### Restore into a fresh database (drill / disaster recovery)

```bash
# 1. Create an empty target database
docker exec myfarmai-postgres psql -U myfarmai -d postgres \
  -c "CREATE DATABASE myfarmai_restore_test;"

# 2. Restore the dump
docker exec -i myfarmai-postgres pg_restore -U myfarmai \
  -d myfarmai_restore_test --no-owner --role=myfarmai \
  < /path/to/myfarmai_<TS>.dump

# 3. Validate row counts and referential integrity
docker exec myfarmai-postgres psql -U myfarmai -d myfarmai_restore_test -tc "
  SELECT (SELECT COUNT(*) FROM users) u,
         (SELECT COUNT(*) FROM conversations) c,
         (SELECT COUNT(*) FROM messages) m,
         (SELECT COUNT(*) FROM messages m2
            LEFT JOIN conversations c2 ON m2.conversation_id = c2.id
           WHERE c2.id IS NULL) orphans;"
```

### Verified drill evidence (2026-10-28)

| Check | Expected | Actual | Result |
|-------|----------|--------|--------|
| users | 1 | 1 | PASS |
| conversations | 236 | 236 | PASS |
| messages | 577 | 577 | PASS |
| orphan messages | 0 | 0 | PASS |

### Production cutover restore

For a real incident, restore into a **new** database, validate, then point the
backend at it (update `DATABASE_PATH`) — never restore in-place over the live
database. The Compose backend service must be restarted after the DSN change.

---

## 3. Known constraints

1. **Backup does not include the legacy SQLite file.** The canonical SQLite
   (`backend/data/app.db`) is backed up separately (see
   `/data/MyFarmAI-backups/` — file copy + SHA-256, verified 2026-10-24).
   Until the production cutover is approved, SQLite remains the system of
   record for live data.
2. **No WAL archiving yet.** `pg_dump` gives point-in-time snapshots only.
   WAL archiving / PITR is a Phase 8 hardening item.
3. **Off-host copies.** Dumps currently live on the same host (`/data`).
   Copying backups off-host is required before production exposure (Phase 8).
4. **Encryption at rest** for dumps is a Phase 8 item; the `/data` volume is
   currently unencrypted.
5. **Secrets:** the dump contains chat content (user data). Handle backup files
   with the same confidentiality as production data; do not commit them to Git
   (`.gitignore` covers `/data/MyFarmAI-backups` via location outside repo).

---

## 4. Recovery time / recovery point notes

- Restore of the 64 KB rehearsal dump completed in under 5 seconds; expect
  proportional scaling for production-sized databases.
- RPO with daily dumps: up to 24 hours of data loss. Tighten cadence or add
  WAL archiving before production exposure (Phase 8, ADR-015).

---

*Runbook verified against PostgreSQL 17 / Docker Compose on 2026-10-28.*
