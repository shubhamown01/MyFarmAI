# MyFarmAI — Non-Destructive Backup Location Audit

**Document ID:** MYFARMAI-BACKUP-AUDIT-001  
**Version:** 1.0  
**Date:** 2026-10-21  
**Status:** Verified — Read-Only Audit Complete  
**Purpose:** Audit the proposed backup location `/data/MyFarmAI-backups` for capacity, permissions, accessibility, and suitability per ADR-015 and PHASE_01_IMPLEMENTATION_PLAN.md Prerequisite #7 / P1-01.

---

## 1. Executive Summary

| Item | Finding | Evidence |
|------|---------|----------|
| **Backup directory exists** | ❌ **NO** — `/data/MyFarmAI-backups` does not exist | `ls: cannot access '/data/MyFarmAI-backups': No such file or directory` |
| **Parent `/data` mount** | ✅ YES — `/dev/sda2` (274 GB, 176 GB free, 33% used) | `df -h /data` |
| **Disk capacity** | ✅ ADEQUATE — 176 GB free vs. ~1 MB SQLite files | `df -h /data` |
| **Filesystem type** | ext4 (assumed, HDD) | `/etc/fstab` not inspected; `/data` on `/dev/sda2` |
| **Permissions** | N/A — directory must be created | `mkdir -p` required |
| **SELinux/AppArmor** | Unknown — not tested | Requires `ls -Z` or `aa-status` |
| **Backup tooling** | ❌ NONE — no scripts, cron, or runbooks in repo | Repository search (Phase 0) |
| **Current DB locations** | Two SQLite files, divergent data | `backend/data/app.db` (122/315), `data/app.db` (35/74) |

**Conclusion:** Backup location is **suitable but not ready**. Directory must be created, permissions set, and a restore drill procedure documented and tested before Phase 1 P1-01 can complete.

---

## 2. Storage Topology (Verified)

```
/
├── /dev/nvme0n1p5 (126 GB, 115 GB used, 5.3 GB free, 96% full)  ← SSD, Docker root here
│   └── /var/lib/docker (16.39 GB images, 23.84 GB volumes)
│
└── /data → /dev/sda2 (274 GB, 85 GB used, 176 GB free, 33% used)  ← HDD
    ├── /data/MyFarmAI/ (repo, source code)
    ├── /data/MyFarmAI/backend/data/app.db (local-dev DB, 98 KB)
    ├── /data/MyFarmAI/data/app.db (Compose DB, 41 KB)
    ├── /data/SentinelAI/ollama/models/ (44 GB, shared with another project)
    └── /data/MyFarmAI-backups/ (DOES NOT EXIST — must create)
```

**Key Finding:** Docker data root is on `/` (SSD, critically low at 5.3 GB free). Backups **must** target `/data` (HDD, 176 GB free) to avoid build failures and host instability (HW-02, HW-03).

---

## 3. Current Database Files (Read-Only Verification)

| File | Path | Size | Conversations | Messages | mtime | Git Status | Integrity |
|------|------|------|---------------|----------|-------|------------|-----------|
| Local-dev DB | `backend/data/app.db` | 98,304 B | 122 | 315 | 2026-10-21 10:33:31 | Untracked, **not ignored** | `ok` |
| Compose DB | `data/app.db` | 40,960 B | 35 | 74 | 2026-10-19 11:07:54 | Untracked, ignored by `data/*` | `ok` |

**Verification Commands Run (Read-Only):**
```bash
sqlite3 backend/data/app.db "PRAGMA integrity_check;"  # → ok
sqlite3 data/app.db "PRAGMA integrity_check;"          # → ok
sqlite3 backend/data/app.db "SELECT COUNT(*) FROM conversations;"  # → 122
sqlite3 backend/data/app.db "SELECT COUNT(*) FROM messages;"       # → 315
sqlite3 data/app.db "SELECT COUNT(*) FROM conversations;"          # → 35
sqlite3 data/app.db "SELECT COUNT(*) FROM messages;"               # → 74
stat backend/data/app.db  # mode 644, mtime 2026-10-21 10:33:31
stat data/app.db          # mode 644, mtime 2026-10-19 11:07:54
```

**No database was modified during this audit.**

---

## 4. Backup Requirements (per ADR-015 & PHASE_01_IMPLEMENTATION_PLAN.md)

### Phase 1 (SQLite) — Required for P1-01 Acceptance
- [ ] Directory `/data/MyFarmAI-backups` created with mode 700 (owner-only)
- [ ] Backup script using SQLite online backup API (`VACUUM INTO`) or stop-writes filesystem copy
- [ ] SHA-256 checksum computed for each backup file
- [ ] `PRAGMA integrity_check` run on backup copy
- [ ] Restore drill: restore to disposable path (e.g., `/tmp/restore-test/app.db`), verify row counts match source
- [ ] Evidence recorded: source checksum, restored checksum, row counts, integrity check results
- [ ] No cron/automation until approved (manual drill only in Phase 1)

### Phase 2 (PostgreSQL) — Future
- [ ] Daily `pg_dump -Fc` (custom format)
- [ ] WAL archiving if RPO < 24 hours (owner must confirm RPO)
- [ ] Encrypted at rest (LUKS volume or pg_dump encryption)
- [ ] Stored outside DB volume (`/data/MyFarmAI-backups/postgres/`)
- [ ] Access restricted (mode 700, dedicated backup user)
- [ ] Quarterly restore test documented

---

## 5. Proposed Backup Procedure (Phase 1 — Not Executed)

```bash
#!/bin/bash
# /data/MyFarmAI/scripts/backup_sqlite.sh — PROPOSED, NOT EXECUTED
set -euo pipefail

BACKUP_DIR="/data/MyFarmAI-backups"
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
CANONICAL_DB="${1:-backend/data/app.db}"  # Requires G1 decision first

mkdir -p "${BACKUP_DIR}"
chmod 700 "${BACKUP_DIR}"

# Stop writes (requires app shutdown or SQLite backup API)
# Option A: VACUUM INTO (requires SQLite 3.27+, online backup)
sqlite3 "${CANONICAL_DB}" "VACUUM INTO '${BACKUP_DIR}/app_${TIMESTAMP}.db';"

# Option B: Stop app → filesystem copy → restart (simpler, requires downtime)
# cp "${CANONICAL_DB}" "${BACKUP_DIR}/app_${TIMESTAMP}.db"

# Verify
sqlite3 "${BACKUP_DIR}/app_${TIMESTAMP}.db" "PRAGMA integrity_check;"

# Checksum
sha256sum "${BACKUP_DIR}/app_${TIMESTAMP}.db" > "${BACKUP_DIR}/app_${TIMESTAMP}.db.sha256"

# Record metadata
cat > "${BACKUP_DIR}/app_${TIMESTAMP}.meta" <<EOF
source: ${CANONICAL_DB}
timestamp: ${TIMESTAMP}
conversations: $(sqlite3 "${CANONICAL_DB}" "SELECT COUNT(*) FROM conversations;")
messages: $(sqlite3 "${CANONICAL_DB}" "SELECT COUNT(*) FROM messages;")
sha256: $(cat "${BACKUP_DIR}/app_${TIMESTAMP}.db.sha256" | cut -d' ' -f1)
integrity: ok
EOF

echo "Backup complete: ${BACKUP_DIR}/app_${TIMESTAMP}.db"
```

### Restore Drill Procedure (Proposed)
```bash
#!/bin/bash
# /data/MyFarmAI/scripts/restore_drill.sh — PROPOSED, NOT EXECUTED
set -euo pipefail

BACKUP_FILE="${1}"  # e.g., /data/MyFarmAI-backups/app_20261021T120000Z.db
RESTORE_PATH="/tmp/restore-test/app.db"

mkdir -p "$(dirname "${RESTORE_PATH}")"
cp "${BACKUP_FILE}" "${RESTORE_PATH}"

# Verify
sqlite3 "${RESTORE_PATH}" "PRAGMA integrity_check;"
CONV_COUNT=$(sqlite3 "${RESTORE_PATH}" "SELECT COUNT(*) FROM conversations;")
MSG_COUNT=$(sqlite3 "${RESTORE_PATH}" "SELECT COUNT(*) FROM messages;")

echo "Restore verification:"
echo "  Conversations: ${CONV_COUNT}"
echo "  Messages: ${MSG_COUNT}"
echo "  Integrity: $(sqlite3 "${RESTORE_PATH}" "PRAGMA integrity_check;")"

# Compare with source (requires canonical DB decision G1)
# diff -u <(sqlite3 "${CANONICAL_DB}" .dump) <(sqlite3 "${RESTORE_PATH}" .dump)
```

---

## 6. Permission & Security Checklist

| Check | Status | Notes |
|-------|--------|-------|
| Directory mode 700 | ❌ NOT CREATED | `mkdir -p /data/MyFarmAI-backups && chmod 700 /data/MyFarmAI-backups` |
| Owner = backup service user | ❌ TBD | Determine backup runner (root? dedicated user? CI?) |
| No world/group read | ❌ TBD | Verify after creation: `stat -c '%a %n' /data/MyFarmAI-backups` |
| Encryption at rest | ❌ NOT YET | Phase 1: file-level (GPG) or LUKS on `/data`; Phase 2: pg_dump encryption |
| Off-host copy | ❌ NOT YET | ADR-015: quarterly off-host copy required; document destination |
| Retention enforcement | ❌ NOT YET | ADR-015: 30 days proposed; implement `find -mtime +30 -delete` after approval |

---

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| `/data` fills up | Low (176 GB free) | Backup failures | Monitor with `df` alerts; prune old backups per retention |
| Permission misconfiguration | Medium | Unauthorized access to conversations | Enforce mode 700; audit with `stat` in backup script |
| Restore drill never tested | High (no procedure exists) | False confidence in backups | **Mandatory**: P1-01 requires successful restore drill |
| Wrong DB backed up (G1 unresolved) | High | Data loss / silent corruption | **Gate G1 must be resolved first** — canonical DB decision required |
| Backup script has bugs | Medium | Corrupt/unusable backups | Code review; test on disposable copy first |

---

## 8. Verification Evidence Required for P1-01 Acceptance

Per `PHASE_01_IMPLEMENTATION_PLAN.md` §3 P1-01 Acceptance Criteria:

- [ ] Working tree committed on branch, restorable from bundle/remote
- [ ] `git check-ignore -v backend/data/app.db` matches (DB ignored)
- [ ] `git ls-files` contains no `*.db`/`*.sqlite*`
- [ ] **Canonical DB decision recorded and signed by owner** (G1)
- [ ] **Backup checksum and integrity check pass; restore drill row counts match** (G5)
- [ ] No secret or user data printed in logs/evidence

**Evidence to Capture:**
```
- Backup file: /data/MyFarmAI-backups/app_<timestamp>.db
- Checksum file: /data/MyFarmAI-backups/app_<timestamp>.db.sha256
- Integrity output: "ok"
- Meta file: conversations=N, messages=M (matching source)
- Restore path: /tmp/restore-test/app.db
- Restore counts: conversations=N, messages=M (identical)
- Owner sign-off on G1 and G5 in DECISION_REGISTER.md
```

---

## 9. Next Steps (Owner Actions Required)

1. **Resolve G1 (Canonical DB)** — Choose `backend/data/app.db` or `data/app.db` or neither
2. **Create backup directory** — `mkdir -p /data/MyFarmAI-backups && chmod 700 /data/MyFarmAI-backups`
3. **Approve backup procedure** — Review proposed scripts above; approve or modify
4. **Execute restore drill** — Run backup + restore drill; record evidence
5. **Record decisions in DECISION_REGISTER.md** — G1 and G5 sign-off

**No implementation work should begin until G1 and G5 are APPROVED with evidence.**