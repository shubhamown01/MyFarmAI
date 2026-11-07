# API Documentation (backend, verified 2026-10-23)

Base URL: `http://127.0.0.1:8000` (development, loopback binding).
All endpoints defined in `backend/app/api/v1/`. **Authentication (Phase 3+, ADR-008):** session cookie (web) or bearer access token (Android); see the auth endpoints in `backend/app/api/v1/auth.py`. Land endpoints additionally require verified status (see below). The API must not be exposed beyond loopback until the Phase 6/9 deployment gates are met.

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

## Authentication / registration (E1)

| Method | Path | Notes |
|--------|------|-------|
| POST | `/auth/register/email/request-otp` | Body `{"email"}`. Always 200 with a privacy-aware message; **additive field `delivery_mode`** (`"dev"` = no real email sent in this environment — code in `backend/data/dev_otp_outbox.txt`; future `"provider"` = real email). 429 within the 60 s resend cooldown. |
| POST | `/auth/register/email/verify` | Body `{"email","code"}`. Sets the session cookie; account becomes `pending_verification`. |

## OAuth login / signup (E2, Google + Microsoft)

Authorization-code + OIDC id_token flow. State/nonce are stored server-side (single-use, 10-min TTL).

| Method | Path | Notes |
|--------|------|-------|
| GET | `/auth/oauth/{provider}/authorize` | `provider` = `google` \| `microsoft`; `redirect_uri` required. Returns `{authorize_url, state}` — the client navigates to `authorize_url`. **503 `OAUTH_NOT_CONFIGURED`** until the owner adds client credentials (blocker B1). |
| GET | `/auth/oauth/{provider}/callback` | `code`, `state`, `redirect_uri` required. Validates state + id_token (JWKS), then login/signup with account-linking protection. **409 `OAUTH_EMAIL_TAKEN`** if a provider-verified email belongs to an ACTIVE account (no silent merge); a PENDING email-OTP user is claimed. Session cookie set; account becomes `pending_verification`. Other errors: `OAUTH_INVALID_STATE` 422, `OAUTH_TOKEN_EXCHANGE_FAILED`/`OAUTH_PROVIDER_ERROR` 502, `OAUTH_INVALID_TOKEN` 422. |

Web `redirect_uri`: `http://localhost:3000/auth/callback?provider=<provider>` in dev — this exact string must be registered as an authorized redirect URI in each provider console.

## Land registration (E4)

All land endpoints require authentication **and** `verification_status == "active"` (E3 gate; `pending_verification` → 403 `USER_NOT_VERIFIED`, `rejected` → 403 `USER_REJECTED`). Non-farm-members get 404; `VIEWER` role is read-only.

Polygons are lists of `{lat, lon}` points (NO PostGIS, owner-approved). **Area is always computed server-side** with the geodesic spherical-excess formula (`backend/app/services/geometry.py`, R = 6,371,008.8 m — same as turf.js; expect ~0.1–0.5% deviation from professional geodesic tooling). Map-measured areas are estimates, **not legal land-survey certificates**.

Unit constants: 1 hectare = 10,000 m² · 1 acre = 4,046.8564224 m². Responses include `conversions` — the area in `sq_m`, `sq_km`, `hectare`, `acre`, `sq_ft`, `sq_yd`.

### Plots

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/v1/farms/{farm_id}/plots` | `201` — `{name, land_type: home_farming\|small_outdoor\|agricultural\|other, notes?}` |
| GET | `/api/v1/farms/{farm_id}/plots` | `200` — list with boundary + latest measurement |
| GET | `/api/v1/farms/{farm_id}/plots/{plot_id}` | `200` — detail; `404` if not a member |
| PATCH | `/api/v1/farms/{farm_id}/plots/{plot_id}` | partial update (MEMBER/OWNER) |
| DELETE | `/api/v1/farms/{farm_id}/plots/{plot_id}` | `204` (MEMBER/OWNER) |

### Boundary (draw / replace)

**PUT `/api/v1/farms/{farm_id}/plots/{plot_id}/boundary`**

```json
{"polygon": [{"lat": 28.61, "lon": 77.20}, ...], "source": "map_drawn"}
```

- `source`: `map_drawn` (map polygon) or `manual_entry` (typed coordinates). Replaces the single active boundary; 3–500 points.
- Validation → `422` `INVALID_POLYGON` with an `errors` list: self-intersection, <3 unique points, duplicate consecutive vertices, near-zero area, bbox span > 5°.
- Saving a boundary records a new `FarmAreaMeasurement`: `map_measured` for `map_drawn`, `user_reported` for `manual_entry` — **the two are never conflated**.

### Manual area entry

**POST `/api/v1/farms/{farm_id}/plots/{plot_id}/area`** → `201`

```json
{"area_value": 2.5, "area_unit": "acre", "confirm": true}
```

Stored as `user_reported` (never presented as map-measured); `confirm: true` marks it farmer-confirmed.

### Home location (upsert, one per farmer)

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/v1/me/home-location` | `200` or `404` `HOME_LOCATION_NOT_SET` |
| PUT | `/api/v1/me/home-location` | upsert — `{name?, latitude, longitude, accuracy_m?, address?, city?, district?, state?, country?, postal_code?, source: auto_detected\|manual_entry\|map_pin}` |

A farmer's home location is stored separately from farms — the system never assumes the farmer lives on their farmland.

## Farmer profile & onboarding (E5)

| Method | Path | Gate | Notes |
|--------|------|------|-------|
| GET | `/api/v1/me/onboarding` | authenticated only | computed onboarding state — `{verification_status, steps: [{step, complete, detail?}], next_step, complete}`; steps in order: `contact_verified → verification → location → land → profile`. **No state table** — derived from source-of-truth records; pending users can check their own progress |
| GET | `/api/v1/me/farmer-profile` | verified | `200` or `404` `PROFILE_NOT_FOUND` |
| PUT | `/api/v1/me/farmer-profile` | verified | progressive upsert — every field optional; `profile_completed` is computed server-side (`full_name` + `farming_type` present); accepted: `full_name`, `farming_type` (home_farming\|small_outdoor\|agricultural\|other), `preferred_language`, `farming_experience_years` (0–100), `existing_crops`, `intended_crops` (≤50 names, 1–100 chars each), `soil_info`, `water_availability`, `growing_season` |

## Rate limiting & request hardening

Implemented (`middleware/rate_limit.py`, factory wiring): bounded rate limit with trusted-proxy CIDR handling (spoofed `X-Forwarded-For` from non-trusted proxies is not honored), request body size limit (`max_request_body_size`).

## Voice service (contained)

`ai/voice/` runs faster-whisper STT but is deliberately **not in Compose and not published** — no endpoints are reachable until authentication work (Phase 3) redesigns its containment.

## Contract documentation

- Machine-readable schema: `GET /docs` / `GET /openapi.json` (FastAPI default).
- Older narrative reference: `docs/backend/API.md` — verify against this file if they diverge (this file is generated from code inspection 2026-10-23).
