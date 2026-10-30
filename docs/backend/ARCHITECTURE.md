# MyFarm AI Backend — Architecture

**Version:** 0.1.0 (aligned with `settings.app_version`)  
**Date:** 2026-10-28  
**Status:** Phase 1 Complete — Quality Gates Passing

---

## Overview

MyFarm AI Backend is a FastAPI-based REST API serving agricultural AI assistance to web and mobile clients. It provides chat functionality with conversation persistence, weather information via Open-Meteo, curated agricultural resources, integrates with local Ollama for LLM inference, and operates alongside a deferred voice service for speech-to-text.

**Core Principle:** No paid APIs or mandatory SaaS dependencies. All AI inference runs locally via Ollama. PostgreSQL is the production database; SQLite is test-only.

---

## System Context

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Web Client    │     │  Mobile Client  │     │  Voice Client   │
│   (Next.js 15)  │     │  (Expo/RN 51)   │     │   (Deferred)    │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │ HTTPS / JSON
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DOCKER COMPOSE NETWORK                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    BACKEND :8000                          │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐    │    │
│  │  │  REST   │  │ Chat    │  │ Ollama  │  │PostgreSQL│    │    │
│  │  │  API    │──│ Service │──│ Client  │  │ (Prod)   │    │    │
│  │  │         │  │         │  │         │  │          │    │    │
│  │  │         │  │         │  │         │  │ SQLite   │    │    │
│  │  │         │  │ Weather │  │ Weather │  │ (Tests)  │    │    │
│  │  │         │──│ Service │──│ Client  │  │          │    │    │
│  │  │         │  │         │  │         │  │          │    │    │
│  │  │         │  │         │  │         │  │          │    │    │
│  │  │         │  │Resources│  │         │  │          │    │    │
│  │  │         │──│Catalogue│  │         │  │          │    │    │
│  │  └─────────┘  └─────────┘  └────┬────┘  └──────────┘    │    │
│  └─────────────────────────────────│─────────────────────────┘    │
└─────────────────────────────────────│─────────────────────────────┘
                                     │ HTTP (loopback)
                                     ▼
                            ┌─────────────────┐
                            │   OLLAMA :11434 │
                            │   (Host/Loopback)│
                            └─────────────────┘
                                     │ HTTPS
                                     ▼
                            ┌─────────────────┐
                            │ OPEN-METEO API  │
                            │ (External)      │
                            └─────────────────┘
```

**Network Policy:** Backend binds to `127.0.0.1` only. Phase 3 authentication is implemented (ADR-008); non-loopback exposure remains gated on the Phase 3 exit-gate security review.

---

## Component Responsibilities

### 1. Application Factory (`app/factory.py`)
- `create_app(settings, test_mode=False)` — Creates FastAPI instance with dependency injection
- Configuration profiles: DEVELOPMENT, TEST, PRODUCTION with validation
- Lifespan management: DB initialization, Alembic migrations (PostgreSQL), HTTP client cleanup
- Middleware stack: TrustedHost (prod), RequestBodyLimit, CORS, RateLimit, RequestID/Logging
- Health endpoints: `/health` (liveness), `/health/live`, `/health/ready` (readiness with DB/Ollama checks)

### 2. Configuration (`app/core/config.py`, `app/core/config_profiles.py`)
- Pydantic Settings with `.env` support and environment-aware profiles
- **Environment enum:** `development`, `test`, `production`
- **Profile defaults:** Applied at startup; production fails fast on unsafe config (wildcard CORS, missing trusted proxies, debug mode)
- **Validation:** `validate_for_environment()` checks production requirements
- **Settings groups:** Core, Ollama, Database, CORS, Logging, Weather, Resources, Rate Limiting, Trusted Proxy, Request Body Limits, DB Pool

### 3. API Layer (`app/api/v1/`)
| Module | Endpoints | Purpose |
|--------|-----------|---------|
| `router.py` | Aggregates all v1 routes | Versioned API under `/api/v1` |
| `health.py` | `GET /health`, `/health/live`, `/health/ready`, `/api/v1/health` | Liveness/readiness probes |
| `chat.py` | `POST /chat` | Agricultural Q&A with Ollama, conversation persistence |
| `farms.py` | `POST/GET/PATCH /farms`, `GET/PATCH/DELETE /farms/{id}/members(/{user_id})` | Farm CRUD + membership (P5A-01); service-level role authz (OWNER/MEMBER/VIEWER) |
| `crop_cycles.py` | `POST/GET /farms/{id}/crop-cycles`, `GET/PATCH /crop-cycles/{id}` | Crop-cycle records (P5A-02); forward-only status transitions, (farm, crop, season) uniqueness → 409 |
| `weather.py` | `GET /weather`, `/weather/current` | Open-Meteo integration, WMO codes |
| `resources.py` | `GET /resources`, `/resources/categories`, `/resources/{category}` | Curated Indian agricultural resources |

**Error Contract (ADR-009):** All errors return flat envelope:
```json
{
  "detail": "Human-readable message",
  "error_code": "STABLE_CODE",
  "request_id": "uuid",
  "errors": [{"field": "...", "message": "..."}]  // optional, validation only
}
```

### 4. Services (`app/services/`)
| Module | Responsibility |
|--------|----------------|
| `ollama.py` | Async HTTPX client for Ollama `/api/chat`; timeouts, retries, error classification (timeout, connection, model not found) |
| `ai/gateway.py` | **P4-01:** provider-independent `AIGateway` protocol (`chat`/`health_check`/`model_name`) + gateway error types; `OllamaGateway` adapter maps Ollama errors to gateway types — provider specifics confined here; domain modules depend on the interface only |
| `ai/registry.py` | **Phase 4B:** model registry (tag/capability/status/license); only enabled+capability-matching models selectable per-request; drift check vs live tags |
| `chat.py` | System prompt construction, context retrieval, message persistence, Ollama orchestration; sync + async variants for tests |
| `weather.py` | Open-Meteo client with 300s caching; current + 7-day forecast; WMO code → human-readable mapping |
| `resources.py` | Static catalogue of 12 verified Indian agricultural resources across 7 categories |

### 5. Database (`app/db/`)
| Module | Purpose |
|--------|---------|
| `session.py` | SQLAlchemy 2 async session management; `DatabaseManager` with async/sync engines, session factories, context managers |
| `repositories.py` | Repository pattern for all models: User, Farm, Crop, Conversation, Message, Research, Session, RefreshToken, AuditEvent |
| `models/` | SQLAlchemy 2 typed ORM models with UUID PKs, timestamps, constraints, indexes, relationships |

**Models:**
- **Auth:** `User`, `Session`, `RefreshToken`
- **Domain:** `Farm`, `FarmMember`, `Crop`, `CropCycle`
- **Chat:** `Conversation`, `Message` (with `MessageRole` enum)
- **Research:** `ResearchQuery`, `ResearchSource`, `Citation`
- **Audit:** `AuditEvent` (security events)

**Migrations:** Alembic async environment (`alembic/env.py`), initial migration `6cd2bffd9881_initial_schema.py` tested on PostgreSQL.

### 6. Schemas (`app/schemas/`)
| Module | Models |
|--------|--------|
| `chat.py` | `ChatRequest`, `ChatResponse`, `ErrorResponse` |
| `weather.py` | `WeatherRequest`, `WeatherResponse`, `WeatherErrorResponse` |
| `resources.py` | `AgriculturalResource`, `ResourcesListRequest`, `ResourcesResponse` |

---

## Data Flow

### Chat Request Flow (`POST /api/v1/chat`)

```
1. Client POST /api/v1/chat {message, conversation_id?, language?, crop?, location?}
         │
2. FastAPI validates request (Pydantic ChatRequest)
         │
3. Chat endpoint calls generate_chat_response() [async] or generate_chat_response_sync() [tests]
         │
4. If conversation_id provided:
      - Load conversation from DB via ConversationRepository
      - Verify exists, return 404 if not found
   Else:
      - Create new conversation with legacy_user_id (UUID nil) for backward compat
         │
5. Load recent messages (last 10) via MessageRepository.get_recent()
         │
6. Build system prompt with language, crop, location context
         │
7. Construct message history: [system] + recent + [user]
         │
8. Persist user message via MessageRepository.create(role=USER)
         │
9. Call OllamaClient.chat(messages)
         │
10. On success:
      - Persist assistant response via MessageRepository.create(role=ASSISTANT)
      - Return ChatResponse {response, conversation_id, model}
    On error (OllamaTimeoutError, OllamaConnectionError, OllamaModelNotFoundError):
      - Persist error message as assistant
      - Raise appropriate HTTPException (503/504)
    On unexpected error:
      - Return 500 INTERNAL_ERROR
```

### Weather Request Flow

```
1. Client GET /api/v1/weather?latitude=...&longitude=...&current=true&daily=true
         │
2. FastAPI validates coordinates (Pydantic WeatherRequest)
         │
3. Weather endpoint calls WeatherClient.get_weather()
         │
4. WeatherClient calls Open-Meteo API (HTTPX) with caching (300s TTL)
         │
5. On success:
      - Transform response (add weather descriptions from WMO codes)
      - Return structured WeatherResponse
    On error:
      - Map to HTTPException (503 connection, 504 timeout)
```

### Agricultural Resources Flow

```
1. Client GET /api/v1/resources?category=schemes
         │
2. Resources endpoint calls ResourcesCatalogue.get_all() or get_by_category()
         │
3. Returns filtered/curated list of 12 verified resources
         │
4. Response includes resources, total count, and available categories
```

---

## Error Handling Strategy

| Error Type | HTTP Status | Error Code | Client Action |
|------------|-------------|------------|---------------|
| Validation error | 422 | (Pydantic) | Fix request |
| Conversation not found | 404 | CONVERSATION_NOT_FOUND | Start new conversation |
| Category not found | 404 | CATEGORY_NOT_FOUND | Use valid category |
| Model not found | 503 | MODEL_NOT_FOUND | Check model name |
| Ollama connection failed | 503 | OLLAMA_CONNECTION_FAILED | Retry later |
| Ollama timeout | 504 | OLLAMA_TIMEOUT | Retry with shorter message |
| Weather connection failed | 503 | WEATHER_CONNECTION_FAILED | Retry later |
| Weather timeout | 504 | WEATHER_TIMEOUT | Retry later |
| Rate limit exceeded | 429 | RATE_LIMIT_EXCEEDED | Respect `Retry-After` |
| Unexpected error | 500 | INTERNAL_ERROR | Report issue |

**Request Correlation:** Every response includes `X-Request-ID` header; logs include request_id for traceability.

---

## Security Considerations

| Measure | Status | Details |
|---------|--------|---------|
| Authentication | ✅ Phase 3 | Opaque sessions (web cookie / Android bearer) + refresh rotation + Argon2id; backend still binds to `127.0.0.1` |
| Authorization | ✅ Phase 3 | Service-layer ownership predicates (`user_id` scoped in SQL, deny-by-default); see `docs/engineering/AUTHZ_MATRIX.md` |
| CORS | ✅ Configured | Explicit origins via `CORS_ALLOWED_ORIGINS`; prod requires explicit config |
| Trusted Proxy | ✅ Implemented | `TRUSTED_PROXY_CIDRS` required in production; rate limiter uses socket peer by default |
| Rate Limiting | ✅ Bounded LRU | In-memory TTL/LRU limiter; per-route limits; returns `Retry-After` |
| Request Body Limit | ✅ 1 MB default | Configurable via `MAX_REQUEST_BODY_SIZE`; returns 413 |
| Input Validation | ✅ Pydantic | Message ≤2000 chars, coordinate bounds, UUID validation |
| Error Sanitization | ✅ Implemented | No stack traces, SQL, secrets, or upstream bodies in responses |
| Structured Logging | ✅ JSON-ready | Request ID, method, path, client IP, status, latency; redaction for secrets |
| Container Hardening | ✅ Compose ready | Non-root user, internal network, health checks, read-only root FS where practical |
| Secrets Management | ✅ Externalized | `.env` mode 600; SearXNG secret rotated; PG password via Docker secrets |
| Dependency Pinning | ✅ uv.lock | Committed lockfile; dev/runtime groups separated |

---

## Deployment Architecture

### Development (Docker Compose)
```yaml
services:
  postgres:
    image: postgres:17
    # ... healthcheck, secrets, internal network
  backend:
    build: ./backend
    environment:
      DATABASE_PATH: postgresql://myfarmai:myfarmai@postgres:5432/myfarmai
    volumes:
      - ./backend/data:/app/data  # Canonical SQLite
      - ./.env:/app/.env:ro
    networks:
      - myfarmai-internal
    depends_on:
      postgres:
        condition: service_healthy
```

**Key Points:**
- Single-host Compose with internal bridge network
- PostgreSQL and backend internal only; no published ports except via future Caddy (Phase 8)
- Ollama runs on host loopback (`127.0.0.1:11434`), not in Compose
- SearXNG and voice internal only
- Volume for PostgreSQL data on `/data`

### Production Considerations (Future)
- Caddy as TLS terminator on 80/443 (ADR-010)
- PostgreSQL backups via `pg_dump -Fc` to `/data`, encrypted, off-host copy
- Ollama model pre-baked/pinned, persistent cache
- Rate limiting, body limits, trusted proxy config enforced
- ADR-015 backup/retention policy implemented

---

## Scalability Limits (Phase 1)

| Component | Limit | Mitigation |
|-----------|-------|------------|
| SQLite writes | Single writer | Dev only; PostgreSQL for production |
| Ollama CPU inference | ~10-30s/request (`qwen3:0.6b`) | Small model; Phase 4 AI gateway with concurrency cap |
| Weather API calls | No rate limit (Open-Meteo) | 300s cache TTL |
| Single backend instance | No horizontal scaling | Stateless; can scale behind LB after session externalization |
| Conversation history | Unbounded growth | Retention policy in ADR-015 |
| Resources catalogue | Static (12 items) | Easy to extend |

---

## Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Framework | FastAPI | 0.115+ |
| Server | Uvicorn | 0.34+ |
| Validation | Pydantic | 2.10+ |
| Config | Pydantic Settings | 2.10+ |
| HTTP Client | HTTPX | 0.28+ |
| ORM | SQLAlchemy | 2.0+ |
| Migrations | Alembic | 1.14+ |
| Database (Prod) | PostgreSQL | 17 |
| Database (Test) | SQLite + aiosqlite | 0.20+ |
| Async Driver | asyncpg | 0.29+ |
| Testing | Pytest + pytest-asyncio | 8.3+ |
| Linting | Ruff | 0.10+ |
| Type Checking | MyPy | 1.14+ |
| Dependency Mgmt | uv | Latest |
| LLM Runtime | Ollama | Latest |
| LLM Model | Qwen3 | 0.6B (Q4_K_M, default) |
| Weather API | Open-Meteo | v1 (non-commercial) |
| Search | SearXNG | Latest (AGPL-3.0, internal) |

---

## Future Extensibility Points

1. **Authentication (Phase 3, implemented):** Opaque sessions (web) + rotating refresh tokens (mobile); Argon2id password hashing; service-layer ownership enforcement; per-IP + per-account limits; CSRF/Origin enforcement
2. **AI Gateway (Phase 4):** Provider-independent interface over Ollama; model allowlist, prompt versioning, bounded concurrency, resource-aware fallback
3. **Research Engine (Phase 6):** SearXNG + PostgreSQL FTS; safe extraction, citations, SSRF protection
4. **Vector Search (Deferred):** Qdrant only if PostgreSQL FTS insufficient (ADR-007)
5. **Background Jobs (Deferred):** Valkey + workers only when measured need exists (ADR-012)
6. **Voice Reintroduction:** Requires Phase 3 auth + ADR-014 criteria (auth, limits, non-root, pre-baked model, internal network)

---

*Architecture reflects current implementation as of Phase 1 completion (2026-10-28).*