#!/usr/bin/env bash
# Local quality gate - runs all checks for the backend
# Usage: ./scripts/check.sh

set -euo pipefail

cd "$(dirname "$0")/../backend"

echo "=== Running Ruff format check ==="
uv run ruff format --check app tests

echo "=== Running Ruff lint check ==="
uv run ruff check app tests

echo "=== Running MyPy type check ==="
uv run mypy app

echo "=== Running tests ==="
uv run pytest -q

echo "=== All checks passed! ==="