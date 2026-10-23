# MyFarm AI Backend — Architecture

## Overview

MyFarm AI Backend is a FastAPI-based REST API serving agricultural AI assistance to web and mobile clients. It provides chat functionality with conversation persistence, weather information via Open-Meteo, curated agricultural resources, integrates with local Ollama for LLM inference, and operates alongside a separate voice service for speech-to-text.

## System Context

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Web Client    │     │  Mobile Client  │     │  Voice Client   │
│   (Future)      │     │   (Future)      │     │   (Optional)    │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │ HTTPS
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DOCKER COMPOSE NETWORK                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    BACKEND :8000                          │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐    │    │
│  │  │  REST   │  │ Chat    │  │ Ollama  │  │ SQLite   │    │    │
│  │  │  API    │──│ Service │──│ Client  │  │ (File)   │    │    │
│  │  │         │  │         │  │         │  │          │    │    │
│  │  │         │  │         │  │         │  │          │    │    │
│  │  │         │  │ Weather │  │ Weather │  │          │    │    │
│  │  │         │──│ Service │──│ Client  │  │          │    │    │
│  │  │         │  │         │  │         │  │          │    │    │
│  │  │         │  │         │  │         │  │          │    │    │
│  │  │         │  │Resources│  │         │  │          │    │    │
│  │  │         │──│Catalogue│  │         │  │          │    │    │
│  │  └─────────┘  └─────────┘  └────┬────┘  └──────────┘    │    │
│  └─────────────────────────────────│─────────────────────────┘    │
└─────────────────────────────────────│─────────────────────────────┘
                                     │ HTTP
                                     ▼
                            ┌─────────────────┐
                            │   OLLAMA :11434 │
                            │   (External)    │
                            └─────────────────┘
                                     │ HTTPS
                                     ▼
                            ┌─────────────────┐
                            │ OPEN-METEO API  │
                            │ (External)      │
                            └─────────────────┘
```

## Component Responsibilities

### 1. FastAPI Application (`app/main.py`)
- Application factory and lifecycle management
- Root endpoints (`/`, `/health`)
- CORS middleware configuration
- API router inclusion

### 2. Configuration (`app/core/config.py`)
- Pydantic Settings with `.env` support
- Type-safe environment variable parsing
- All runtime configuration centralized
- Weather and agricultural resources configuration

### 3. API Layer (`app/api/v1/`)
- **router.py**: Versioned API router with prefix `/api/v1`
- **health.py**: Health check endpoints
- **chat.py**: Chat endpoint with validation and error handling
- **weather.py**: Weather endpoints (current + forecast)
- **resources.py**: Agricultural resources catalogue endpoints

### 4. Services (`app/services/`)
- **ollama.py**: Async HTTPX client for Ollama API
  - Connection pooling
  - Timeout handling
  - Error classification (timeout, connection, model not found)
- **chat.py**: Chat orchestration
  - System prompt construction with agricultural context
  - Conversation context retrieval
  - Message persistence coordination
- **weather.py**: Open-Meteo weather client
  - Async HTTPX client for weather API
  - Current weather + 7-day forecast
  - WMO weather code mapping
  - Timeout and error handling
- **resources.py**: Agricultural resources catalogue
  - Curated list of 12 verified Indian agricultural resources
  - Categories: schemes, advisory, market, weather, research, financial, digital
  - Category filtering support

### 5. Database (`app/db/`)
- **connection.py**: Async SQLite connection management
- **conversations.py**: CRUD operations for conversations and messages
- **init_db.py**: Schema initialization script
- **Schema**: `conversations` (id, timestamps, language, crop, location) + `messages` (id, conversation_id, role, content, timestamp)

### 6. Schemas (`app/schemas/`)
- **chat.py**: Pydantic models for request/response validation
  - `ChatRequest`: message, conversation_id, language, crop, location
  - `ChatResponse`: response, conversation_id, model
  - `ErrorResponse`: detail, error_code
- **weather.py**: Pydantic models for weather validation
  - `WeatherRequest`: latitude, longitude
  - `WeatherResponse`: current_weather, daily forecast, metadata
  - `WeatherErrorResponse`: detail, error_code
- **resources.py**: Pydantic models for resources
  - `AgriculturalResource`: title, category, url, source, description
  - `ResourcesListRequest`: category filter
  - `ResourcesResponse`: resources list, total, categories

## Data Flow

### Chat Request Flow

```
1. Client POST /api/v1/chat {message, conversation_id?, language?, crop?, location?}
         │
2. FastAPI validates request (Pydantic ChatRequest)
         │
3. Chat endpoint calls generate_chat_response()
         │
4. If conversation_id provided:
      - Load conversation from SQLite
      - Verify exists
   Else:
      - Create new conversation in SQLite
         │
5. Load recent messages (last 10) from SQLite
         │
6. Build system prompt with language, crop, location context
         │
7. Construct message history: [system] + recent + [user]
         │
8. Persist user message to SQLite
         │
9. Call OllamaClient.chat(messages)
         │
10. On success:
      - Persist assistant response to SQLite
      - Return ChatResponse
    On error:
      - Persist error message to SQLite
      - Raise appropriate HTTPException
```

### Weather Request Flow

```
1. Client GET /api/v1/weather?latitude=...&longitude=...&current=true&daily=true
         │
2. FastAPI validates coordinates (Pydantic WeatherRequest)
         │
3. Weather endpoint calls WeatherClient.get_weather()
         │
4. WeatherClient calls Open-Meteo API (HTTPX)
         │
5. On success:
      - Transform response (add weather descriptions from WMO codes)
      - Return structured WeatherResponse
    On error:
      - Map to appropriate HTTPException (timeout, connection, etc.)
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
| Unexpected error | 500 | INTERNAL_ERROR | Report issue |

All errors return structured JSON: `{"detail": "...", "error_code": "..."}`

## Security Considerations

- **No authentication** in Phase 0 (public prototype)
- **CORS** restricted to configured origins
- **Input validation** via Pydantic (message length ≤ 2000 chars, coordinate bounds)
- **No sensitive data** in logs or error responses
- **SQLite** file permissions managed by OS
- **Environment variables** for secrets (`.env` not committed)
- **Weather API** - no authentication required (Open-Meteo free tier)

## Deployment Architecture

### Development (Docker Compose)
```yaml
services:
  backend:
    build: ./backend
    network_mode: host
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env:ro
```

### Production Considerations
- Replace SQLite with PostgreSQL
- Add authentication (JWT/OIDC)
- Add rate limiting
- Use managed Ollama or hosted LLM API
- Add monitoring (Prometheus/Grafana)
- Use secrets manager for `.env` values
- Weather API: free tier suitable for prototype; consider paid for production SLA

## Scalability Limits (Phase 0)

| Component | Limit | Mitigation |
|-----------|-------|------------|
| SQLite writes | Single writer | Low traffic prototype |
| Ollama CPU inference | ~30-60s/request | Use smaller model or hosted API |
| Weather API calls | No rate limit (Open-Meteo) | Cache responses (TTL 300s) |
| Single backend instance | No horizontal scaling | Stateless, can scale behind LB |
| Conversation history | Unbounded growth | Add retention policy later |
| Resources catalogue | Static (12 items) | Easy to extend |

## Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Framework | FastAPI | 0.115+ |
| Server | Uvicorn | 0.34+ |
| Validation | Pydantic | 2.14+ |
| Config | Pydantic Settings | 2.16+ |
| HTTP Client | HTTPX | 0.28+ |
| Database | SQLite + aiosqlite | 0.22+ |
| Testing | Pytest + pytest-asyncio | 9.1+ |
| Linting | Ruff | 0.17+ |
| Type Checking | MyPy | 2.4+ |
| LLM Runtime | Ollama | Latest |
| LLM Model | Qwen3 | 4B (Q4_K_M) |
| Weather API | Open-Meteo | v1 |

## Future Extensibility Points

1. **Authentication**: Add JWT/OIDC middleware
2. **Weather API**: Already implemented; add caching layer
3. **Vector Search**: Add pgvector/pgvector for RAG
4. **Webhooks**: Event system for conversation updates
5. **Multi-tenancy**: Add organization_id to conversations
6. **Streaming**: Add Server-Sent Events for token streaming
7. **Voice Integration**: Connect voice service to chat pipeline