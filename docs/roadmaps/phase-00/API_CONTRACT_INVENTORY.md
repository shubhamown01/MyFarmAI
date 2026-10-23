# API Contract Inventory

**Phase:** 0 — read-only  
**Date:** 2026-10-21  
**Scope:** Existing HTTP surfaces and their known consumers.  
**Related:** [`CURRENT_STATE_AUDIT.md`](CURRENT_STATE_AUDIT.md), [`SECURITY_AND_PRIVACY_AUDIT.md`](SECURITY_AND_PRIVACY_AUDIT.md)

---

## 1. Method

The inventory was derived from source code and Pydantic models. No committed OpenAPI file exists. FastAPI can generate `/openapi.json` and `/docs` at runtime, but the application was not started during Phase 0, so the generated schema was not captured. Schemas below are **verified from code**, not from a live server.

Base URLs used by clients:

- Backend development: `http://localhost:8000` (web) or `http://10.0.2.2:8000` (Android emulator).
- Backend production placeholder: `https://api.myfarmai.example.com`.
- Voice service: `http://localhost:8001`.

All backend application routes except `/` and `/health` are under `/api/v1`.

## 2. Authentication and authorization

**Verified:** none. No dependency, middleware, header check, session, token, or ownership rule exists on any route. Every request is anonymous.

Consequences:

- Chat creation and continuation are open to anyone who can reach the service.
- A conversation ID is a bearer-like secret; possession allows continuation, but there is no read/list endpoint.
- No user/farm scoping exists in the database (`conversations` has no owner column).
- Rate limiting is per-IP only and can be bypassed by spoofing `X-Forwarded-For` (see security audit).

## 3. Backend endpoints

### 3.1 `GET /`

| Field | Value |
|---|---|
| Purpose | Project/version/status |
| Request | None |
| Response | `{"project":"My Farm AI","version":"0.1.0","status":"running"}` (`settings.app_version` default `0.1.0`) |
| Auth | None |
| Errors | None expected |
| Dependencies | None |
| Consumers | Web `checkHealth` does not use `/`; Android does not use `/`; no known UI consumer |
| Tests | `backend/tests/test_health.py:6-14` |
| Evidence | `backend/app/main.py:94-100` |

### 3.2 `GET /health`

| Field | Value |
|---|---|
| Purpose | Simple liveness response |
| Request | None |
| Response | `{"status":"ok","service":"backend"}` |
| Auth | None |
| Errors | None expected |
| Dependencies | None — does **not** check DB or Ollama |
| Consumers | Web/Android `checkHealth` (Android path is relative and therefore broken); not used by compose healthcheck (none exists) |
| Tests | `backend/tests/test_health.py:16-22` |
| Evidence | `backend/app/main.py:103-108`; rate-limit bypass `middleware/rate_limit.py:38-40` |

### 3.3 `GET /api/v1/health`

Same response as `/health`; versioned duplicate. Tested at `backend/tests/test_health.py:24-29`; evidence `backend/app/api/v1/health.py:6-11`.

### 3.4 `POST /api/v1/chat`

| Field | Value |
|---|---|
| Purpose | Send a message; create or continue a conversation; call local Ollama; persist messages |
| Auth | None |
| Request schema | `ChatRequest` (`backend/app/schemas/chat.py:4-38`) |
| Response schema | `ChatResponse` (`backend/app/schemas/chat.py:40-43`) |
| Dependencies | SQLite, Ollama |
| Consumers | Web `apiClient.sendMessage` (`web/src/lib/api/client.ts:80-95`); Android `apiClient.sendMessage` (`android/src/lib/api/client.ts:62-85`) |
| Tests | `backend/tests/test_chat.py` (7 tests; fail on a clean DB — see §6) |
| Evidence | `backend/app/api/v1/chat.py:15-69`; `backend/app/services/chat.py:37-78` |

**Request fields:**

| Field | Type | Required | Constraints | Notes |
|---|---|---|---|---|
| `message` | string | Yes | 1–2000 chars; trimmed; non-whitespace | Pydantic `min_length`/`max_length` + validator |
| `conversation_id` | string or null | No | No UUID validation, no max length | Any string is accepted and queried; missing row → 404 |
| `language` | string | No | Regex `^[a-z]{2}$`; default `en` | Two lowercase letters only |
| `crop` | string or null | No | ≤100 chars | Context only |
| `location` | string or null | No | ≤200 chars | Context only; potential indirect PII |

**Response:** `{"response": string, "conversation_id": string, "model": string}`. `model` is the configured model name, not the model digest/version.

**Behavioral notes:**

- If `conversation_id` is omitted, a conversation is created before the model call.
- The user message is persisted **before** the Ollama call (`services/chat.py:58`). On failure, an assistant error message is persisted and the request returns 503/504.
- When continuing a conversation, `language`, `crop`, and `location` are taken from the current request, not from stored conversation metadata. Clients that omit them on follow-up lose context and default to English.
- History is the last 10 messages ordered by `created_at` (second resolution). Ties can reorder messages; there is no `id` tie-breaker (`db/conversations.py:75-96`).
- No streaming; the client waits up to 120 s.
- No idempotency key; retries can duplicate user messages.

**Declared error responses:**

| Status | Code | Condition | Actual body shape |
|---|---|---|---|
| 404 | `CONVERSATION_NOT_FOUND` | `conversation_id` does not exist | `{"detail":{"detail":"...","error_code":"CONVERSATION_NOT_FOUND"}}` |
| 503 | `MODEL_NOT_FOUND` | Ollama returns 404 for the model | Same nested shape |
| 503 | `OLLAMA_CONNECTION_FAILED` | Connection error | Same nested shape |
| 504 | `OLLAMA_TIMEOUT` | Timeout | Same nested shape |
| 500 | `INTERNAL_ERROR` | Unexpected exception | Same nested shape |
| 422 | Pydantic validation | Invalid body | FastAPI default `{"detail":[...]}` |

**Contract defect:** the `responses` models (`ErrorResponse` with flat `detail` + `error_code`) and `docs/backend/API.md` describe a flat error object, but handlers raise `HTTPException(detail={...})`, which nests it. Web handles both shapes (`web/src/lib/api/client.ts:52-65`); Android only reads `error.detail` and will display `[object Object]` for these errors (`android/src/lib/api/client.ts:41-47`).

### 3.5 `GET /api/v1/weather`

| Field | Value |
|---|---|
| Purpose | Current weather + 7-day daily forecast |
| Auth | None |
| Query params | `latitude` float, required, −90..90; `longitude` float, required, −180..180; `current` bool default true; `daily` bool default true |
| Response schema | `WeatherResponse` (`backend/app/schemas/weather.py:39-52`) |
| Dependencies | Open-Meteo over HTTPS |
| Consumers | Web `getWeather` (`web/src/lib/api/client.ts:97-106`); Android `getWeather` (`android/src/lib/api/client.ts:87-104`) |
| Tests | `backend/tests/test_weather.py` (mocked service; 10 tests) |
| Evidence | `backend/app/api/v1/weather.py:13-53`; `backend/app/services/weather.py:56-134` |

**Response fields:** `latitude`, `longitude`, `generationtime_ms`, `utc_offset_seconds`, `timezone`, `timezone_abbreviation`, `elevation`, optional `current_weather` (`temperature`, `windspeed`, `winddirection`, `weathercode`, `weather_description`, `time`), optional `daily[]` (`date`, `temperature_2m_max`, `temperature_2m_min`, `precipitation_sum`, `precipitation_probability_max`, `weathercode`, `weather_description`).

**Degraded behavior:** on timeout → 504 `WEATHER_TIMEOUT`; connection error → 503 `WEATHER_CONNECTION_FAILED`; other errors → 500 `INTERNAL_ERROR`. No cache is used despite `weather_cache_ttl_seconds`; every request calls Open-Meteo. No attribution field is returned to the client.

**Tests gap:** tests mock `get_weather`, so they do not test real Open-Meteo shape changes, rate limits, attribution, or caching.

### 3.6 `GET /api/v1/weather/current`

Same schema; calls Open-Meteo with `include_daily=False`. Consumers: Web `getCurrentWeather`; Android `getCurrentWeather`; tests `test_weather.py:157-174`; evidence `backend/app/api/v1/weather.py:56-94`.

### 3.7 `GET /api/v1/resources`

| Field | Value |
|---|---|
| Purpose | Static catalogue of 12 Indian agricultural resources |
| Auth | None |
| Query params | `category` optional, case-insensitive exact match |
| Response schema | `ResourcesResponse` (`backend/app/schemas/resources.py:16-19`) |
| Dependencies | None (in-memory static list) |
| Consumers | Web `getResources`; Android `getResources`; `ResourcesList.tsx` |
| Tests | `backend/tests/test_resources.py` (12 tests) |
| Evidence | `backend/app/api/v1/resources.py:9-31`; `backend/app/services/resources.py:3-112` |

**Response:** `{"resources":[{"title","category","url","source","description"}],"total":int,"categories":[string]}`.

**Behavior:** unknown category returns 200 with an empty list. The separate path route returns 404 for an unknown category, so `/resources?category=x` and `/resources/x` disagree.

### 3.8 `GET /api/v1/resources/categories`

Returns `string[]`; source categories are `advisory`, `digital`, `financial`, `market`, `research`, `schemes`, `weather`. Evidence `backend/app/api/v1/resources.py:34-39`; tests `test_resources.py:83-92`.

### 3.9 `GET /api/v1/resources/{category}`

Returns `ResourcesResponse` or 404 `CATEGORY_NOT_FOUND` (nested shape). Evidence `backend/app/api/v1/resources.py:42-66`; tests `test_resources.py:94-106`.

## 4. Voice service endpoints

| Method | Path | Request | Response | Auth | Limits | Evidence |
|---|---|---|---|---|---|---|
| GET | `/health` | None | `{"service":"voice","status":"ok"}` | None | None | `ai/voice/main.py:12-17` |
| POST | `/transcribe` | multipart file | `{"language":"hi","text":string}` | None | **No file size, type, duration, or rate limit** | `ai/voice/main.py:20-53` |

**Implementation facts:** Whisper model `small`, CPU, `int8`, language hard-coded to Hindi at `ai/voice/main.py:37-40`. The returned `info.language` may differ from the forced language. Filename suffix is used for the temp file; content type is not validated. Temp file is deleted in `finally`.

**Consumers:** none in the backend; no web/Android call to `/transcribe` was found. The container is published on `0.0.0.0:8001`.

## 5. Consumer mapping

| Consumer | Chat | Weather | Current weather | Resources | Categories | Health | Voice |
|---|---|---|---|---|---|---|---|
| Web | Yes | Yes | Yes | Yes | Yes | Yes | No |
| Android | Yes (broken URL) | Yes (broken URL) | Yes (broken URL) | Yes (broken URL) | Yes (broken URL) | Yes (broken URL) | No |
| Backend itself | — | Open-Meteo | Open-Meteo | Static | Static | — | Configured but unused |
| Tests | Mocked Ollama | Mocked client | Mocked client | In-memory | In-memory | Real app | None |

## 6. Contract risks

| ID | Risk | Evidence | Impact | Breaking-change risk | Recommendation |
|---|---|---|---|---|---|
| API-C-01 | Flat vs nested error body | `chat.py:39-69`, `weather.py:36-53`, `schemas/chat.py:45-47` | Clients must parse two shapes; Android displays `[object Object]` | Changing to flat would break web if it only expected nested; web already handles both | Standardise before 1.0; add a contract test. Prefer one documented shape and update both clients. |
| API-C-02 | No auth/ownership | All routes | Anonymous abuse; cross-user access if IDs leak | Adding auth is a breaking change for clients | Introduce auth before public exposure; version or coordinate with clients. |
| API-C-03 | `conversation_id` not validated | `schemas/chat.py:9-12` | Arbitrary-length strings hit DB; 404 oracle | Low | Add UUID/length validation (still accept legacy IDs if any). |
| API-C-04 | Android uses relative URLs | `android/src/lib/api/client.ts:29`; `android/src/config/api.ts:10-18` | Android cannot reach backend | Fix is non-breaking to API | Prefix with configured base URL; add integration test. |
| API-C-05 | Follow-up context reset | `services/chat.py:44-55` | Language/crop/location lost if clients omit them | Server-side fix can preserve behavior | Load stored context when continuing, or require context each call. |
| API-C-06 | Message ordering ties | `db/conversations.py:75-96` | Model receives messages out of order | No API change | Order by `(created_at, id)` or use a monotonic sequence; migrate to `TIMESTAMPTZ`. |
| API-C-07 | No idempotency | `services/chat.py:58` | Retry duplicates user messages | Additive header/field | Add idempotency key in a later phase. |
| API-C-08 | Version drift | `config.py:7` (0.1.0) vs `docs/backend/API.md` (0.2.0) | Misleading clients/docs | Low | Single source of truth for version. |
| API-C-09 | Weather contract depends on upstream | `services/weather.py:93-134` | Upstream field changes can cause 500s | External | Validate upstream schema; contract tests with fixtures; cache. |
| API-C-10 | No OpenAPI artifact | No `openapi.json` | No reviewable contract; client drift | Additive | Generate and commit/review in CI. |
| API-C-11 | Resource category semantics differ | `resources.py:22-31` vs `42-66` | Inconsistent 200/404 behavior | Changing path route could break clients | Document intended behavior; align in a versioned change. |
| API-C-12 | Voice contract unversioned/unsecured | `ai/voice/main.py` | Cannot safely expose | Additive/hardening | Put behind backend/auth or remove from MVP. |

## 7. Tests and verification

| Test file | Count | Scope | Result in clean-DB run |
|---|---:|---|---|
| `test_health.py` | 3 | `/`, `/health`, `/api/v1/health` | Pass |
| `test_chat.py` | 7 | Chat success, continuation, validation, Ollama errors | **7 fail** (no schema in isolated DB; test client does not run startup lifespan) |
| `test_weather.py` | 10 | Mocked weather success/errors/bounds | Pass |
| `test_resources.py` | 12 | Catalogue/filter/categories | Pass |
| `test_schemas.py` | 12 | Pydantic validation | Pass |
| `test_database.py` | 9 | Temp DB CRUD/limits/isolation | Pass |
| **Total** | **56** | | **49 pass / 7 fail** |

This is a test-isolation defect, not evidence that the chat code is broken in the existing dev environment. See [`VERIFICATION_REPORT.md`](VERIFICATION_REPORT.md).

## 8. Unknowns

- The generated OpenAPI schema was not captured; response examples beyond source models are not verified.
- No production client build was run; Android behavior is inferred from source (relative `fetch`) and is a strong, verified code defect.
- No live request was made to Ollama, Open-Meteo, or the voice service. Timeout/latency behavior is based on code and configuration, not measured here.
- Whether any external consumer relies on the current nested error shape is unknown.
