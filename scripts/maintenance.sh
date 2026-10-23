#!/usr/bin/env bash
# MyFarmAI Maintenance Workflow
# Run from repository root: ./scripts/maintenance.sh

set -euo pipefail

REPO_ROOT="/data/MyFarmAI"
REPORT_FILE="$REPO_ROOT/maintenance-report-$(date +%Y%m%d-%H%M%S).md"

echo "# MyFarmAI Maintenance Report - $(date)" > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 1. Git Hygiene
echo "## 1. Git Status" >> "$REPORT_FILE"
cd "$REPO_ROOT"
git status --short >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# 2. Check for Secrets (basic)
echo "## 2. Secret Exposure Check" >> "$REPORT_FILE"
if grep -r "api_key\|secret\|password\|token" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.json" --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.venv --exclude-dir=.next . 2>/dev/null | grep -v ".example" | grep -v "test" | head -20; then
    echo "⚠️ Potential secrets found" >> "$REPORT_FILE"
else
    echo "✅ No obvious secrets in source" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# 3. Web Frontend Checks
echo "## 3. Web Frontend" >> "$REPORT_FILE"
cd "$REPO_ROOT/web"
echo "### TypeScript" >> "$REPORT_FILE"
npm run typecheck 2>&1 | tail -20 >> "$REPORT_FILE" || true
echo "" >> "$REPORT_FILE"
echo "### Lint" >> "$REPORT_FILE"
npm run lint 2>&1 | tail -20 >> "$REPORT_FILE" || true
echo "" >> "$REPORT_FILE"
echo "### Tests" >> "$REPORT_FILE"
npm test -- --runInBand 2>&1 | tail -30 >> "$REPORT_FILE" || true
echo "" >> "$REPORT_FILE"

# 4. Android Checks
echo "## 4. Android App" >> "$REPORT_FILE"
cd "$REPO_ROOT/android"
echo "### TypeScript" >> "$REPORT_FILE"
./node_modules/.bin/tsc --noEmit 2>&1 | tail -20 >> "$REPORT_FILE" || true
echo "" >> "$REPORT_FILE"
echo "### Lint" >> "$REPORT_FILE"
./node_modules/.bin/eslint . --ext .ts,.tsx 2>&1 | tail -20 >> "$REPORT_FILE" || true
echo "" >> "$REPORT_FILE"

# 5. Backend Checks
echo "## 5. Backend" >> "$REPORT_FILE"
cd "$REPO_ROOT/backend"
echo "### Type Check (mypy)" >> "$REPORT_FILE"
.venv/bin/python -m mypy app 2>&1 | tail -20 >> "$REPORT_FILE" || true
echo "" >> "$REPORT_FILE"
echo "### Lint (ruff)" >> "$REPORT_FILE"
.venv/bin/python -m ruff check app 2>&1 | tail -20 >> "$REPORT_FILE" || true
echo "" >> "$REPORT_FILE"
echo "### Tests" >> "$REPORT_FILE"
.venv/bin/python -m pytest tests -v 2>&1 | tail -30 >> "$REPORT_FILE" || true
echo "" >> "$REPORT_FILE"

# 6. Docker Compose Validation
echo "## 6. Docker Compose" >> "$REPORT_FILE"
cd "$REPO_ROOT"
docker compose config 2>&1 >> "$REPORT_FILE" || true
echo "" >> "$REPORT_FILE"

# 7. Graphify Update
echo "## 7. Knowledge Graph" >> "$REPORT_FILE"
if command -v graphify &> /dev/null; then
    graphify update . 2>&1 | tail -10 >> "$REPORT_FILE" || true
else
    echo "graphify not installed" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# 8. Documentation Links Check
echo "## 8. Documentation" >> "$REPORT_FILE"
find "$REPO_ROOT/docs" -name "*.md" -exec grep -l "\[.*\](.*.md)" {} \; 2>/dev/null | while read file; do
    echo "Checking links in $file" >> "$REPORT_FILE"
done
echo "" >> "$REPORT_FILE"

echo "Report saved to: $REPORT_FILE"
cat "$REPORT_FILE"