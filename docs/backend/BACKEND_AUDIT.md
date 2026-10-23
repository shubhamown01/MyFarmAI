# MyFarm AI — Backend Audit

**Date:** 2026-10-18
**Branch:** `main` (commit `3cd1a6e` + working tree changes)
**Auditor:** Sisyphus (OpenCode)

---

## 1. Actual File Inventory

### Backend Structure (`backend/`)

```
backend/
├── Dockerfile                 # python:3.12-slim, installs requirements, runs uvicorn
├── requirements.txt           # fastapi, uvicorn[standard], httpx, python-multipart, pydantic-settings
└── app/
    ├── __init__.py            # NEW (untracked)
    ├── main.py                # FastAPI app with / and /api/v1/* routes
    ├── core/
    │   ├── __init__.py        # NEW (untracked)
    │   └── config.py          # Pydantic Settings from .env
    └── api/
        ├── __init__.py        # NEW (untracked)
        └── v1/
            ├── __init__.py    # NEW (untracked)
            ├── router.py      # APIRouter(prefix="/api/v1") includes health_router
            └── health.py      # GET /health -> {"status":"ok","service":"backend"}
```

### Voice Service (`ai/voice/`)

```
ai/voice/
├── Dockerfile                 # python:3.12-slim + ffmpeg/libsndfile1
├── requirements.txt           # faster-whisper, fastapi, uvicorn[standard], python-multipart
└── main.py                    # FastAPI with /health and POST /transcribe (Whisper "small", CPU, int8, Hindi)
```

### Docker Compose (`docker-compose.yml`)

```yaml
services:
  voice:
    build: ./ai/voice
    ports: ["8001:8001"]
    restart: unless-stopped

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [voice]
    restart: unless-stopped
```

### Documentation (`docs/`)
- Directory exists but **completely empty**

### Tests
- **None** — no `test_*.py`, `pytest.ini`, `conftest.py`

### Data (`data/`)
- Empty except `.gitkeep`

### Git Status
- **Branch:** `main`
- **Modified:** `backend/app/main.py`, `backend/requirements.txt`
- **Untracked:** `backend/app/__init__.py`, `backend/app/api/`, `backend/app/core/`

---

## 2. Existing Architecture and Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXTERNAL CLIENTS                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER COMPOSE NETWORK                        │
│  ┌─────────────────────┐    ┌─────────────────────────────┐    │
│  │   BACKEND :8000     │    │    VOICE SERVICE :8001      │    │
│  │   (FastAPI)         │    │    (FastAPI + Whisper)      │    │
│  │   GET /             │    │    GET /health              │    │
│  │   GET /api/v1/health│    │    POST /transcribe         │    │
│  │   (future: /api/v1/*)           (Hindi STT only)       │    │
│  └──────────┬──────────┘    └─────────────────────────────┘    │
│             │                                                  │
│             │ (future: HTTP calls to voice service)            │
│             ▼                                                  │
│  ┌─────────────────────┐                                        │
│  │   OLLAMA :11434     │  ← External, not in docker-compose    │
│  │   (Local LLM)       │                                        │
│  └─────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────┘
```

### Request Flow (Current)
1. Client → `GET http://localhost:8000/` → Returns project info
2. Client → `GET http://localhost:8000/api/v1/health` → Returns `{"status":"ok","service":"backend"}`
3. Client → `GET http://localhost:8001/health` → Returns `{"service":"voice","status":"ok"}`
4. Client → `POST http://localhost:8001/transcribe` → Audio file → Whisper "small" → Hindi text

### Missing Components
- No database integration
- No Ollama/LLM integration in backend
- No chat/conversation endpoints
- No authentication
- No rate limiting
- No CORS configuration

---

## 3. Working and Broken Endpoints

| Endpoint | Method | Status | Evidence |
|----------|--------|--------|----------|
| `/` | GET | ✅ **Working** | `{"project":"My Farm AI","version":"0.1.0","status":"running"}` |
| `/health` | GET | ❌ **404 Not Found** | Route exists at `/api/v1/health` due to router prefix |
| `/api/v1/health` | GET | ✅ **Working** | `{"status":"ok","service":"backend"}` |
| `/api/v1/*` (other) | - | ❌ **Not Implemented** | Only health router registered |
| Voice `/health` | GET | ✅ **Working** | `{"service":"voice","status":"ok"}` |
| Voice `/transcribe` | POST | ✅ **Working** | Accepts audio, returns Hindi transcription |

### Health Endpoint Diagnosis
**Root Cause:** The health route in `backend/app/api/v1/health.py` is defined at `/health` but included in `router.py` with `prefix="/api/v1"`, making the full path `/api/v1/health`.

**Recommended Fix (Option A):** Add root-level `/health` in `main.py` that returns equivalent payload.

---

## 4. Existing Dependencies and Integrations

### Backend (`backend/requirements.txt`)
| Package | Version (latest) | Purpose |
|---------|------------------|---------|
| fastapi | 0.115+ | Web framework |
| uvicorn[standard] | 0.34+ | ASGI server |
| httpx | 0.28+ | Async HTTP client |
| python-multipart | 0.0.20+ | Form data parsing |
| pydantic-settings | 2.10+ | Config from .env |

### Voice Service (`ai/voice/requirements.txt`)
| Package | Purpose |
|---------|---------|
| faster-whisper | STT (Whisper "small", CPU, int8) |
| fastapi | Web framework |
| uvicorn[standard] | ASGI server |
| python-multipart | File upload handling |

### Missing Dependencies (Needed for Milestone 1)
- `aiosqlite` — Async SQLite for conversation persistence
- `pytest` + `pytest-asyncio` — Testing
- `ruff` — Linting/formatting
- `mypy` — Type checking

---

## 5. Existing Database and Ollama Status

### Database
- **None** — No SQLAlchemy, Alembic, database models, migrations, or connection code
- Docker Compose has no database service
- `data/` directory exists but empty

### Ollama
- **Running externally** on port 11434 (not in Docker Compose)
- **Available Models:** 14 models installed
- **Primary Candidate:** `qwen3:4b` (2.5 GB, Q4_K_M, 262K context, Apache 2.0)
- **Embedding Models:** `qwen3-embedding:0.6b` (639 MB), `qwen3-embedding:4b` (2.5 GB)
- **No backend integration yet** — no Ollama client, no model management, no inference endpoints

### Ollama Networking Note
- Ollama runs on host `localhost:11434`
- Inside Docker containers, `localhost` refers to the container itself
- **Correct endpoint for backend container:** `http://host.docker.internal:11434` (Docker Desktop) or host IP
- Must be configurable via environment variable

---

## 6. Missing Features and Risks

### Missing Features (Priority Order)
1. **Chat endpoint** — `POST /api/v1/chat` with Ollama integration
2. **SQLite conversation persistence** — Conversations and messages tables
3. **Ollama client service** — Configurable HTTPX client with timeouts, retries
4. **Request/Response schemas** — Pydantic models for validation
5. **Error handling** — Structured error responses, no stack traces
6. **Tests** — Unit tests with mocked Ollama, integration tests
7. **Documentation** — API reference, setup guide, architecture
8. **CORS configuration** — For future web/mobile clients
9. **Environment template** — `.env.example` with all config keys

### Risks
| Risk | Severity | Mitigation |
|------|----------|------------|
| Ollama on host not reachable from container | HIGH | Document `host.docker.internal` or host IP; make configurable |
| Laptop RAM exhaustion (7 GB + 4 GB swap) | HIGH | Use smaller model for dev; document hosted API for production |
| MX250 GPU (2 GB VRAM) unusable for LLM | MEDIUM | CPU-only inference; don't optimize for GPU |
| qwen3:4b latency ~60-90s on CPU | HIGH | Accept for dev; plan hosted API (Together.ai, Fireworks) for prod |
| No .env.example | MEDIUM | Create template with all required variables |
| Voice service hardcoded Hindi | LOW | Make language configurable later |

---

## 7. Uncommitted Changes That Must Be Preserved

| File | Change | Reason |
|------|--------|--------|
| `backend/app/main.py` | Refactored to use `settings` + `api_router`; removed inline `/health` | Modular architecture |
| `backend/requirements.txt` | Added `pydantic-settings` | Config management |
| `backend/app/__init__.py` | New package init | Python package structure |
| `backend/app/api/__init__.py` | New package init | Python package structure |
| `backend/app/core/__init__.py` | New package init | Python package structure |

---

## 8. Prioritized Implementation Plan

### Phase 1: Foundation & Health (Day 1)
1. Add root-level `GET /health` endpoint in `main.py`
2. Create `.env.example` with all configuration keys
3. Add SQLite + aiosqlite initialization (`backend/app/db/`)
4. Add pytest + test for health endpoints
5. Add Ruff + MyPy config + pre-commit
6. Create `docs/backend/DEVELOPMENT_SETUP.md`, `ARCHITECTURE.md`, `CHANGELOG.md`

### Phase 2: Chat Endpoint & Ollama Integration (Day 2)
1. Create `backend/app/services/ollama.py` — HTTPX client with config
2. Create `backend/app/schemas/chat.py` — Request/Response Pydantic models
3. Create `backend/app/api/v1/chat.py` — Chat endpoint with validation
4. Register chat router in `router.py`
3. Benchmark qwen3:4b with 3 Hindi agricultural prompts

### Phase 3: Conversation Persistence (Day 2-3)
1. Create `backend/app/db/conversations.py` — CRUD for conversations/messages
2. Integrate with chat endpoint — load bounded context, persist messages
4. Add conversation ID handling (create new, continue existing, validate)

### Phase 4: Testing & Documentation (Day 3-4)
1. Unit tests for all endpoints with mocked Ollama
2. Integration tests for SQLite persistence
3. Update `docs/backend/API.md` with request/response examples
4. Update `docs/backend/ROADMAP.md` with completed items
5. Run full test suite, lint, type check
6. Verify Docker build and startup

---

## 9. Current Configuration

### Environment Variables Needed
```bash
# Backend
APP_NAME="My Farm AI Backend"
APP_VERSION="0.1.0"
ENVIRONMENT="development"
OLLAMA_BASE_URL="http://host.docker.internal:11434"  # or host IP
OLLAMA_MODEL="qwen3:4b"
OLLAMA_TIMEOUT_SECONDS=120
DATABASE_PATH="data/app.db"

# Voice Service (existing)
# No additional config currently
```

### Docker Networking
- Backend port 8000 → Host port 8000
- Voice port 8001 → Host port 8001
- Ollama on host port 11434 (external to compose)
- Backend → Ollama: use `OLLAMA_BASE_URL` env var

---

## 10. Definition of Done for Milestone 1

- [ ] Chat endpoint exists at `POST /api/v1/chat`
- [ ] Request/Response have defined Pydantic schemas
- [ ] Ollama URL and model configurable via env
- [ ] Docker networking documented and verified
- [ ] Conversations persist in SQLite (`data/app.db`)
- [ ] Recent context bounded (e.g., last 10 messages) and isolated per conversation
- [ ] Failure cases return appropriate HTTP responses (no stack traces)
- [ ] Tests pass without requiring live model inference
- [ ] API and setup documentation match the code
- [ ] Existing health endpoints and voice service remain functional
- [ ] Git diff contains no unrelated destructive changes
- [ ] Remaining limitations explicitly listed

---

*End of Audit — Ready for Implementation Planning*