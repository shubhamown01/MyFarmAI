# Current-State Repository Audit

**Phase:** 0 — read-only  
**Date:** 2026-10-21  
**Repository:** `/data/MyFarmAI`  
**Branch / commit:** `main` / `3cd1a6e`  
**Related:** [`DEPENDENCY_INVENTORY.md`](DEPENDENCY_INVENTORY.md), [`API_CONTRACT_INVENTORY.md`](API_CONTRACT_INVENTORY.md), [`DATABASE_ASSESSMENT.md`](DATABASE_ASSESSMENT.md)

---

## 1. Repository state

### 1.1 Git

| Item | Finding | Evidence | Classification |
|---|---|---|---|
| Work tree root | `/data/MyFarmAI` | `git rev-parse --show-toplevel` | Verified |
| Branch | `main` | `git status --short --branch` | Verified |
| History | Single commit `3cd1a6e chore: initialize My Farm AI foundation` | `git log -5 --oneline` | Verified |
| Remote | None configured | `git remote -v` (empty) | Verified |
| Uncommitted/untracked work | 4 modified files and a large untracked tree | `git status` | Verified |
| Modification risk | Backend feature code, tests, docs, clients, and infrastructure are not committed | `git status` | Risk |
| Backup | No remote and no verified backup | Git state | Risk |

The working tree contains substantial pre-existing user work. This audit did not stage, commit, revert, clean, or reformat any of it.

### 1.2 Top-level layout

```text
/data/MyFarmAI
├── backend/        FastAPI service, SQLite code, tests, Dockerfile
├── ai/voice/       Separate faster-whisper HTTP service
├── web/            Next.js 15 dashboard/client
├── android/        Expo / React Native client
├── infra/searxng/  Self-hosted SearXNG configuration + cache
├── docs/           Backend, frontend, integration, and roadmap docs
├── data/           Docker-mounted SQLite database
├── scripts/        Maintenance script
├── graphify-out/   Generated code graph
├── docker-compose.yml
├── .env            Local environment (ignored, world-group readable)
└── .env.example    Template (untracked)
```

## 2. Backend application

### 2.1 Runtime and framework

| Item | Finding | Evidence | Classification |
|---|---|---|---|
| Framework | FastAPI | `backend/app/main.py:5`, `backend/requirements.txt` | Verified |
| Language | Python | `backend/app/**/*.py` | Verified |
| Local interpreter | Python 3.14.4 | `backend/.venv/bin/python --version` | Verified |
| Container interpreter | `python:3.12-slim` (floating tag) | `backend/Dockerfile:1` | Verified |
| Dependency manager | `pip` + unpinned `requirements.txt`; no `pyproject.toml`, no `uv.lock` | `backend/requirements.txt` | Verified |
| ASGI server | Uvicorn | `backend/Dockerfile:13` | Verified |
| App entry point | `app.main:app` | `backend/Dockerfile:13` | Verified |
| Settings | Pydantic Settings, `.env` driven | `backend/app/core/config.py:5-88` | Verified |
| API versioning | `/api/v1` router prefix | `backend/app/api/v1/router.py:8` | Verified |

The local interpreter (3.14.4) does not match the container interpreter (3.12). `mypy.ini` targets 3.12 (`backend/mypy.ini:2`). This is a reproducibility risk, not a runtime failure observed in this audit.

### 2.2 Application composition

| Component | Responsibility | Evidence |
|---|---|---|
| `main.py` | FastAPI app, lifespan, CORS, rate limit, request ID/logging, `/`, `/health`, router include | `backend/app/main.py:36-111` |
| `api/v1/router.py` | Aggregates health, chat, weather, resources | `backend/app/api/v1/router.py:1-13` |
| `api/v1/*.py` | HTTP handlers, validation, error mapping | `backend/app/api/v1/` |
| `services/ollama.py` | Async Ollama HTTP adapter | `backend/app/services/ollama.py:6-82` |
| `services/chat.py` | Prompt construction, history, persistence orchestration | `backend/app/services/chat.py:15-78` |
| `services/weather.py` | Open-Meteo client and WMO code mapping | `backend/app/services/weather.py:37-157` |
| `services/resources.py` | Static catalogue of 12 Indian agricultural links | `backend/app/services/resources.py:3-112` |
| `db/connection.py` | SQLite connections and startup DDL | `backend/app/db/connection.py:18-63` |
| `db/conversations.py` | Conversation/message queries | `backend/app/db/conversations.py:6-97` |
| `schemas/*.py` | Pydantic request/response models | `backend/app/schemas/` |
| `middleware/rate_limit.py` | Per-IP in-memory fixed window | `backend/app/middleware/rate_limit.py:9-65` |

**Boundaries:** route handlers call services; services call the database and Ollama; there is no repository/ORM abstraction. Business logic is mostly in services, but chat persistence and prompt history are tightly coupled in `services/chat.py`.

### 2.3 Lifespan and startup

`backend/app/main.py:22-33`:

1. Logs startup.
2. Calls `validate_settings_or_exit()`; invalid critical settings call `sys.exit(1)`.
3. Imports and runs `init_db()` — executes `CREATE TABLE IF NOT EXISTS` at every startup.
4. On shutdown, closes Ollama and weather HTTP clients.

There is no readiness check for the database or Ollama. A failed database initialization aborts startup, but `/health` itself never checks dependencies.

## 3. API surface

Nine backend routes and two voice-service routes exist. Full schemas and consumers are in [`API_CONTRACT_INVENTORY.md`](API_CONTRACT_INVENTORY.md).

| Method | Path | Purpose | Auth |
|---|---|---|---|
| GET | `/` | Project/version/status | None |
| GET | `/health` | Liveness-style health | None |
| GET | `/api/v1/health` | Versioned health | None |
| POST | `/api/v1/chat` | Chat with Ollama, persist conversation | None |
| GET | `/api/v1/weather` | Current + 7-day Open-Meteo forecast | None |
| GET | `/api/v1/weather/current` | Current weather only | None |
| GET | `/api/v1/resources` | Static resource catalogue, optional category filter | None |
| GET | `/api/v1/resources/categories` | Category list | None |
| GET | `/api/v1/resources/{category}` | Resources by category | None |
| GET | `:8001/health` | Voice liveness | None |
| POST | `:8001/transcribe` | Whisper speech-to-text (Hindi) | None |

**Versioning:** only chat/weather/resources are under `/api/v1`; `/` and `/health` are unversioned. The voice service is unversioned and separately exposed.

## 4. Client integration points

### 4.1 Web (Next.js 15)

- API base: `NEXT_PUBLIC_API_BASE_URL`, default `/api/v1` (`web/src/lib/api/client.ts:3`).
- Next.js rewrite proxies `/api/v1/:path*` to `NEXT_PUBLIC_API_BASE_URL` (`web/next.config.js:4-10`).
- Calls: chat, weather, current weather, resources, categories, resources-by-category, health (`web/src/lib/api/client.ts:79-131`).
- Chat history is persisted in `sessionStorage` (max 60 messages), not server-side retrieval (`web/src/hooks/useChat.ts:8-105`).
- Profile (name, location label, coordinates) is stored in `localStorage` with a hardcoded default profile (`web/src/hooks/useProfile.ts:5-70`).
- Web chat sends only `location` from the profile (`web/src/components/Chat/ChatInterface.tsx:40`); language defaults to `en` and crop is unset.

### 4.2 Android (Expo / React Native 51)

- Endpoint constants are relative (`android/src/config/api.ts:1-8`).
- A base URL is computed and exported (`android/src/config/api.ts:10-18`) but **never used** by the client.
- `android/src/lib/api/client.ts:29` calls `fetch(endpoint)` directly, so requests are relative URLs such as `/api/v1/chat`. React Native `fetch` requires an absolute URL; this is a verified integration blocker.
- `android/.env.example` documents `EXPO_PUBLIC_API_BASE_URL`, but no code reads it.
- Android chat sends `language: 'hi'` and a weather-derived location (`android/src/components/ChatInterface.tsx:44-47`, `65-68`).
- Conversation cache uses `expo-secure-store` and keeps 50 conversations (`android/src/storage/conversations.ts:1-31`).

### 4.3 Voice

The voice service is standalone on port 8001. The backend has a `voice_service_url` setting (`backend/app/core/config.py:46-50`) but no code uses it; no backend route proxies transcription. `docker-compose.yml` nevertheless makes the backend depend on the voice container.

## 5. Database and persistence

| Item | Finding | Evidence |
|---|---|---|
| Engine | SQLite 3.46.1 via Python stdlib; async wrapper `aiosqlite==0.22.1` | Interpreter query; `backend/requirements.txt` |
| ORM | None; raw SQL | `backend/app/db/*.py` |
| Migration tool | None; startup DDL only | `backend/app/db/connection.py:26-63` |
| Tables | `conversations`, `messages`, `sqlite_sequence` | Schema inspection |
| Production-like DB | `data/app.db` (Docker bind mount) — 35 conversations / 74 messages | File inspection |
| Local-dev DB | `backend/data/app.db` — 122 conversations / 315 messages | File inspection |
| Integrity | `PRAGMA integrity_check` = `ok` for both | Read-only query |
| Foreign keys | Declared on `messages.conversation_id`, but `PRAGMA foreign_keys` is not enabled per connection | `connection.py:18-23`; SQLite default is off |
| Indexes | Only `idx_messages_conversation_id` | Schema inspection |
| Backups | None found | Repository search |
| Tests | Chat tests write to the configured app DB when the app schema exists; no per-test app DB override | `backend/tests/conftest.py`, `backend/tests/test_chat.py` |

Full analysis and migration implications: [`DATABASE_ASSESSMENT.md`](DATABASE_ASSESSMENT.md).

## 6. Authentication and authorization

**Verified:** no authentication or authorization code exists. No login, user, session, token, API-key, or ownership model is present. All endpoints are public. Conversation rows have no user/farm identifier (`backend/app/db/connection.py:31-54`). Conversation IDs are UUIDv4 generated server-side (`backend/app/db/conversations.py:12`), so they are unguessable in practice, but possession of an ID is the only access control for continuing a chat. There is no endpoint to read a conversation by ID, which limits — but does not eliminate — exposure.

`docs/backend/AUTH_ASSESSMENT.md` documents the gap and recommends API keys for private deployment and OIDC/JWT for public launch. That document is a proposal, not an implementation.

## 7. AI, search, and research

| Capability | Current state | Evidence |
|---|---|---|
| Chat inference | Local Ollama HTTP API, model `qwen3:4b` | `backend/app/services/ollama.py`, `backend/app/core/config.py:10-22` |
| Model provider independence | None; one concrete `OllamaClient` | `backend/app/services/ollama.py` |
| Prompt/template management | One Python string template; no versioning | `backend/app/services/chat.py:15-34` |
| Embeddings | No application use; `qwen3-embedding:0.6b` is present in Ollama | `ollama list` |
| Vector search | None | Repository search |
| Web search | SearXNG container running on `127.0.0.1:8890`; no backend client | `docker ps`, `infra/searxng/` |
| Page fetching/crawling | None | Repository search |
| Research citations | None | Repository search |
| Prompt-injection defenses | System prompt only; no input/output policy enforcement | `backend/app/services/chat.py:15-34` |

## 8. Background work, uploads, storage, notifications

| Area | Finding | Evidence |
|---|---|---|
| Queues/workers | None | Repository search |
| Scheduled jobs | None | Repository search |
| Notifications/email/SMS | None | Repository search |
| Object storage | None | Repository search |
| Document processing | None | Repository search |
| File uploads | Voice `/transcribe` accepts `UploadFile` with no size/type limit | `ai/voice/main.py:18-53` |
| Temp files | Written to container temp dir with filename-derived suffix, deleted in `finally` | `ai/voice/main.py:20-53` |

## 9. Containers and deployment

### 9.1 Backend image

`backend/Dockerfile`:
- `python:3.12-slim`, floating tag.
- Installs unpinned `requirements.txt`.
- Copies only `app/`; no `.dockerignore`.
- Runs as root (no `USER`).
- Exposes 8000, no `HEALTHCHECK`.
- No pinned digests, no build metadata.

### 9.2 Compose

`docker-compose.yml`:
- `voice`: builds `ai/voice`, publishes `8001:8001` on all interfaces, no healthcheck, no resource limit, no read-only filesystem.
- `backend`: builds `backend`, uses `network_mode: "host"`, bind-mounts `./data` to `/app/data` and `./.env` to `/app/.env:ro`, `depends_on: voice`, no healthcheck, no limits.
- No PostgreSQL, Ollama, SearXNG, reverse proxy, or CI service is defined in this Compose file.
- `docker compose config` validates the current file.

### 9.3 Running host state (not necessarily MyFarmAI)

At audit time, Docker was running 17 containers, including unrelated Langfuse and Sentinel stacks, plus `myfarmai-voice` and `myfarmai-searxng`. The backend container was not running. This matters for resource assessment; it is not a claim that all containers belong to MyFarmAI.

### 9.4 Volumes and data locations

- Compose database: `/data/MyFarmAI/data/app.db` (bind mount).
- Local development database: `/data/MyFarmAI/backend/data/app.db`.
- Ollama models: `/data/SentinelAI/ollama/models` (44 GB, shared with another project).
- Docker root: `/var/lib/docker` on `/` (126 GB, 96% used; 16.39 GB images, 23.84 GB volumes).
- SearXNG cache: `/data/MyFarmAI/infra/searxng/data` (small at audit time).

## 10. Tests, quality, CI, and documentation

| Area | Finding | Evidence |
|---|---|---|
| Backend tests | 56 tests across 6 files; 49 pass / 7 fail against a clean DB | `backend/tests/`; `VERIFICATION_REPORT.md` |
| Test isolation | Chat tests rely on the app's default DB being pre-initialized | `conftest.py:42-64`; test run |
| Ruff | Passes on `app` and `tests` | `ruff check app tests` |
| mypy | Reports no issues, but emits a config warning: duplicate `[tool.mypy.overrides]` in an INI file | `backend/mypy.ini`; run output |
| Pre-commit | Config exists; hook paths assume repo-root `.venv` and `mypy.ini` at root, which do not exist | `.pre-commit-config.yaml` |
| CI | No `.github/workflows` or equivalent | Filesystem inspection |
| Web tests | 19 Jest tests passed in a prior maintenance report; not re-run in this audit | `maintenance-report-20261021-103253.md` |
| Android checks | Prior maintenance report shows typecheck/lint failure due missing local binaries and wrong `npx` packages | Same report |
| API spec | No committed OpenAPI JSON/YAML; FastAPI can generate it at runtime | Repository search |
| Documentation | Existing backend docs are partly stale: they describe no DB/chat/weather and a 404 `/health`, while current code implements them | `docs/backend/BACKEND_AUDIT.md`, `docs/backend/ARCHITECTURE.md`, `docs/backend/API.md` |
| Duplicate roadmap | `docs/backend/ROADMAP.md` (milestone status) and `docs/roadmaps/MyFarmAI_Backend_Roadmap.md` (target roadmap) coexist | Docs tree |
| License | No `LICENSE` file; README “License” section is empty | Filesystem; `README.md:220` |

## 11. Documentation drift (verified examples)

| Existing document | Claim | Current evidence |
|---|---|---|
| `docs/backend/BACKEND_AUDIT.md` | “No database integration”, “No chat/conversation endpoints”, “No rate limiting” | `backend/app/db/`, `api/v1/chat.py`, `middleware/rate_limit.py` exist |
| `docs/backend/BACKEND_AUDIT.md` | `/health` is 404 | `backend/app/main.py:103-108` defines `/health` |
| `docs/backend/API.md` | Errors are flat `{detail, error_code}` | Handlers raise `HTTPException(detail={...})`, producing nested `{"detail":{"detail":...,"error_code":...}}` |
| `docs/backend/API.md` | Version `0.2.0` | `settings.app_version` defaults to `0.1.0` (`config.py:7`) |
| `docs/backend/ROADMAP.md` | 56/56 tests passing | Clean-DB run: 49 pass / 7 fail |
| `docs/backend/ARCHITECTURE.md` | Production should use a hosted LLM API | Conflicts with the roadmap’s no-paid-API requirement |

These should be corrected in Phase 1 (documentation-only change), not silently ignored.

## 12. Significant unknowns

| Unknown | Why it matters | How to resolve |
|---|---|---|
| Which SQLite file is authoritative | Data migration and user-data preservation | Owner decision; inspect app usage history; do not merge blindly |
| Whether either DB contains real user data | Privacy/retention obligations | Owner confirmation; data classification review |
| Firewall/external exposure of ports 8000/8001 | Severity of unauthenticated endpoints | Host firewall/network review by owner |
| Production deployment target | Auth, TLS, backup, compliance requirements | Product decision |
| Actual Ollama latency/RAM with `qwen3:4b` | Model feasibility on 7 GiB / 2 GiB VRAM | Controlled benchmark on an isolated profile |
| SearXNG engine terms and robots compliance | Research-engine legality | Per-engine terms review in Phase 6 |
| IMD/public weather data licensing | Open-Meteo alternative | Legal/terms review in Phase 5 |
| Project licence and AGPL obligations | Distribution/commercial model | Owner/legal decision |

## 13. Current-state conclusion

The repository is a working prototype, not a production backend. Its strongest parts are a clean FastAPI separation, Pydantic validation, parameterized SQL, local-only Ollama inference, and a useful static resource catalogue. Its production blockers are the absence of authentication, ownership, backups, migrations, hermetic tests, dependency pinning, and a licensed weather provider, plus an unsecured voice endpoint and a hardcoded search secret.

No code, configuration, dependency, database, or deployment state was modified during this audit.
