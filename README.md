# MyFarmAI

An agricultural AI platform serving farmers, agronomists, and field workers with AI-powered chat assistance, weather information, and curated agricultural resources.

## Overview

MyFarmAI is a multi-platform application providing:
- **AI Chat Assistant** — Farming questions answered with agricultural context (crops, location, language)
- **Weather Intelligence** — Current conditions and forecasts via Open-Meteo
- **Agricultural Resources** — Curated catalogue of 12+ verified Indian government schemes, advisories, and market information
- **Voice Interaction** — Speech-to-text (Hindi/English) via local Whisper model

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Web App   │     │ Android App │     │ Voice Client│
│  (Next.js)  │     │ (Expo/RN)   │     │  (Optional) │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │ HTTPS
                           ▼
              ┌─────────────────────────┐
              │      BACKEND API        │
              │      (FastAPI)          │
              │  ┌───────────────────┐  │
              │  │  Chat Service     │  │
              │  │  Weather Service  │  │
              │  │  Resources Cat.   │  │
              │  │  Ollama Client    │──┼──▶ Ollama (Qwen3 4B)
              │  │  SQLite (async)   │  │
              │  └───────────────────┘  │
              └─────────────────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              ┌─────────┐   ┌───────────┐
              │ Open-   │   │  Voice    │
              │ Meteo   │   │ Service   │
              │ Weather │   │ (Whisper) │
              └─────────┘   └───────────┘
```

## Quick Start

### Prerequisites
- Node.js 20+
- Python 3.12+ (backend uses `uv` + `uv.lock`)
- Docker & Docker Compose
- Ollama (for LLM inference): `ollama pull qwen3:4b`

### Development Setup

```bash
# Clone and enter
cd /data/MyFarmAI

# Start backend service (voice service is contained, not published — see SECURITY.md)
docker compose up -d

# Web frontend
cd web
npm install
npm run dev          # http://localhost:3000

# Android app (separate terminal)
cd android
npm install
npm start            # Expo dev server
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your settings
```

Key variables:
- `OLLAMA_BASE_URL` — Ollama API endpoint (default: http://localhost:11434)
- `OLLAMA_MODEL` — Model name (default: qwen3:4b)
- `CORS_ALLOWED_ORIGINS` — Allowed frontend origins

## Project Structure

```
/data/MyFarmAI/
├── web/                    # Next.js 15 web application
│   ├── src/
│   │   ├── app/           # App Router pages
│   │   ├── components/    # Feature components (Chat, Weather, Resources)
│   │   ├── hooks/         # Custom React hooks
│   │   ├── lib/           # API client, utilities
│   │   └── providers.tsx  # TanStack Query provider
│   └── package.json
├── android/                # React Native/Expo application
│   ├── src/
│   │   ├── components/    # Shared components
│   │   ├── hooks/         # Custom hooks (useChat, useWeather)
│   │   ├── lib/api/       # API client + types
│   │   ├── storage/       # SecureStore persistence
│   │   └── config/        # API config, constants
│   └── package.json
├── backend/                # FastAPI backend
│   ├── app/
│   │   ├── api/v1/        # REST endpoints (chat, weather, resources)
│   │   ├── core/          # Configuration
│   │   ├── db/            # SQLite async operations
│   │   ├── services/      # Business logic (Ollama, chat, weather, resources)
│   │   └── schemas/       # Pydantic models
│   ├── tests/             # Pytest test suite
│   └── requirements.txt
├── ai/
│   └── voice/             # FastAPI voice service (Whisper)
├── infra/
│   └── searxng/           # Self-hosted search (optional)
├── docs/                  # Documentation
│   ├── backend/           # Architecture, API, roadmap
│   ├── frontend/          # Design system, color, interactions
│   ├── integration/       # Web/Android integration guides
│   └── roadmaps/          # Implementation roadmaps
├── graphify-out/          # Knowledge graph (generated)
├── docker-compose.yml     # Development services
└── .env.example           # Environment template
```

## Technology Stack

| Layer | Technology |
|-------|------------|
| Web Framework | Next.js 15, React 18, TypeScript |
| Styling | Tailwind CSS 3.4, CSS Variables |
| State Management | TanStack Query v5 (server), Zustand (client) |
| Mobile Framework | Expo 51, React Native 0.74, React Native Paper |
| Backend Framework | FastAPI, Uvicorn |
| Validation | Pydantic 2, Pydantic Settings |
| Database | SQLite + aiosqlite (async) |
| LLM Runtime | Ollama (Qwen3 4B Q4_K_M) |
| Voice STT | faster-whisper (small, CPU, int8) |
| Weather API | Open-Meteo (free tier) |
| Testing | Jest (web), Jest (android), Pytest (backend) |
| Linting | ESLint, Ruff, MyPy |
| Containerization | Docker Compose |

## Development Commands

### Web Frontend
```bash
cd web
npm run dev        # Development server
npm run build      # Production build
npm run start      # Production server
npm run lint       # ESLint
npm run typecheck  # TypeScript check
npm test           # Jest tests
```

### Android App
```bash
cd android
npm start          # Expo dev server
npm run android    # Android emulator
npm run ios        # iOS simulator
npm run lint       # ESLint
npm run typecheck  # TypeScript check
npm test           # Jest tests
```

### Backend
```bash
cd backend
uv run pytest tests -v              # Tests
uv run ruff check app               # Lint
uv run mypy app                     # Type check
uv run uvicorn app.main:app --host 127.0.0.1 --reload   # Dev server (loopback only)

# Alternative: single entrypoint for all backend checks
./scripts/check.sh                  # From repository root
```

### Docker
```bash
docker compose up -d        # Start backend (voice is contained, not published)
docker compose logs -f      # View logs
docker compose down         # Stop services
```

## Documentation

- [Project Overview](docs/project-overview.md)
- [Architecture](docs/architecture.md)
- [Setup Guide](docs/setup-guide.md)
- [API Documentation](docs/api-documentation.md)
- [Database Design](docs/database-design.md)
- [Demo Guide](docs/demo-guide.md)
- [Backend Architecture](docs/backend/ARCHITECTURE.md)
- [Backend API Reference](docs/backend/API.md)
- [Backend Roadmap](docs/backend/ROADMAP.md)
- [Frontend Design System](docs/frontend/DESIGN_SYSTEM.md)
- [Frontend Color System](docs/frontend/COLOR_SYSTEM.md)
- [Interaction Guidelines](docs/frontend/INTERACTION_GUIDELINES.md)
- [Web Integration Guide](docs/integration/WEB_INTEGRATION.md)
- [Android Integration Guide](docs/integration/ANDROID_INTEGRATION.md)
- [Frontend Dashboard Roadmap](docs/roadmaps/MyFarmAI_Frontend_Dashboard_Roadmap.md)

## Current Status

| Component | Status |
|-----------|--------|
| Backend API | ✅ Core endpoints implemented |
| Voice Service | ✅ Whisper transcription working — **contained**: not in Compose, port 8001 unpublished |
| Web Frontend | 🚧 Dashboard implementation in progress (see roadmap) |
| Android App | 🚧 Feature parity with web |
| Design System | ✅ Foundation documented, tokens pending |
| Tests | ✅ Backend passing, Web/Android baseline passing |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow, coding standards, and pull request process.

## Security

See [SECURITY.md](SECURITY.md) for vulnerability reporting and security policy.

## License

Apache-2.0 — see [LICENSE](LICENSE). Third-party notices in [docs/engineering/LICENSE_DECISION.md](docs/engineering/LICENSE_DECISION.md).