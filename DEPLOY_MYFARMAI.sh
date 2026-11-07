#!/bin/bash
# MYFARMAI deploy — rebuilds and restarts the LOCAL Docker stack with
# preflight checks. This is the development/upgrade path, NOT a public
# production deployment.
#
# PUBLIC MODE IS REFUSED BY DESIGN (phase E6): exposing a host service
# publically requires domain/TLS/security gates and explicit owner approval
# (see docs/deployment/PRODUCTION_SECURITY_CHECKLIST.md). When those gates are
# approved, the `--public` flag will only work if a deployment target has been
# configured in deployment.env — until then every --public attempt fails with
# a loud refusal and no infrastructure is touched.
#
# Usage: ./DEPLOY_MYFARMAI.sh                 # local rebuild + health checks
#        ./DEPLOY_MYFARMAI.sh --public       # guarded; refuses until approved
set -eu
# shellcheck source=scripts/lib/myfarmai-common.sh
source "$(dirname "$0")/scripts/lib/myfarmai-common.sh"

echo "=============================================="
echo " MyFarmAI deploy — $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="

# ---- Preflight -------------------------------------------------------------
docker info >/dev/null 2>&1 || { fail "Docker daemon unreachable"; exit 1; }
ok "Docker daemon running"

[ -f "$MYFARMAI_ROOT/backend/.pg_password" ] || { fail "backend/.pg_password missing"; exit 1; }
ok "Database credentials present"

[ -f "$MYFARMAI_ROOT/docker-compose.yml" ] || { fail "docker-compose.yml missing"; exit 1; }

for port in 3000 8000 5432; do
    if ss -ltn 2>/dev/null | grep -q ":$port " || \
       docker ps --format '{{.Ports}}' 2>/dev/null | grep -q ":$port->"; then
        info "Port $port already in use by the stack (will be reused/recreated)."
    fi
done

# ---- Public-mode guard (hard refuse) ---------------------------------------
if [ "${1:-}" = "--public" ]; then
    cat >&2 <<'EOF'
[FAIL] Public deployment REFUSED (phase E6 gate).
Public production exposure requires ALL of:
  1. Owner-written approval in docs/deployment/PRODUCTION_SECURITY_CHECKLIST.md
  2. A configured public host (none exists yet — see FREE_TIER_COMPARISON.md)
  3. Security review: auth, rate limiting, secret protection (open Phase 0 work)
No infrastructure was created or changed.
EOF
    exit 2
fi
if [ "$#" -gt 0 ]; then warn "Unknown argument '$1' ignored (use no flag or --public)."; fi

# ---- Build & bring up the local stack ---------------------------------------
info "Building images (backend, web)…"
$COMPOSE build >>"$LOG_DIR/deploy.log" 2>&1 || { fail "docker build failed — see $LOG_DIR/deploy.log"; exit 1; }
info "Bringing stack up (existing state preserved; volumes intact)…"
$COMPOSE up -d >>"$LOG_DIR/deploy.log" 2>&1 || { fail "docker compose up failed — see $LOG_DIR/deploy.log"; exit 1; }

# ---- Migrations -------------------------------------------------------------
info "Applying database migrations…"
run_migrations || fail "migrations failed — backend may 500; check $LOG_DIR/migrations.log"

# ---- Health checks ----------------------------------------------------------
failures=0
wait_for_container myfarmai-postgres 60  && ok "postgres healthy"       || { fail "postgres not healthy"; failures=$((failures+1)); }
wait_for_url "backend-ready" http://127.0.0.1:8000/health/ready 60 \
                                            && ok "backend ready"       || { fail "backend /health/ready unreachable"; failures=$((failures+1)); }
wait_for_url "frontend" http://127.0.0.1:3000 60 \
                                            && ok "frontend responding" || { fail "frontend :3000 unreachable"; failures=$((failures+1)); }
ensure_ollama_bridge
docker exec myfarmai-backend .venv/bin/python -c \
    "import urllib.request; urllib.request.urlopen('http://host.docker.internal:11434/api/tags', timeout=8)" \
    >/dev/null 2>&1 && ok "AI: backend reaches host Ollama" \
                    || warn "AI bridge check failed (run ./STATUS_MYFARMAI.sh for details)"

echo "----------------------------------------------"
if [ "$failures" -eq 0 ]; then
    ok "Deploy complete — local stack healthy."
    echo "Local URLs: http://localhost:3000 (web) · http://127.0.0.1:8000 (API)"
    echo "NOTE: this is the LOCAL stack. Public exposure stays blocked (E6 gate)."
else
    fail "Deploy finished with $failures failed health check(s)."
    exit 1
fi
echo "=============================================="
