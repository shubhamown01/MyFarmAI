#!/bin/bash
# Forward the Docker bridge gateway :11434 -> host loopback :11434 so the
# MyFarmAI backend container can reach host-run Ollama (which binds 127.0.0.1).
# Backend containers reach it as http://host.docker.internal:11434
# (extra_hosts: host-gateway == docker0 gateway). Idempotent, rootless.
set -u
BRIDGE_IP="$(docker network inspect bridge --format '{{(index .IPAM.Config 0).Gateway}}' 2>/dev/null || echo 172.17.0.1)"
[ -z "$BRIDGE_IP" ] && exit 0
if ! ss -tln 2>/dev/null | grep -q "$BRIDGE_IP:11434"; then
    mkdir -p /tmp/opencode
    setsid socat "TCP-LISTEN:11434,bind=$BRIDGE_IP,fork,reuseaddr" TCP:127.0.0.1:11434 \
        </dev/null >>/tmp/opencode/socat-ollama.log 2>&1 &
    echo "ollama-bridge: socat listening on $BRIDGE_IP:11434"
fi
