# MyFarmAI Maintenance Report - Wed Oct 21 10:32:06 AM IST 2026

## 1. Git Status
 M .gitignore
 M backend/app/main.py
 M backend/requirements.txt
 M docker-compose.yml
?? .agents/
?? .env.example
?? .omo/
?? .opencode/
?? .pre-commit-config.yaml
?? AGENTS.md
?? CHANGELOG.md
?? CONTRIBUTING.md
?? README.md
?? REPOSITORY_AUDIT.md
?? SECURITY.md
?? android/
?? backend/app/__init__.py
?? backend/app/api/
?? backend/app/core/
?? backend/app/db/
?? backend/app/middleware/
?? backend/app/schemas/
?? backend/app/services/
?? backend/data/
?? backend/mypy.ini
?? backend/pytest.ini
?? backend/ruff.toml
?? backend/tests/
?? docs/
?? graphify-out/
?? infra/
?? maintenance-report-20261021-103206.md
?? opencode.json
?? scripts/
?? skills-lock.json
?? web/

## 2. Secret Exposure Check
✅ No obvious secrets in source

## 3. Web Frontend
### TypeScript

> myfarmai-web@1.0.0 typecheck
> tsc --noEmit


### Lint

> myfarmai-web@1.0.0 lint
> next lint

`next lint` is deprecated and will be removed in Next.js 16.
For new projects, use create-next-app to choose your preferred linter.
For existing projects, migrate to the ESLint CLI:
npx @next/codemod@canary next-lint-to-eslint-cli .

✔ No ESLint warnings or errors

### Tests

> myfarmai-web@1.0.0 test
> jest --runInBand


Test Suites: 4 passed, 4 total
Tests:       19 passed, 19 total
Snapshots:   0 total
Time:        3.289 s, estimated 8 s
Ran all test suites.

## 4. Android App
### TypeScript

> myfarmai-android@1.0.0 typecheck
> tsc --noEmit

sh: 1: tsc: not found

### Lint

> myfarmai-android@1.0.0 lint
> eslint . --ext .ts,.tsx

sh: 1: eslint: not found

## 5. Backend
### Type Check (mypy)
/usr/bin/python: No module named mypy

### Lint (ruff)
/usr/bin/python: No module named ruff

### Tests
/usr/bin/python: No module named pytest

## 6. Docker Compose
name: myfarmai
services:
  backend:
    build:
      context: /data/MyFarmAI/backend
      dockerfile: Dockerfile
    container_name: myfarmai-backend
    depends_on:
      voice:
        condition: service_started
        required: true
    network_mode: host
    restart: unless-stopped
    volumes:
      - type: bind
        source: /data/MyFarmAI/data
        target: /app/data
        bind: {}
      - type: bind
        source: /data/MyFarmAI/.env
        target: /app/.env
        read_only: true
        bind: {}
  voice:
    build:
      context: /data/MyFarmAI/ai/voice
      dockerfile: Dockerfile
    container_name: myfarmai-voice
    networks:
      default: null
    ports:
      - mode: ingress
        target: 8001
        published: "8001"
        protocol: tcp
    restart: unless-stopped
networks:
  default:
    name: myfarmai_default

## 7. Knowledge Graph
Re-extracting code files in . (no LLM needed)...
[graphify watch] 73 file(s) not classified (no supported extension or shebang), skipped: .env.example, .gitignore, .gitkeep, ChatInterface.tsx.bak, Dockerfile, Dockerfile.nodejs (+67 more)
  AST extraction: 100/104 uncached files (96%) [8 workers]
  AST extraction: 104/104 uncached files (100%) [8 workers]
  warning: 21 code file(s) yielded no symbols (0.01 MB) — a data file, or source this extractor models no symbols for: .agents/skills/docker-build-strategies/assets/Dockerfile.go, android/src/theme/index.ts, android/src/types/index.ts, backend/app/api/v1/__init__.py, backend/app/api/v1/router.py (+16 more)
[graphify watch] community set changed since labeling (0 saved labels, 273 communities now; renamed 36 community(ies) by their hub). Run `graphify label` to refresh names with the LLM.
[graphify watch] Rebuilt: 4172 nodes, 5821 edges, 273 communities
[graphify watch] graph.json, graph.html and GRAPH_REPORT.md updated in graphify-out
Code graph updated. For doc/paper/image changes run /graphify --update in your AI assistant.
Tip: set GEMINI_API_KEY or GOOGLE_API_KEY to use Gemini for semantic extraction.

## 8. Documentation
Checking links in /data/MyFarmAI/docs/frontend/FRONTEND_AGENTS.md
Checking links in /data/MyFarmAI/docs/frontend/INTERACTION_GUIDELINES.md
Checking links in /data/MyFarmAI/docs/frontend/COLOR_SYSTEM.md
Checking links in /data/MyFarmAI/docs/frontend/DESIGN_SYSTEM.md
Checking links in /data/MyFarmAI/docs/backend/DEVELOPMENT_SETUP.md

