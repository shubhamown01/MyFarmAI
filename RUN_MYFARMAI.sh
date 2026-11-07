#!/bin/bash
# MYFARMAI master startup — single entry point.
# Usage: ./RUN_MYFARMAI.sh [--mode local|development|public-demo|production] [--open-browser]
set -u
# shellcheck source=scripts/lib/myfarmai-common.sh
source "$(dirname "$0")/scripts/lib/myfarmai-common.sh"

MODE="local"
OPEN_BROWSER=0
while [ $# -gt 0 ]; do
    case "$1" in
        --mode) MODE="${2:-local}"; shift 2 ;;
        --mode=*) MODE="${1#*=}"; shift ;;
        --open-browser) OPEN_BROWSER=1; shift ;;
        *) warn "Unknown argument: $1"; shift ;;
    esac
done

echo "=============================================="
echo " MyFarmAI — starting (mode: $MODE)"
echo "=============================================="

# ── Public modes require explicit owner configuration (E6 gates) ────────────
case "$MODE" in
    local|development) : ;;
    public-demo|production)
        fail "Mode '$MODE' requires owner-approved public deployment (E6):"
        echo "  - a configured domain / DuckDNS hostname,"
        echo "  - TLS reverse proxy (Caddy/Cloudflare Tunnel) configuration,"
        echo "  - completed security review (auth exposure, rate limiting)."
        echo "  See docs/runner-guide.md and MYFARMAI_FINAL_PHASE_STATUS.md."
        exit 1
        ;;
    *) fail "Unknown mode '$MODE' (use local|development|public-demo|production)"; exit 1 ;;
esac

# ── A. Preflight ────────────────────────────────────────────────────────────
PREFLIGHT_FAILED=0

for d in backend web android scripts; do
    [ -d "$MYFARMAI_ROOT/$d" ] || { fail "Missing project directory: $d"; PREFLIGHT_FAILED=1; }
done
[ "$PREFLIGHT_FAILED" = 1 ] && exit 1
ok "Project directories present"

require_cmd docker || { fail "Docker is not installed or not in PATH."; exit 1; }
docker info >/dev/null 2>&1 || { fail "Docker daemon unreachable (permission? try 'sudo usermod -aG docker $USER' and re-login)."; exit 1; }
ok "Docker available"

$COMPOSE version >/dev/null 2>&1 || { fail "Docker Compose v2 unavailable."; exit 1; }
ok "Docker Compose available"

# Environment configuration
if [ ! -f "$MYFARMAI_ROOT/.env" ]; then
    if [ -f "$MYFARMAI_ROOT/.env.example" ]; then
        cp "$MYFARMAI_ROOT/.env.example" "$MYFARMAI_ROOT/.env"
        warn "Created .env from .env.example — review it: web URL http://localhost:3000 works with defaults."
        echo "  Owner-configured values (OAuth, email provider, SMS) stay empty until provided."
    else
        fail ".env missing and no .env.example found."; exit 1
    fi
else
    ok ".env present"
fi
[ -f "$MYFARMAI_ROOT/backend/.pg_password" ] || { fail "backend/.pg_password missing (PostgreSQL secret)."; exit 1; }
ok "Database secret file present"

# Disk / memory (runner needs headroom; models are large)
avail_mb="$(df -Pm "$MYFARMAI_ROOT" | awk 'NR==2 {print $4}')"
if [ "${avail_mb:-0}" -lt 2048 ]; then
    fail "Only ${avail_mb} MiB free on the repository filesystem (need ≥ 2 GiB)."; exit 1
fi
ok "Disk: ${avail_mb} MiB free"
mem_mb="$(free -m | awk '/^Mem:/ {print $2}')"
info "Memory: ${mem_mb} MiB total (7 GiB-class hosts are supported; AI inference shares this)"

# Port conflicts (8000 backend, 3000 web). 5432 stays container-internal.
for port in 8000 3000; do
    if ss -tln 2>/dev/null | grep -q ":$port "; then
        case "$port" in
            8000) warn "Port 8000 in use — assuming an existing backend and reusing it." ;;
            3000) warn "Port 3000 in use — assuming an existing web server and reusing it." ;;
        esac
    fi
done
ok "Port check done"

# Ollama (host service — reuse, never duplicate)
if curl -s --max-time 3 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    ok "Ollama reachable on host (127.0.0.1:11434)"
else
    warn "Ollama not reachable on 127.0.0.1:11434. AI chat will fail until it is started."
    warn "Start it with: ollama serve   (do not let the runner install models.)"
fi

MODEL="$(grep -E '^OLLAMA_MODEL=' "$MYFARMAI_ROOT/.env" 2>/dev/null | cut -d= -f2 | tr -d '\"' )"
MODEL="${MODEL:-qwen3:4b}"
if curl -s --max-time 3 http://127.0.0.1:11434/api/tags 2>/dev/null | grep -q "\"name\":\"$MODEL\""; then
    ok "AI model '$MODEL' installed"
else
    warn "Model '$MODEL' not found in Ollama. Install with: ollama pull $MODEL"
    warn "(Check disk/RAM first — do not pull automatically without owner approval.)"
fi

# ── B. Service startup (dependency order) ───────────────────────────────────
ensure_ollama_bridge

info "Starting PostgreSQL…"
$COMPOSE up -d postgres >>"$LOG_DIR/docker.log" 2>&1 || { fail "PostgreSQL failed to start — see $LOG_DIR/docker.log"; exit 1; }
wait_for_container myfarmai-postgres 90 || { fail "PostgreSQL did not become healthy — see $LOG_DIR/docker.log"; $COMPOSE logs postgres | tail -20; exit 1; }
ok "PostgreSQL healthy"

info "Applying database migrations…"
if run_migrations; then ok "Migrations up to date"; else fail "Migrations failed — see $LOG_DIR/migrations.log"; exit 1; fi

info "Starting backend…"
$COMPOSE up -d backend >>"$LOG_DIR/docker.log" 2>&1 || { fail "Backend failed to start — see $LOG_DIR/docker.log"; exit 1; }
if wait_for_url "backend" "http://127.0.0.1:8000/health/live" 90; then ok "Backend live on http://127.0.0.1:8000 (loopback only)"
else fail "Backend not responding — see logs: docker compose logs backend"; $COMPOSE logs backend | tail -20; exit 1; fi
if wait_for_url "backend-ready" "http://127.0.0.1:8000/health/ready" 60; then ok "Backend ready (dependencies OK)"
else warn "Backend /health/ready not fully ready — see docker compose logs backend"; fi

info "Starting web frontend…"
if start_web_dev; then
    if wait_for_url "web" "http://127.0.0.1:3000" 120; then ok "Web frontend live on http://localhost:3000"
    else fail "Web frontend not responding — see $LOG_DIR/web-dev.log"; exit 1; fi
else exit 1; fi

# ── C/D. Integration verification ───────────────────────────────────────────
info "Verifying frontend → backend connectivity…"
# The web dev server proxies /api/v1 to the backend; hitting it through :3000
# proves the rewrite works end to end.
code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 http://127.0.0.1:3000/api/v1/health 2>/dev/null || true)"
case "$code" in 2??|3??) ok "Frontend→backend proxy works (HTTP $code through :3000)" ;; *) warn "Frontend→backend proxy check returned HTTP ${code:-none}" ;; esac

info "Verifying backend → Ollama + real AI inference (may take ~60 s on first load)…"
rm -f "$LOG_DIR/ai-smoke.log"
if ai_smoke_test; then
    ok "AI verified: container→Ollama bridge + real model inference (+end-to-end chat if smoke creds configured)"
else
    fail "AI verification FAILED — check $LOG_DIR/ai-smoke.log and 'docker compose logs backend'"
    warn "Common cause: ollama-bridge not listening (scripts/ollama-bridge.sh) or model missing."
    AI_FAILED=1
fi

info "Verifying database persistence…"
if docker exec myfarmai-postgres psql -U myfarmai -d myfarmai -tc "SELECT 1" >/dev/null 2>&1; then
    ok "Database operations verified (read test)"
else
    warn "Database read test failed inside container"
fi

# ── E. Summary ──────────────────────────────────────────────────────────────
echo ""
echo "=============================================="
echo " MyFarmAI status"
echo "=============================================="
printf '  %-12s %s\n' "PostgreSQL:"  "healthy (container-internal, volume: postgres_data)"
printf '  %-12s %s\n' "Backend:"     "http://127.0.0.1:8000 (loopback only)"
printf '  %-12s %s\n' "API docs:"    "http://127.0.0.1:8000/docs"
printf '  %-12s %s\n' "Frontend:"    "http://localhost:3000"
printf '  %-12s %s\n' "Ollama:"      "http://127.0.0.1:11434 (host, reused — not duplicated)"
printf '  %-12s %s\n' "AI model:"    "$MODEL"
echo "  Logs:        $LOG_DIR (web-dev.log, docker.log, migrations.log, ai-smoke.log)"
echo "  Stop:        ./STOP_MYFARMAI.sh"
echo "  Status:      ./STATUS_MYFARMAI.sh"
echo "=============================================="

if [ "${AI_FAILED:-0}" = 1 ]; then
    echo "NOTE: core services are up, but AI inference FAILED (see above)."
fi

if [ "$OPEN_BROWSER" = 1 ]; then
    if require_cmd xdg-open; then xdg-open http://localhost:3000 >/dev/null 2>&1 &
        ok "Opening http://localhost:3000 in the browser…"
    else warn "xdg-open unavailable — open http://localhost:3000 manually."; fi
else
    echo "Open http://localhost:3000 in your browser."
fi

# Nonzero exit if an essential service is unavailable.
exit "${AI_FAILED:-0}"
