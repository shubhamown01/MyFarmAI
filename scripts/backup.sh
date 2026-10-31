#!/usr/bin/env bash
# MyFarmAI nightly backup (Phase 6D) — UNSCHEDULED pending owner approval.
# Approved usage: run from cron AFTER the owner approves the schedule.
# One-shot manual run: bash scripts/backup.sh
#
# Backs up the Dockerized PostgreSQL (myfarmai-postgres, db myfarmai) to
# /data/MyFarmAI-backups/ (HDD). Read-only against the live DB (pg_dump).
# Retention: keep 14 nightly + all first-of-month dumps (delete older only
# with owner approval).

set -euo pipefail

CONTAINER="${MYFARMAI_PG_CONTAINER:-myfarmai-postgres}"
PG_USER="${MYFARMAI_PG_USER:-myfarmai}"
PG_DB="${MYFARMAI_PG_DB:-myfarmai}"
DEST="${MYFARMAI_BACKUP_DIR:-/data/MyFarmAI-backups/postgres}"
KEEP_NIGHTLY=14

mkdir -p "$DEST"
STAMP=$(date +%Y%m%d-%H%M%S)
FILE="$DEST/myfarmai-$STAMP.dump"

docker exec "$CONTAINER" pg_dump -U "$PG_USER" -d "$PG_DB" -Fc > "$FILE"

# Integrity check: a custom-format dump must list its contents cleanly.
if docker exec -i "$CONTAINER" pg_restore --list < "$FILE" > /dev/null 2>&1; then
    echo "backup OK: $FILE ($(du -h "$FILE" | cut -f1))"
else
    echo "backup FAILED integrity check: $FILE" >&2
    rm -f "$FILE"
    exit 1
fi

# Retention: delete nightly dumps beyond KEEP_NIGHTLY (keep 1st-of-month).
# grep exits 1 when there is nothing to delete — the || true covers it.
{ ls -1t "$DEST"/myfarmai-*.dump 2>/dev/null | tail -n +$((KEEP_NIGHTLY + 1)) |
    grep -vE 'myfarmai-[0-9]{8}-01-' | xargs -r rm -f; } || true
