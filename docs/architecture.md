# Architecture (verified 2026-10-23)

## Components

| Component | Path | Responsibility |
|-----------|------|----------------|
| **Web app** | `web/` | Next.js 15 App Router SPA: dashboard, chat, weather, resources |
| **Android app** | `android/` | Expo 51 / RN 0.74 client (API base via `EXPO_PUBLIC_API_BASE_URL`) |
| **Backend API** | `backend/` | FastAPI: routing, validation, business services, persistence |
| **Voice service** | `ai/voice/` | faster-whisper STT — **contained** (not in Compose, port unpublished) |
| **SearXNG** | `infra/searxng/` | Self-hosted metasearch — deployed for Phase 6 research, secret externalized |
| **Ollama** | external | Qwen3 4B inference at `http://localhost:11434` |

## Data Flow (chat)

```
Web/Android → POST /api/v1/chat
                   → provider factory (factory.py: app lifecycle, middleware)
                   → services/chat.py generate_chat_response()
                        → db/conversations.py (persist conversation + messages)
                        → services/ollama.py (HTTP to Ollama, pool + error handling)
                   ← {response, conversation_id, model}
```

## Data Flow (weather)

```
GET /api/v1/weather?lat&lon → weather service (TTL cache) → Open-Meteo → WMO-mapped response
```

## Persistence

- **Runtime today:** SQLite (`backend/data/app.db`, canonical per G1 decision — approval pending in the register). Tables `conversations` + `messages` created by `app/db/connection.py` `CREATE TABLE IF NOT EXISTS`.
- **Target (Phase 2):** SQLAlchemy 2 models + Alembic migration `backend/alembic/versions/6cd2bffd9881_initial_schema.py` defining 13 tables — `users, farms, farm_members, crops, crop_cycles, sessions, refresh_tokens, conversations, messages, research_queries, research_sources, citations, audit_events`. This migration targets the Phase 2 model and is **not yet the runtime schema of current SQLite data**; do not assume migrations ran.

## Cross-Cutting (implemented in backend)

- App factory with configuration profiles (`core/config_profiles.py`), validated settings (`core/config_validation.py`).
- Error envelope + request correlation, rate limiting with trusted-proxy CIDR handling, request body size limits (see `middleware/`, `core/config.py`).
- Health: `GET /health` (legacy), `GET /health/live`, `GET /health/ready` (`backend/app/factory.py:174-201`).

## Deployment

- `docker-compose.yml`: **backend only**, `network_mode: host`, mounts `./data` + `./.env` (read-only), non-exposed by default.
- Backend binds to loopback until Phase 3 authentication lands (hard governance rule).

## Diagram

```
Web (3000)   Android (Expo)
    │              │
    └──────┬───────┘
           ▼
   FastAPI (:8000, loopback)
   ├── chat ─── Ollama (Qwen3 4B)
   ├── weather ─ Open-Meteo (external)
   ├── resources (static verified catalogue)
   └── SQLite: conversations/messages (runtime) · Alembic 13-table target
```
