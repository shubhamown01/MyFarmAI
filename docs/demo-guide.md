# Instructor Demonstration Guide

**Date:** 2026-10-23 · All commands verified as present in the repo; run them once before the demo.

## Pre-demo checklist (10 min)

```bash
cd /data/MyFarmAI
ollama list | grep qwen3:4b            # model present?
docker compose up -d                   # backend container
curl -s http://127.0.0.1:8000/health/ready   # {"status":"ok",...}
cd web && npm run dev &                # http://localhost:3000
# optional before demo: make backend-check && make web-check
```

## Suggested sequence (15–20 min)

1. **Overview (2 min)** — show `docs/project-overview.md`; explain farmer-first problem, three clients, single backend.
2. **Backend API (3 min)** — open `http://127.0.0.1:8000/docs`; demonstrate `GET /api/v1/weather?lat=20&lon=73`; note error envelope and rate limiting.
3. **Web chat (5 min)** — on http://localhost:3000, ask an agricultural question with `location`/`crop` context; show conversation continuity (follow-up question, same thread).
4. **Resources catalog (3 min)** — browse resources page; point out `12 verified Indian sources` in 7 categories; explain curation vs. scraping.
5. **Weather integration (2 min)** — weather card, note Open-Meteo free-tier licensing constraint.
6. **Android (3 min, optional)** — `cd android && npm start` + emulator (`npm run android`); identical chat flow; mention `EXPO_PUBLIC_API_BASE_URL` configure-on-demand pattern.
7. **Code / architecture (2 min)** — `docs/architecture.md` diagram; show app factory + Alembic target schema in `backend/alembic/versions/`.

## Known limitations (state them honestly)

| Limitation | Reason |
|-----------|--------|
| No login/auth | Phase 3 (roadmap gate) — API is loopback-only until then |
| Voice not available in demo | Contained for security (port unpublished, bearer token required, 25 MB cap) until a consumer is wired |
| Android build tested only as dev server | No release build verified in this pass |
| AI answers depend on Ollama/Qwen3 availability and quality | Local, low-VRAM model (2 GB VRAM host) |
| Alembic 13-table schema not applied to live SQLite | Phase 2 pending — chat uses runtime tables only |

## Fallbacks

- Ollama down → `/health/ready` shows degraded; demo weather + resources + UI instead (chat returns 503 with clean error envelope).
- Web not building → show API via `/docs` and Android, or static images in `docs/`.

## Recover

```bash
docker compose down          # stop backend
pkill -f "uvicorn app.main"  # only if running uvicorn directly
```
