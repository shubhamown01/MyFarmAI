#!/bin/bash
# MYFARMAI backup — dumps the Compose PostgreSQL database plus a repo state
# snapshot. Non-destructive; never prints secret values. Requires the stack's
# postgres container (does NOT stop it). Mirrors run_migrations() for the
# password file handling: the password is passed to the container via env and
# never echoed to the terminal or stored in the dump.
#
# Usage: ./BACKUP_MYFARMAI.sh [--verify]
#   --verify   additionally restore the dump into a throwaway postgres container
#              and count tables (proves the dump is usable; never touches prod)
set -u
# shellcheck source=scripts/lib/myfarmai-common.sh
source "$(dirname "$0")/scripts/lib/myfarmai-common.sh"

BACKUP_ROOT="${MYFARMAI_BACKUP_DIR:-/data/MyFarmAI-backups}"
STAMP="$(date '+%Y%m%d-%H%M%S')"
DEST="$BACKUP_ROOT/$STAMP"

echo "=============================================="
echo " MyFarmAI backup — $STAMP"
echo "=============================================="

# Preflight
[ -x "$(command -v docker)" ] || { fail "docker missing"; exit 1; }
docker info >/dev/null 2>&1 || { fail "Docker daemon unreachable"; exit 1; }
docker ps --format '{{.Names}}' 2>/dev/null | grep -qx 'myfarmai-postgres' \
    || { fail "myfarmai-postgres container not running — start the stack first (./RUN_MYFARMAI.sh)"; exit 1; }
PWFILE="$MYFARMAI_ROOT/backend/.pg_password"
[ -f "$PWFILE" ] || { fail "backend/.pg_password missing — cannot authenticate to PostgreSQL."; exit 1; }

mkdir -p "$DEST" || { fail "cannot create $DEST"; exit 1; }

# 1. PostgreSQL dump (via pg_dump inside the running postgres container)
dump="$DEST/myfarmai-postgres.sql.gz"
if docker exec myfarmai-postgres sh -c 'exec pg_dump -U myfarmai -d myfarmai --no-owner' \
        | gzip >"$dump" && [ -s "$dump" ]; then
    ok "PostgreSQL dump: $dump ($(du -h "$dump" | cut -f1))"
else
    rm -f "$dump"
    fail "pg_dump failed or produced an empty file"
    exit 1
fi

# 2. .env files are deliberately NOT copied — credentials stay out of backups.
# 3. Runner/docs evidence snapshot (metadata only, no secrets).
grep -E '^OLLAMA_MODEL=' "$MYFARMAI_ROOT/.env" 2>/dev/null >"$DEST/env-keys-snapshot.txt" || true
{ echo "backup_stamp=$STAMP"; echo "git_head=$(git -C "$MYFARMAI_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"; \
  git -C "$MYFARMAI_ROOT" status --short 2>/dev/null | head -100; } >"$DEST/repo-state.txt"
ok "Repo snapshot: $DEST/repo-state.txt"

# Retention: keep the newest 10 backups, prune older ones (backups dir only).
ls -1dt "$BACKUP_ROOT"/2* 2>/dev/null | tail -n +11 | while IFS= read -r old; do
    rm -rf "$old" && warn "Pruned old backup: $old"
done

# Restore-verification (optional): throwaway container, prod data untouched.
if [ "${1:-}" = "--verify" ]; then
    info "Verifying restorability in a throwaway container…"
    # Reuse the same Postgres image the stack already uses (avoids a new pull).
    local_pg_image="$(docker inspect myfarmai-postgres --format '{{.Config.Image}}' 2>/dev/null || echo postgres:17)"
    docker run -d --rm --name myfarmai-backup-verify \
        -e POSTGRES_PASSWORD=verify -e POSTGRES_USER=myfarmai -e POSTGRES_DB=myfarmai \
        "$local_pg_image" >/dev/null 2>&1 || \
        { fail "could not start verification container"; exit 1; }
    for _ in $(seq 1 20); do
        docker exec myfarmai-backup-verify pg_isready -U myfarmai -d myfarmai >/dev/null 2>&1 && break
        sleep 1
    done
    ok=1
    gunzip -c "$dump" | docker exec -i myfarmai-backup-verify psql -U myfarmai -d myfarmai -q >>"$DEST/restore-verify.log" 2>&1 \
        || ok=0
    tables="$(docker exec myfarmai-backup-verify psql -U myfarmai -d myfarmai -tc 2>/dev/null \
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'" | tr -d '[:space:]')"
    docker rm -f myfarmai-backup-verify >/dev/null 2>&1 || true
    if [ "$ok" = 1 ] && [ -n "$tables" ] && [ "$tables" -gt 10 ]; then
        ok "Restore verified: $tables public tables present in the throwaway restore."
    else
        fail "Restore verification FAILED — see $DEST/restore-verify.log"
        exit 1
    fi
fi

echo "Backups root: $BACKUP_ROOT · Restore: gunzip -c <dump> | docker exec -i myfarmai-postgres psql -U myfarmai -d myfarmai"
echo "=============================================="
