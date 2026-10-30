#!/usr/bin/env bash
# Local quality gate - runs all checks for the backend
# Usage: ./scripts/check.sh

set -euo pipefail

cd "$(dirname "$0")/../backend"

echo "=== Running Ruff format check ==="
uv run ruff format --check app tests --exclude app/orchestrator

echo "=== Running Ruff lint check ==="
uv run ruff check app tests --exclude app/orchestrator

echo "=== Running MyPy type check (non-blocking) ==="
uv run mypy app --exclude app/orchestrator || true

echo "=== Running tests ==="
uv run pytest -q

echo "=== All checks passed! ==="