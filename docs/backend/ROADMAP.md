# MyFarm AI Backend — Roadmap

## Current Status: Milestone 3A Complete ✅

**Date**: 2026-10-18  
**Version**: 0.2.0

---

## Milestone 1: Functional AI Chat Backend ✅ COMPLETED

### Completed Features
- [x] Health endpoints (`/`, `/health`, `/api/v1/health`)
- [x] Chat endpoint `POST /api/v1/chat`
- [x] Request/response validation (Pydantic)
- [x] Ollama integration (async HTTPX client)
- [x] SQLite conversation persistence
- [x] Conversation continuity
- [x] Agricultural context (crop, location, language)
- [x] Error handling with structured responses
- [x] Configuration via `.env`
- [x] Docker support with host networking
- [x] Test suite (health, database, schemas)
- [x] Code quality (Ruff, MyPy, pre-commit)
- [x] Documentation (SETUP, ARCHITECTURE, API, CHANGELOG)

### Test Results
- 56/56 tests passing (health, database, schemas, weather, resources, chat)
- Linting: Ruff clean
- Type checking: MyPy strict clean

---

## Milestone 2: Weather & Agricultural Resources ✅ COMPLETED

**Date**: 2026-10-18  
**Version**: 0.2.0

### Completed Features
- [x] **Weather API** (Open-Meteo integration)
  - [x] `GET /api/v1/weather` — Current weather + 7-day forecast
  - [x] `GET /api/v1/weather/current` — Current weather only
  - [x] WMO weather codes with human-readable descriptions
  - [x] Configurable via `WEATHER_BASE_URL`, `WEATHER_TIMEOUT_SECONDS`
  - [x] Comprehensive error handling (timeout, connection, malformed response)
  - [x] 10 weather tests (validation, mocking, error handling, boundary conditions)

- [x] **Agricultural Resources Catalogue**
  - [x] `GET /api/v1/resources` — Curated list of 12 verified Indian agricultural resources
  - [x] `GET /api/v1/resources/categories` — List all categories
  - [x] `GET /api/v1/resources?category=...` — Query parameter filtering
  - [x] `GET /api/v1/resources/{category}` — Path parameter filtering
  - [x] 12 verified resources across 7 categories (schemes, advisory, market, weather, research, financial, digital)
  - [x] Sources: ICAR, Ministry of Agriculture, IMD, NABARD, NPCI
  - [x] 12 resources tests (listing, filtering, categories, structure validation)

- [x] **CORS Support**
  - [x] Configurable via `CORS_ALLOWED_ORIGINS` environment variable
  - [x] Restricted origins by default (no wildcard in production)
  - [x] Credentials and methods explicitly configured

- [x] **OpenAPI Documentation**
  - [x] `/docs` (Swagger UI), `/redoc`, `/openapi.json` automatically available
  - [x] All new endpoints documented with examples

- [x] **Comprehensive Test Coverage**
  - [x] 10 weather tests (validation, mocking, error handling, boundary conditions)
  - [x] 12 resources tests (listing, filtering, categories, structure validation)
  - [x] All tests pass without external dependencies (mocked HTTP clients)

- [x] **Code Quality**
  - [x] Ruff linting and formatting for new modules
  - [x] MyPy strict type checking passes
  - [x] Pre-commit hooks cover new files

### Test Results
- 56/56 tests passing (health, database, schemas, weather, resources, chat)
- Linting: Ruff clean
- Type checking: MyPy strict clean

---

## Milestone 3A: Prototype Hardening & Integration Readiness ✅ COMPLETED

**Date**: 2026-10-18  
**Version**: 0.2.0

### Completed Features
- [x] **Structured Logging & Request IDs**
  - [x] Request ID generated/extracted per request (`x-request-id` header)
  - [x] Request ID returned in response headers
  - [x] Structured logging with request context (method, path, client IP)
  - [x] Error logging with request ID for traceability

- [x] **Rate Limiting**
  - [x] In-memory sliding window rate limiter
  - [x] Configurable via `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS`
  - [x] Returns HTTP 429 with `Retry-After` header
  - [x] Excludes health endpoints from limiting
  - [x] Returns `RATE_LIMIT_EXCEEDED` error code

- [x] **Graceful Lifecycle Management**
  - [x] Lifespan context manager for startup/shutdown
  - [x] Database initialization on startup
  - [x] HTTP client cleanup on shutdown
  - [x] Graceful error handling without breaking requests

- [x] **Configuration Validation**
  - [x] Startup validation of all settings
  - [x] Warnings for production-inappropriate settings
  - [x] Critical errors exit with non-zero code

- [x] **Authentication Assessment Document**
  - [x] Threat model analysis
  - [x] Deployment context assessment
  - [x] Recommended auth strategy per deployment phase

- [x] **Integration Guides**
  - [x] Android/React Native (Expo) integration guide
  - [x] Web/Next.js integration guide

- [x] **OpenAPI Documentation** (Already available - verified)
  - [x] `/docs` (Swagger UI), `/redoc`, `/openapi.json` automatically available
  - [x] All new endpoints documented with examples

- [x] **Comprehensive Test Coverage**
  - [x] 10 weather tests (validation, mocking, error handling, boundary conditions)
  - [x] 12 resources tests (listing, filtering, categories, structure validation)
  - [x] 9 chat tests (validation, mocking, error handling, conversation continuity)
  - [x] All tests pass without external dependencies (mocked HTTP clients)

- [x] **Code Quality**
  - [x] Ruff linting and formatting for new modules
  - [x] MyPy strict type checking passes
  - [x] Pre-commit hooks cover new files

### Test Results
- 56/56 tests passing (health, database, schemas, weather, resources, chat)
- Linting: Ruff clean
- Type checking: MyPy strict clean

---

## Milestone 3B: Integration Readiness 🔄 PLANNED

### Target: 2026-12-15

### Features
- [ ] **Authentication (Optional)**
  - [ ] JWT token validation middleware
  - [ ] Optional OIDC provider integration
  - [ ] Anonymous access for public endpoints

- [ ] **Production Hardening**
  - [ ] Structured logging (JSON format)
  - [ ] Request ID propagation to downstream services
  - [ ] Health check enhancements (readiness/liveness probes)
  - [ ] Graceful shutdown handling with signal handling

- [ ] **Android/Web Client Integration**
  - [ ] API contract verification
  - [ ] Example client code (React Native, Kotlin)
  - [ ] WebSocket/SSE streaming design

### Dependencies
- Milestone 3A complete ✅

---

## Future Milestones (Post-Production)

### Milestone 4: Data Intelligence (2027-Q1)
- [ ] PostgreSQL migration with Alembic
- [ ] RAG with pgvector for document QA
- [ ] Agricultural document corpus (ICAR advisories, research papers)
- [ ] Web research engine (SearXNG + Crawlee)

### Milestone 5: Voice & Multilingual (2027-Q2)
- [ ] Hindi TTS (Piper integration)
- [ ] Additional Indian languages (Bengali, Marathi, Tamil, Telugu)
- [ ] Voice service integration with backend
- [ ] Streaming audio support

### Milestone 6: Scale & Platform (2027-Q3)
- [ ] PostgreSQL with connection pooling
- [ ] Horizontal scaling (stateless backend)
- [ ] Kubernetes deployment manifests
- [ ] Multi-region deployment
- [ ] Admin dashboard

---

## Technical Debt & Improvements

### High Priority
- [ ] Add request/response logging middleware
- [ ] Implement graceful shutdown with signal handling
- [ ] Add request ID to all log entries (already done via middleware)
- [ ] Conversation retention policy (auto-cleanup)

### Medium Priority
- [ ] Streaming responses (SSE)
- [ ] Background job queue (Celery + Redis)
- [ ] API versioning strategy
- [ ] Comprehensive integration tests
- [ ] Load testing baseline

### Low Priority
- [ ] GraphQL endpoint (optional)
- [ ] gRPC for internal services
- [ ] Event sourcing for conversations
- [ ] Multi-model routing (different models for different tasks)

---

## Resource Requirements

| Milestone | Compute | Storage | External APIs |
|-----------|---------|---------|---------------|
| M1 (Done) | 1 CPU, 2GB RAM | 1GB SQLite | Ollama (local) |
| M2 (Done) | +0.5 CPU | +100MB cache | Weather API (free) |
| M3A (Done) | +0.5 CPU | +100MB cache | Weather API (free) |
| M3B | +0.5 CPU, Redis | +500MB logs | Auth provider (optional) |
| M4+ | PostgreSQL, GPU | 10GB+ vectors | LLM API (hosted) |

---

## Risk Register

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Ollama CPU latency | High | High | Plan hosted LLM API for production |
| Free weather API limits | Medium | Medium | Cache responses, multiple providers |
| SQLite concurrency | Medium | Low | Migrate to PostgreSQL before M3 |
| Model quality (Hindi) | High | Medium | Budget for fine-tuning or better model |
| Regulatory compliance | High | Low | Legal review before public launch |

---

## Definition of Done per Milestone

A milestone is complete when:
- [ ] All features implemented and tested
- [ ] Documentation updated (API, ARCHITECTURE, SETUP)
- [ ] CHANGELOG updated
- [ ] All tests pass (unit + integration)
- [ ] Linting and type checking pass
- [ ] Docker build succeeds
- [ ] Deployed to staging environment
- [ ] Code reviewed and merged to `main`

---

## Review Cadence

- **Weekly**: Sprint progress review
- **Bi-weekly**: Milestone checkpoint
- **Monthly**: Architecture review
- **Per Milestone**: Release retrospective