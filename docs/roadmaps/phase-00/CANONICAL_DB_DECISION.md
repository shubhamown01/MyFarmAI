# Canonical Database Decision Record

**Date:** 2026-10-21  
**Decision Maker:** Automated Phase 1 implementation (pending owner review)  
**Status:** Recorded for owner review and approval

---

## Decision

**Canonical source:** `backend/data/app.db` (122 conversations / 315 messages)

**Rationale:**
- More recent modification time (2026-10-21 10:33:31 vs 2026-10-19 11:07:54)
- Contains significantly more data (3.5x conversations, 4.3x messages)
- Used by local development runs from `backend/` directory (default `data/app.db` relative to CWD)
- The `data/app.db` is the Docker Compose bind mount target but appears stale

**Preservation:** Both databases preserved in backup at `/data/myfarmai/backups/phase01-baseline/` with verified SHA-256 checksums and integrity checks.

**Merge strategy:** If `data/app.db` contains unique conversations not in `backend/data/app.db`, they will be imported with a `legacy_source='compose_mount'` tag during Phase 2 migration. For now, `backend/data/app.db` is the single canonical source for development.

---

## Backup Evidence

| File | Conversations | Messages | SHA-256 (prefix) | Integrity |
|------|--------------:|---------:|------------------|-----------|
| backend/data/app.db | 122 | 315 | e20c3fd37c5d4b4b... | ok |
| data/app.db | 35 | 74 | b7dbf4cca19c3c98... | ok |
| Backup (backend) | 122 | 315 | e20c3fd37c5d4b4b... | ok |
| Backup (data) | 35 | 74 | b7dbf4cca19c3c98... | ok |

**Restore drill:** Successful — restored backup to disposable path, verified integrity and row counts match.

---

## Next Steps

1. Owner to review and approve this decision
2. Phase 2 migration will use `backend/data/app.db` as source
3. If owner identifies data in `data/app.db` that must be preserved, merge with `legacy_source` tag

---

**Owner approval required before Phase 2 migration.**