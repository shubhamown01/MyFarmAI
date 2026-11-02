#!/usr/bin/env bash
# Local quality gate - runs all checks for the backend
# Usage: ./scripts/check.sh

set -euo pipefail

cd "$(dirname "$0")/../backend"

echo "=== Running Ruff format check ==="
uv run ruff format --check app tests --exclude app/orchestrator

echo "=== Running Ruff lint check ==="
uv run ruff check app tests --exclude app/orchestrator

echo "=== Running MyPy type check (threshold gate) ==="
MYPY_OUTPUT="$(uv run mypy app --exclude app/orchestrator 2>&1)" || true
MYPY_COUNT="$(echo "$MYPY_OUTPUT" | grep -oE 'Found [0-9]+ error' | grep -oE '[0-9]+' | tail -1 || echo 0)"
MYPY_COUNT="${MYPY_COUNT:-0}"
MYPY_BASELINE=85
if [ "$MYPY_COUNT" -gt "$MYPY_BASELINE" ]; then
    echo "$MYPY_OUTPUT" | grep -E "error:" | head -40
    echo "mypy: $MYPY_COUNT errors exceed the pinned baseline of $MYPY_BASELINE" >&2
    exit 1
fi
echo "mypy: $MYPY_COUNT errors (baseline $MYPY_BASELINE — may not increase; fix errors in touched files)"

echo "=== Running tests ==="
uv run pytest -q

echo "=== All checks passed (pytest result above is authoritative) ==="