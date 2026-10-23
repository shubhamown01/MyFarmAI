# API Documentation (backend, verified 2026-10-23)

Base URL: `http://127.0.0.1:8000` (development, loopback binding).
All endpoints defined in `backend/app/api/v1/`. **No authentication exists today** (planned Phase 3) — the API must not be exposed beyond loopback.

## Health

| Method | Path | Response |
|--------|------|----------|
| GET | `/health` | `{"status":"ok","service":"backend"}` (legacy alias) |
| GET | `/health/live` | liveness (`factory.py:182`) |
| GET | `/health/ready` | readiness incl. dependency state (`factory.py:190`) |

## Chat

**POST `/api/v1/chat`**

Request (`ChatRequest`, `backend/app/schemas/chat.py`):
```json
{
  "message": "मेरी गेहूं की फसल में पीले पत्ते क्यों आ रहे हैं?",
  "conversation_id": "uuid-or-null",
  "language": "en",            // pattern: ^[a-z]{2}$
  "crop": "wheat",             // optional, ≤100 chars
  "location": "Nashik"         // optional, ≤200 chars
}
```
- `message`: required, 1–2000 chars, trimmed/validated non-whitespace.

Response `200` (`ChatResponse`):
```json
{"response": "...", "conversation_id": "...", "model": "qwen3:4b"}
```

Errors (shared `ErrorResponse {detail, error_code}`): `400` invalid request · `404` unknown conversation_id · `503` Ollama unavailable · `504` timeout.

## Weather

| Method | Path | Query | Notes |
|--------|------|-------|-------|
| GET | `/api/v1/weather` | `lat`, `lon` | forecast + current, TTL-cached |
| GET | `/api/v1/weather/current` | `lat`, `lon` | current conditions only |

Response `200` (`WeatherResponse`): conditions with WMO code mapping.
Errors: `400` invalid coordinates · `503` (Open-Meteo unavailable) · `504` timeout.

Provider: Open-Meteo free tier — **non-commercial use only** (licensing decision pending, roadmap Phase 5).

## Resources

Static, in-code catalogue: 12 verified items across 7 categories (`advisory == 3, schemes == 3, financial == 2, digital, market, research, weather == 1 each`).

| Method | Path | Response |
|--------|------|----------|
| GET | `/api/v1/resources` | `ResourcesResponse {resources, total, categories}`; optional `?category=` filter |
| GET | `/api/v1/resources/categories` | `list[str]` |
| GET | `/api/v1/resources/{category}` | `ResourcesResponse`; `404` unknown category |

## Rate limiting & request hardening

Implemented (`middleware/rate_limit.py`, factory wiring): bounded rate limit with trusted-proxy CIDR handling (spoofed `X-Forwarded-For` from non-trusted proxies is not honored), request body size limit (`max_request_body_size`).

## Voice service (contained)

`ai/voice/` runs faster-whisper STT but is deliberately **not in Compose and not published** — no endpoints are reachable until authentication work (Phase 3) redesigns its containment.

## Contract documentation

- Machine-readable schema: `GET /docs` / `GET /openapi.json` (FastAPI default).
- Older narrative reference: `docs/backend/API.md` — verify against this file if they diverge (this file is generated from code inspection 2026-10-23).
