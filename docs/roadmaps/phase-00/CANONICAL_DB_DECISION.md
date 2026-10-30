# Canonical Database Decision Record

**Date:** 2026-10-24  
**Decision Maker:** Owner (2026-10-24)  
**Status:** **APPROVED** — Gate G1 resolved per DECISION_REGISTER.md

---

## Decision

**Canonical source:** `backend/data/app.db` (**234 conversations / 573 messages**)

**Rationale:**
- More recent modification time (2026-10-21 14:54:31 vs 2026-10-19 11:07:54)
- Contains 6.7x more conversations, 7.7x more messages than `data/app.db`
- Used by local development runs from `backend/` directory (default `data/app.db` relative to CWD)
- The `data/app.db` was the Docker Compose bind mount target but contained stale data

**Preservation:** Both databases backed up to `/data/MyFarmAI-backups/phase01-baseline/` with verified SHA-256 checksums and integrity checks.

**Merge strategy:** If `data/app.db` contains unique conversations not in `backend/data/app.db`, they will be imported with `legacy_source='compose_mount'` tag during Phase 2 migration.

---

## Critical Fix Applied (F2 — 2026-10-24)

**Problem:** Docker Compose was mounting `./data:/app/data`, causing containerized deployments to write to the stale `data/app.db` (35 conv / 74 msg) while local development used `backend/data/app.db` (234 conv / 573 msg).

**Fix:** Updated `docker-compose.yml` volume mount:
```yaml
# Before (stale)
volumes:
  - ./data:/app/data

# After (canonical)
volumes:
  - ./backend/data:/app/data
```

**Verification:** `docker compose config --quiet` → exit 0. Container now reads/writes canonical DB.

---

## Backup Evidence (Current)

| File | Conversations | Messages | SHA-256 | Integrity |
|------|--------------:|---------:|---------|-----------|
| backend/data/app.db | **234** | **573** | 7ec66ba840e88cd0a283a680e162a17ceb46cbf00566b94fa7feb4c137fd7f52 | ok |
| data/app.db | 35 | 74 | b7dbf4cca19c3c98f10c7ac602fb6da5347d4df75f595428abd3e42fd6f6b21b | ok |
| Backup (backend) | 234 | 573 | 7ec66ba840e88cd0a283a680e162a17ceb46cbf00566b94fa7feb4c137fd7f52 | ok |
| Backup (data) | 35 | 74 | b7dbf4cca19c3c98f10c7ac602fb6da5347d4df75f595428abd3e42fd6f6b21b | ok |

**Restore drill:** Successful — restored backup to disposable path, verified integrity and row counts match (executed 2026-10-22, accepted 2026-10-24).

---

## Owner Approval

| Gate | Date | Approver | Evidence |
|------|------|----------|----------|
| G1 | 2026-10-24 | Owner | DECISION_REGISTER.md §5, §7 |

---

## Next Steps

1. Phase 2 migration will use `backend/data/app.db` as source
2. If owner identifies data in `data/app.db` that must be preserved, merge with `legacy_source` tag
3. PostgreSQL migration (ADR-003/004/005) to reference this canonical source

---

**APPROVED — Phase 1 unblocked.**