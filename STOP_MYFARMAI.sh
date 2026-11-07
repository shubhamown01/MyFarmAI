#!/bin/bash
# MYFARMAI safe shutdown — stops only MyFarmAI-managed services.
# Never uses `down -v` (would destroy the postgres_data volume).
set -u
# shellcheck source=scripts/lib/myfarmai-common.sh
source "$(dirname "$0")/scripts/lib/myfarmai-common.sh"

echo "Stopping MyFarmAI services (this project only)…"

stop_web_dev

# `stop` (not `down -v`): keeps containers and the postgres_data volume intact.
# Compose acts only on this project's services — unrelated containers on the
# host are untouched.
if $COMPOSE stop >>"$LOG_DIR/docker.log" 2>&1; then
    ok "Compose services stopped (postgres data preserved in volume 'postgres_data')."
else
    fail "docker compose stop failed — check $LOG_DIR/docker.log"
    exit 1
fi

echo ""
ok "MyFarmAI stopped. Start again with ./RUN_MYFARMAI.sh"
