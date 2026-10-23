# Setup Guide (fresh machine)

**Verified commands — 2026-10-23** (commands exist in this repo; full-fresh-clone run NOT yet executed end-to-end — see note at end).

## Prerequisites

| Tool | Version | Used by |
|------|---------|---------|
| Node.js | 20+ | `web/`, `android/` |
| Python | 3.12+ | backend (managed via `uv`) |
| uv | latest | backend deps from `backend/uv.lock` |
| Docker + Compose v2 | — | backend container |
| Ollama | — | LLM inference (`ollama pull qwen3:4b`) |

## Steps

```bash
git clone <repo-url> /data/MyFarmAI && cd /data/MyFarmAI

# 1. Environment
cp .env.example .env          # edit values; never commit .env

# 2. Backend (uv installs into backend/.venv from uv.lock)
cd backend && uv sync && cd ..

# 3. Web
cd web && npm install && cd ..

# 4. Android
cd android && npm install && cd ..

# 5. Ollama model
ollama pull qwen3:4b
```

## Run (development)

```bash
# Backend — loopback only (until Phase 3 auth exists)
cd backend && uv run uvicorn app.main:app --host 127.0.0.1 --reload
# or: docker compose up -d

# Web (separate terminal)
cd web && npm run dev           # http://localhost:3000

# Android (separate terminal)
cd android && npm start
```

## Key environment variables (from `backend/app/core/config.py`)

| Var | Default | Notes |
|-----|---------|-------|
| `DATABASE_PATH` | `data/app.db` | SQLite location |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | `http://localhost:11434` / `qwen3:4b` | |
| `CORS_ALLOWED_ORIGINS` | localhost:3000, localhost:8081 | web + Expo |
| rate limiting, trusted proxy CIDRs, body limits, log level | see `.env.example` | |

Client API bases: web uses `NEXT_PUBLIC_API_BASE_URL` (falls back to `/api/v1`); Android uses `EXPO_PUBLIC_API_BASE_URL` (falls back to localhost emulator alias — see `android/src/config/api.ts`).

## Verify installation

```bash
make backend-check        # ruff format/lint + mypy + pytest (scripts/check.sh)
make web-check            # typecheck + eslint + jest
make android-check        # typecheck + eslint
docker compose config -q  # compose syntax
```

**Migration note (Phase 2 target schema):** `cd backend && uv run alembic upgrade head` applies Alembic migrations. Runtime SQLite is currently the `conversations`/`messages` tables from `connection.py`; running Alembic on them is part of Phase 2, not this setup guide today. Do not point Alembic at the canonical DB without the G1 approval + backup.
