#!/bin/bash
# MyFarmAI runner-script shared helpers. Sourced by RUN/STOP/RESTART/STATUS.
# Never prints secret values (passwords, tokens, OTPs).

MYFARMAI_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$MYFARMAI_ROOT" || exit 1

COMPOSE="docker compose"
LOG_DIR="$MYFARMAI_ROOT/logs"
mkdir -p "$LOG_DIR" 2>/dev/null || true

WEB_PID_FILE="$LOG_DIR/web-dev.pid"
WEB_LOG="$LOG_DIR/web-dev.log"

# Status colors (plain when not a TTY).
if [ -t 1 ]; then
    C_G=$'\033[32m'; C_R=$'\033[31m'; C_Y=$'\033[33m'; C_B=$'\033[34m'; C_0=$'\033[0m'
else
    C_G=""; C_R=""; C_Y=""; C_B=""; C_0=""
fi

ok()   { printf '%s[OK]%s %s\n' "$C_G" "$C_0" "$*"; }
fail() { printf '%s[FAIL]%s %s\n' "$C_R" "$C_0" "$*"; }
warn() { printf '%s[WARN]%s %s\n' "$C_Y" "$C_0" "$*"; }
info() { printf '%s[..]%s %s\n' "$C_B" "$C_0" "$*"; }

require_cmd() {
    command -v "$1" >/dev/null 2>&1
}

# Wait until a URL responds (HTTP 2xx/3xx/401/403 all count as "responding").
# Usage: wait_for_url NAME URL TIMEOUT_SECONDS
wait_for_url() {
    local name="$1" url="$2" timeout="${3:-60}" elapsed=0
    while [ "$elapsed" -lt "$timeout" ]; do
        code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "$url" 2>/dev/null || true)"
        case "$code" in
            2??|3??|401|403) return 0 ;;
        esac
        sleep 2; elapsed=$((elapsed + 2))
    done
    return 1
}

# Wait for a compose healthcheck to report healthy.
wait_for_container() {
    local name="$1" timeout="${2:-90}" elapsed=0
    while [ "$elapsed" -lt "$timeout" ]; do
        state="$(docker inspect "$name" --format '{{.State.Health.Status}}' 2>/dev/null || true)"
        [ "$state" = "healthy" ] && return 0
        sleep 2; elapsed=$((elapsed + 2))
    done
    return 1
}

# Ensure the host Ollama bridge forwarder is running (host Ollama binds
# 127.0.0.1 only; backend containers reach it via host.docker.internal).
ensure_ollama_bridge() {
    "$MYFARMAI_ROOT/scripts/ollama-bridge.sh" >/dev/null 2>&1 || true
}

# Start the web dev server if not already listening on :3000.
start_web_dev() {
    if curl -s -o /dev/null --max-time 2 http://127.0.0.1:3000; then
        warn "Web already responding on http://localhost:3000 — reusing it."
        return 0
    fi
    if [ ! -d "$MYFARMAI_ROOT/web/node_modules" ]; then
        info "Installing web dependencies (first run)…"
        (cd "$MYFARMAI_ROOT/web" && npm install >>"$WEB_LOG" 2>&1) || { fail "web npm install failed — see $WEB_LOG"; return 1; }
    fi
    info "Starting web frontend (dev server)…"
    # setsid detaches the npm process tree so it survives the runner exiting.
    (cd "$MYFARMAI_ROOT/web" && setsid nohup npm run dev >>"$WEB_LOG" 2>&1 & echo $! >"$WEB_PID_FILE")
}

# Stop the web dev server started by the runner.
# Discovery is cwd-based (any 'next' process whose working directory is our
# web/ dir) — reliable even when the recorded pid file went stale, and it can
# never match a web server from another project.
stop_web_dev() {
    local pid pgid stopped=0
    for pid in $(pgrep -f "next dev|next-server|next/dist/bin/next" 2>/dev/null); do
        [ "$(readlink "/proc/$pid/cwd" 2>/dev/null)" = "$MYFARMAI_ROOT/web" ] || continue
        pgid="$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' ')"
        if [ -n "$pgid" ] && [ "$pgid" != "$$" ]; then
            kill -- -"$pgid" 2>/dev/null && stopped=1
        fi
    done
    if [ "$stopped" = 1 ]; then
        sleep 1
        # Force-kill any survivors of the same groups.
        for pid in $(pgrep -f "next dev|next-server|next/dist/bin/next" 2>/dev/null); do
            [ "$(readlink "/proc/$pid/cwd" 2>/dev/null)" = "$MYFARMAI_ROOT/web" ] || continue
            kill -9 "$pid" 2>/dev/null || true
        done
        ok "Stopped web dev server (cwd-verified)."
    fi
    rm -f "$WEB_PID_FILE"
}

# Apply database migrations using the documented, verified command.
run_migrations() {
    local pwfile="$MYFARMAI_ROOT/backend/.pg_password"
    if [ ! -f "$pwfile" ]; then
        fail "backend/.pg_password missing — cannot connect to PostgreSQL."
        return 1
    fi
    local pw
    pw="$(cat "$pwfile")"
    $COMPOSE run --rm -e DATABASE_URL="postgresql+asyncpg://myfarmai:${pw}@postgres:5432/myfarmai" \
        backend .venv/bin/alembic upgrade head >>"$LOG_DIR/migrations.log" 2>&1
}

# AI verification (three honest tiers — no faking):
#   1. Backend container can reach host Ollama through the bridge.
#   2. The configured model performs REAL inference (host-side Ollama API).
#   3. Optional full end-to-end chat through the backend API when the owner
#      configures MYFARMAI_SMOKE_EMAIL / MYFARMAI_SMOKE_PASSWORD in .env
#      (chat is auth-gated since Phase 3 — see docs/runner-guide.md).
ai_smoke_test() {
    # Tier 1: connectivity from inside the backend container.
    if ! docker exec myfarmai-backend .venv/bin/python -c \
        "import urllib.request; urllib.request.urlopen('http://host.docker.internal:11434/api/tags', timeout=8)" \
        >/dev/null 2>&1; then
        printf 'tier1: backend container cannot reach host Ollama (bridge)\n' >>"$LOG_DIR/ai-smoke.log"
        return 1
    fi
    # Tier 2: real inference (host side, same Ollama the backend uses).
    local model
    model="$(grep -E '^OLLAMA_MODEL=' "$MYFARMAI_ROOT/.env" 2>/dev/null | cut -d= -f2 | tr -d '\"')"
    model="${model:-qwen3:4b}"
    local resp
    resp="$(curl -s --max-time 120 http://127.0.0.1:11434/api/generate \
        -d "{\"model\":\"$model\",\"prompt\":\"Reply with exactly: OK\",\"stream\":false}" 2>/dev/null || true)"
    if ! printf '%s' "$resp" | grep -q '"response"'; then
        printf 'tier2: inference failed: %s\n' "$resp" >>"$LOG_DIR/ai-smoke.log"
        return 1
    fi
    # Tier 3 (optional): authenticated end-to-end chat via the backend API.
    local email pass
    email="$(grep -E '^MYFARMAI_SMOKE_EMAIL=' "$MYFARMAI_ROOT/.env" 2>/dev/null | cut -d= -f2 | tr -d '\"')"
    pass="$(grep -E '^MYFARMAI_SMOKE_PASSWORD=' "$MYFARMAI_ROOT/.env" 2>/dev/null | cut -d= -f2 | tr -d '\"')"
    if [ -n "$email" ] && [ -n "$pass" ]; then
        resp="$(curl -s --max-time 120 -c /tmp/opencode/smoke_cookies -X POST http://127.0.0.1:8000/api/v1/auth/login \
            -H 'Content-Type: application/json' \
            -d "{\"email\":\"$email\",\"password\":\"$pass\"}" 2>/dev/null || true)"
        if printf '%s' "$resp" | grep -q '"user"'; then
            resp="$(curl -s --max-time 120 -b /tmp/opencode/smoke_cookies -X POST http://127.0.0.1:8000/api/v1/chat \
                -H 'Content-Type: application/json' \
                -d '{"message":"Reply with exactly: OK","language":"en"}' 2>/dev/null || true)"
            rm -f /tmp/opencode/smoke_cookies
            if ! printf '%s' "$resp" | grep -q '"response"'; then
                printf 'tier3: chat failed: %s\n' "$resp" >>"$LOG_DIR/ai-smoke.log"
                return 1
            fi
        else
            printf 'tier3: smoke login failed (check MYFARMAI_SMOKE_EMAIL/PASSWORD): %s\n' "$resp" >>"$LOG_DIR/ai-smoke.log"
            return 1
        fi
    fi
    return 0
}

# Compose project guard: operate only on this directory's project.
compose_ps() { $COMPOSE ps "$@" 2>/dev/null; }
