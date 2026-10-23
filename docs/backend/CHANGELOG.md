# MyFarm AI Backend — Changelog

All notable changes to the backend are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.2.0] - 2026-10-18

### Added
- **Weather API** (Open-Meteo integration)
  - `GET /api/v1/weather` — Current weather + 7-day forecast
  - `GET /api/v1/weather/current` — Current weather only
  - WMO weather codes with human-readable descriptions
  - Configurable via `WEATHER_BASE_URL`, `WEATHER_TIMEOUT_SECONDS`
  - Comprehensive error handling (timeout, connection, malformed response)

- **Agricultural Resources Catalogue**
  - `GET /api/v1/resources` — Curated list of 12 verified Indian agricultural resources
  - `GET /api/v1/resources/categories` — List all categories
  - `GET /api/v1/resources?category=...` — Query parameter filtering
  - `GET /api/v1/resources/{category}` — Path parameter filtering
  - 12 verified resources across 7 categories (schemes, advisory, market, weather, research, financial, digital)
  - Sources: ICAR, Ministry of Agriculture, IMD, NABARD, NPCI

- **CORS Support**
  - Configurable via `CORS_ALLOWED_ORIGINS` environment variable
  - Restricted origins by default (no wildcard in production)
  - Credentials and methods explicitly configured

- **OpenAPI Documentation**
  - `/docs` (Swagger UI), `/redoc`, `/openapi.json` automatically available
  - All new endpoints documented with examples

- **Comprehensive Test Coverage**
  - 10 weather tests (validation, mocking, error handling, boundary conditions)
  - 12 resources tests (listing, filtering, categories, structure validation)
  - All tests pass without external dependencies (mocked HTTP clients)

- **Code Quality**
  - Ruff linting and formatting for new modules
  - MyPy strict type checking passes
  - Pre-commit hooks cover new files

- **Structured Logging & Request IDs**
  - Request ID generated/extracted per request (`x-request-id` header)
  - Request ID returned in response headers
  - Structured logging with request context (method, path, client IP)
  - Error logging with request ID for traceability

- **Rate Limiting**
  - In-memory sliding window rate limiter
  - Configurable via `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS`
  - Returns HTTP 429 with `Retry-After` header
  - Excludes health endpoints from limiting
  - Returns `RATE_LIMIT_EXCEEDED` error code

- **Graceful Lifecycle Management**
  - Lifespan context manager for startup/shutdown
  - Database initialization on startup
  - HTTP client cleanup on shutdown
  - Graceful error handling without breaking requests

- **Configuration Validation**
  - Startup validation of all settings
  - Warnings for production-inappropriate settings
  - Critical errors exit with non-zero code

- **Authentication Assessment Document**
  - Threat model analysis
  - Deployment context assessment
  - Recommended auth strategy per deployment phase

- **Integration Guides**
  - Android/React Native (Expo) integration guide
  - Web/Next.js integration guide

### Changed
- **Health Endpoint**: Moved from inline `/health` in `main.py` to versioned `/api/v1/health` via router, added root `/health` for convenience

### Fixed
- Ollama connection from Docker container using host network mode
- SQLite directory creation on startup
- Exception chaining for proper error tracing
- Message ID handling for SQLite AUTOINCREMENT
- Chat test mock patching (fixed to patch `app.services.chat.ollama_client`)

### Infrastructure
- Requirements updated with test dependencies
- Ruff configuration with per-file ignores
- MyPy strict configuration with overrides
- Pre-commit configuration
- Pytest configuration with async support
- Rate limit settings in config

## [0.1.0] - 2026-10-18

### Added
- **Health Endpoints**
  - `GET /` — Project information
  - `GET /health` — Root health check
  - `GET /api/v1/health` — Versioned health check

- **Chat API**
  - `POST /api/v1/chat` — Agricultural AI chat endpoint
  - Request validation with Pydantic (message length, language codes, optional fields)
  - Conversation continuity via `conversation_id`
  - Agricultural context support (crop, location, language)
  - Structured error responses with error codes

- **Ollama Integration**
  - Async HTTPX client with connection pooling
  - Configurable base URL, model, timeout
  - Error classification: timeout, connection, model not found
  - Proper exception chaining (`raise ... from e`)

- **SQLite Conversation Persistence**
  - `conversations` table: id, timestamps, language, crop, location
  - `messages` table: id, conversation_id, role, content, timestamp
  - Automatic schema initialization
  - Conversation CRUD operations
  - Bounded context retrieval (last 10 messages)
  - Conversation isolation

- **Configuration**
  - Pydantic Settings with `.env` support
  - All runtime config via environment variables
  - `.env.example` template provided

- **Code Quality**
  - Ruff linting and formatting
  - MyPy strict type checking
  - Pytest with async support
  - Pre-commit hooks
  - Comprehensive test suite (health, database, schemas)

- **Docker Support**
  - Multi-stage Dockerfile
  - Docker Compose with host networking for Ollama
  - Volume mount for SQLite persistence
  - `.env` file mount

### Changed
- **Health Endpoint**: Moved from inline `/health` in `main.py` to versioned `/api/v1/health` via router, added root `/health` for convenience

### Fixed
- Ollama connection from Docker container using host network mode
- SQLite directory creation on startup
- Exception chaining for proper error tracing
- Message ID handling for SQLite AUTOINCREMENT

### Infrastructure
- Requirements updated with test dependencies
- Ruff configuration with per-file ignores
- MyPy strict configuration with overrides
- Pre-commit configuration
- Pytest configuration with async support

## [0.0.1] - 2026-10-17

### Added
- Initial project scaffold
- FastAPI application with root endpoint
- Voice service with faster-whisper (Hindi STT)
- Docker Compose for backend + voice services
- Basic project structure and `.gitignore`

---

## Unreleased (Planned)

### Milestone 3 — Integration Readiness
- Authentication (JWT/OIDC)
- Rate limiting
- Android/iOS client integration guides

### Future Enhancements
- PostgreSQL migration
- RAG with vector search (pgvector/Qdrant)
- Web research engine (SearXNG + Crawlee)
- Hindi TTS (Piper)
- Streaming responses (SSE)
- Multi-tenancy support
- Admin dashboard