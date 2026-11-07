#!/bin/bash
# MYFARMAI restart — safe stop + full startup with health checks.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"

"$DIR/STOP_MYFARMAI.sh" || true
echo ""
exec "$DIR/RUN_MYFARMAI.sh" "$@"
