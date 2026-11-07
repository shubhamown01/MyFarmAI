#!/bin/bash
# MYFARMAI status dashboard — read-only. Never exposes credentials.
set -u
# shellcheck source=scripts/lib/myfarmai-common.sh
source "$(dirname "$0")/scripts/lib/myfarmai-common.sh"

echo "=============================================="
echo " MyFarmAI status — $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="

# Docker
if docker info >/dev/null 2>&1; then ok "Docker daemon running"; else fail "Docker daemon unreachable"; fi

# Compose services
echo "--- Compose services ---"
compose_ps
for svc in postgres backend; do
    name="myfarmai-$svc"
    state="$(docker inspect "$name" --format '{{.State.Status}}/{{if .State.Health}}{{.State.Health.Status}}{{else}}no-hc{{end}}' 2>/dev/null || echo "not created")"
    case "$state" in
        running/healthy) ok "$svc: $state" ;;
        not\ created)    warn "$svc: not created (run ./RUN_MYFARMAI.sh)" ;;
        *)               warn "$svc: $state" ;;
    esac
done

# HTTP endpoints
echo "--- Endpoints ---"
for entry in "backend-live|http://127.0.0.1:8000/health/live" "backend-ready|http://127.0.0.1:8000/health/ready" "frontend|http://127.0.0.1:3000"; do
    label="${entry%%|*}"; url="${entry#*|}"
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "$url" 2>/dev/null || true)"
    case "$code" in 2??|3??|401|403) ok "$label: HTTP $code" ;; *) fail "$label: unreachable (${code:-none})" ;; esac
done

# Ollama + model
MODEL="$(grep -E '^OLLAMA_MODEL=' "$MYFARMAI_ROOT/.env" 2>/dev/null | cut -d= -f2 | tr -d '\"')"
MODEL="${MODEL:-qwen3:4b}"
if curl -s --max-time 3 http://127.0.0.1:11434/api/tags 2>/dev/null | grep -q "\"name\":\"$MODEL\""; then
    ok "Ollama reachable; model '$MODEL' installed"
else
    fail "Ollama unreachable or model '$MODEL' missing"
fi

# Resources
echo "--- Resources ---"
df -h "$MYFARMAI_ROOT" | awk 'NR==2 {print "Disk " $6 ": " $3 " used, " $4 " free (" $5 ")"}'
free -h | awk '/^Mem:/ {print "Memory: " $3 " used / " $2 " total"}'

# Recent errors (compose + logs) — last few error lines only
echo "--- Recent errors (last 12 lines of matches) ---"
errs="$($COMPOSE logs --since 24h 2>/dev/null | grep -iE "error|traceback|exception" | tail -12)"
[ -z "$errs" ] && errs="(none in compose logs)"
printf '%s\n' "$errs"
for f in "$LOG_DIR/web-dev.log"; do
    [ -f "$f" ] && { grep -iE "error|failed" "$f" 2>/dev/null | tail -6; }
done
echo "=============================================="
echo "Logs: $LOG_DIR · Stop: ./STOP_MYFARMAI.sh · Restart: ./RESTART_MYFARMAI.sh"
