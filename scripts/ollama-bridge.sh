#!/bin/bash
# Forward the Docker bridge gateway :11434 -> host loopback :11434 so the
# MyFarmAI backend container can reach host-run Ollama (which binds 127.0.0.1).
# Installed via user crontab @reboot (rootless). Idempotent.
BRIDGE_IP="$(docker network inspect myfarmai_default --format '{{(index .IPAM.Config 0).Gateway}}' 2>/dev/null || true)"
[ -z "$BRIDGE_IP" ] && exit 0
if ! ss -tln 2>/dev/null | grep -q "$BRIDGE_IP:11434"; then
    setsid socat "TCP-LISTEN:11434,bind=$BRIDGE_IP,fork,reuseaddr" TCP:127.0.0.1:11434 \
        </dev/null >>/tmp/opencode/socat-ollama.log 2>&1 &
fi
