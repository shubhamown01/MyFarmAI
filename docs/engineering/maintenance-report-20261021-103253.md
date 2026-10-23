# MyFarmAI Maintenance Report - Wed Oct 21 10:32:53 AM IST 2026

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
?? maintenance-report-20261021-103253.md
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
Time:        2.04 s
Ran all test suites.

## 4. Android App
### TypeScript
npm warn exec The following package was not found and will be installed: tsc@2.0.4
npm warn deprecated tsc@2.0.4: Package no longer supported. Contact Support at https://www.npmjs.com/support for more info.

[41m                                                                               [0m
[41m[37m                This is not the tsc command you are looking for                [0m
[41m                                                                               [0m

To get access to the TypeScript compiler, [34mtsc[0m, from the command line either:

- Use [1mnpm install typescript[0m to first add TypeScript to your project [1mbefore[0m using npx
- Use [1myarn[0m to avoid accidentally running code from un-installed packages

### Lint
npm warn exec The following package was not found and will be installed: eslint@10.13.0

Oops! Something went wrong! :(

ESLint: 10.13.0

ESLint couldn't find an eslint.config.* file.

From ESLint v9.0.0, the default configuration file is now eslint.config.*.
If you are using a .eslintrc.* file, please follow the migration guide
to update your configuration file to the new format:

https://eslint.org/docs/latest/use/configure/migration-guide

If you still have problems after following the migration guide, please stop by
https://eslint.org/chat/help to chat with the team.


## 5. Backend
### Type Check (mypy)
mypy.ini: While reading from 'mypy.ini' [line 18]: section '[tool.mypy.overrides]' already exists
Success: no issues found in 26 source files

### Lint (ruff)
All checks passed!

### Tests
tests/test_schemas.py::TestChatRequest::test_valid_request_with_all_fields <- ../../../home/mrknight/MyFarmAI/backend/tests/test_schemas.py PASSED [ 62%]
tests/test_schemas.py::TestChatRequest::test_message_trimmed <- ../../../home/mrknight/MyFarmAI/backend/tests/test_schemas.py PASSED [ 64%]
tests/test_schemas.py::TestChatRequest::test_empty_message_rejected <- ../../../home/mrknight/MyFarmAI/backend/tests/test_schemas.py PASSED [ 66%]
tests/test_schemas.py::TestChatRequest::test_whitespace_only_rejected <- ../../../home/mrknight/MyFarmAI/backend/tests/test_schemas.py PASSED [ 67%]
tests/test_schemas.py::TestChatRequest::test_message_too_long_rejected <- ../../../home/mrknight/MyFarmAI/backend/tests/test_schemas.py PASSED [ 69%]
tests/test_schemas.py::TestChatRequest::test_invalid_language_rejected <- ../../../home/mrknight/MyFarmAI/backend/tests/test_schemas.py PASSED [ 71%]
tests/test_schemas.py::TestChatRequest::test_valid_language_accepted <- ../../../home/mrknight/MyFarmAI/backend/tests/test_schemas.py PASSED [ 73%]
tests/test_schemas.py::TestChatRequest::test_crop_too_long_rejected <- ../../../home/mrknight/MyFarmAI/backend/tests/test_schemas.py PASSED [ 75%]
tests/test_schemas.py::TestChatRequest::test_location_too_long_rejected <- ../../../home/mrknight/MyFarmAI/backend/tests/test_schemas.py PASSED [ 76%]
tests/test_schemas.py::TestChatResponse::test_valid_response <- ../../../home/mrknight/MyFarmAI/backend/tests/test_schemas.py PASSED [ 78%]
tests/test_schemas.py::TestErrorResponse::test_valid_error <- ../../../home/mrknight/MyFarmAI/backend/tests/test_schemas.py PASSED [ 80%]
tests/test_schemas.py::TestErrorResponse::test_error_without_code <- ../../../home/mrknight/MyFarmAI/backend/tests/test_schemas.py PASSED [ 82%]
tests/test_weather.py::TestWeatherEndpoint::test_weather_valid_coordinates <- ../../../home/mrknight/MyFarmAI/backend/tests/test_weather.py PASSED [ 83%]
tests/test_weather.py::TestWeatherEndpoint::test_weather_only_current <- ../../../home/mrknight/MyFarmAI/backend/tests/test_weather.py PASSED [ 85%]
tests/test_weather.py::TestWeatherEndpoint::test_weather_only_daily <- ../../../home/mrknight/MyFarmAI/backend/tests/test_weather.py PASSED [ 87%]
tests/test_weather.py::TestWeatherEndpoint::test_weather_invalid_latitude <- ../../../home/mrknight/MyFarmAI/backend/tests/test_weather.py PASSED [ 89%]
tests/test_weather.py::TestWeatherEndpoint::test_weather_invalid_longitude <- ../../../home/mrknight/MyFarmAI/backend/tests/test_weather.py PASSED [ 91%]
tests/test_weather.py::TestWeatherEndpoint::test_weather_connection_error <- ../../../home/mrknight/MyFarmAI/backend/tests/test_weather.py PASSED [ 92%]
tests/test_weather.py::TestWeatherEndpoint::test_weather_timeout <- ../../../home/mrknight/MyFarmAI/backend/tests/test_weather.py PASSED [ 94%]
tests/test_weather.py::TestWeatherEndpoint::test_weather_boundary_latitudes <- ../../../home/mrknight/MyFarmAI/backend/tests/test_weather.py PASSED [ 96%]
tests/test_weather.py::TestWeatherEndpoint::test_weather_boundary_longitudes <- ../../../home/mrknight/MyFarmAI/backend/tests/test_weather.py PASSED [ 98%]
tests/test_weather.py::TestWeatherEndpoint::test_current_weather_endpoint <- ../../../home/mrknight/MyFarmAI/backend/tests/test_weather.py PASSED [100%]

=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /data/MyFarmAI/backend/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 56 passed, 1 warning in 6.29s =========================

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
  AST extraction: 99/99 uncached files (100%) [8 workers]
  warning: 21 code file(s) yielded no symbols (0.01 MB) — a data file, or source this extractor models no symbols for: .agents/skills/docker-build-strategies/assets/Dockerfile.go, android/src/theme/index.ts, android/src/types/index.ts, backend/app/api/v1/__init__.py, backend/app/api/v1/router.py (+16 more)
[graphify watch] community set changed since labeling (0 saved labels, 271 communities now; renamed 18 community(ies) by their hub). Run `graphify label` to refresh names with the LLM.
[graphify watch] Rebuilt: 4190 nodes, 5838 edges, 271 communities
[graphify watch] graph.json, graph.html and GRAPH_REPORT.md updated in graphify-out
Code graph updated. For doc/paper/image changes run /graphify --update in your AI assistant.
Tip: set GEMINI_API_KEY or GOOGLE_API_KEY to use Gemini for semantic extraction.

## 8. Documentation
Checking links in /data/MyFarmAI/docs/frontend/FRONTEND_AGENTS.md
Checking links in /data/MyFarmAI/docs/frontend/INTERACTION_GUIDELINES.md
Checking links in /data/MyFarmAI/docs/frontend/COLOR_SYSTEM.md
Checking links in /data/MyFarmAI/docs/frontend/DESIGN_SYSTEM.md
Checking links in /data/MyFarmAI/docs/backend/DEVELOPMENT_SETUP.md

