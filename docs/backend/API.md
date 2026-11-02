# MyFarm AI Backend — API Reference

**Version:** 0.1.0 (aligned with `settings.app_version`)  
**Date:** 2026-10-28  
**Status:** Phase 1 Complete

---

## Base URL

- **Development:** `http://localhost:8000`
- **Production:** `https://api.myfarmai.example.com` (requires Caddy + Phase 8)

All API routes are prefixed with `/api/v1`.

---

## Authentication

**Implemented (Phase 3, ADR-008):** all chat endpoints require authentication; other v1 endpoints require auth per `docs/engineering/AUTHZ_MATRIX.md`.

- **Web:** opaque session ID in `HttpOnly, Secure (production), SameSite=Lax` cookie; only the SHA-256 hash is stored server-side
- **Android:** `Authorization: Bearer <session_id>` + single-use rotating refresh token with reuse detection (reuse revokes the whole chain and all user sessions)
- Accounts are admin-created (`POST /api/v1/auth/admin/users`); public self-registration is available via passwordless email OTP (below; introduced E1)
- Protections: per-IP rate limits (stricter on `/api/v1/auth/*`), trusted-proxy-aware client IP, per-account lockout (5 fails / 15 min → 429), Origin/Referer enforcement on cookie-carrying unsafe requests, Argon2id password hashing
- See `docs/product/flows/AUTHENTICATION_FLOW.md` for the full flows

### Authentication — Passwordless Email Registration (E1)

Public email signup with one-time-code verification. The user never sets a password; the account activates only after successful verification.

#### `POST /api/v1/auth/register/email/request-otp`

```json
{ "email": "farmer@example.com" }
```

- **200** → `{ "message": "If the email address is valid, a verification code has been sent." }` — **privacy-aware**: the response is identical whether or not the address was already registered.
- If the email is unknown, a **pending user** is created (`is_active=false`, `email_verified=false`, unusable random password) plus an `authentication_accounts` row (`provider='email_otp'`).
- Code: 6 digits, Argon2id-hashed at rest, 10-minute expiry, single-use (consumed on success), max 5 attempts.
- Resend cooldown: 60 s per destination.
- **429** `OTP_RESEND_COOLDOWN` + `Retry-After: 60` header if requested inside the cooldown window (429 chosen over 422 because it is a rate/abuse signal, not a validation error).
- **422** with FastAPI's default validation body (`{"detail": [...]}` — no `error_code`; the flat envelope applies to HTTPException paths only) for malformed input (invalid email or non-6-digit code).

> **DEV-MODE DELIVERY WARNING:** no email provider is configured yet (owner-approved decision, 2026-11-01). Codes are **not actually delivered** — they are logged (`DEV-MODE OTP — NOT ACTUALLY DELIVERED`) and, best-effort, appended to `/tmp/opencode/dev_otp_outbox.txt`. Swap via `email_delivery_mode` config; never treat dev-mode output as real delivery.

#### `POST /api/v1/auth/register/email/verify`

```json
{ "email": "farmer@example.com", "code": "123456" }
```

- **200** → `LoginResponse` (same shape as login) + web session cookie set exactly as login. The user is activated (`email_verified=true`, `is_active=true`) and logged in.
- **422** `OTP_INVALID` — wrong code or no pending verification for this address (attempts increment; persisted even on the error response).
- **422** `OTP_EXPIRED` — code older than 10 minutes.
- **422** `OTP_MAX_ATTEMPTS` — 5 wrong codes consumed; the row can no longer be verified (request a new code after the cooldown).
- Pending (never-verified) users **cannot** log in via `/login` — activation happens only through verification.

Phone (SMS) registration is **not yet exposed**: the delivery-adapter interface exists (`UnavailableSmsDelivery`) and reports "temporarily unavailable" per the owner-approved plan until an approved provider is configured.

New tables (owner-approved staged schema, migration `b3f2a5d1c7e4`): `authentication_accounts`, `contact_verifications`.

### Authentication — OAuth (E2)

OIDC authorization-code login/signup for **Google** and **Microsoft**. Providers are **disabled until the owner creates the OAuth apps** (client id/secret via env: `oauth_google_client_id/secret`, `oauth_microsoft_client_id/secret`) — both endpoints then return **503 `OAUTH_NOT_CONFIGURED`**.

#### `GET /api/v1/auth/oauth/{provider}/authorize?redirect_uri=...`

- **200** → `{"authorize_url": "...", "state": "..."}` — redirect the user to `authorize_url`. The server generates `state` + `nonce` (`secrets.token_urlsafe(32)`); nonce is embedded in the authorize URL and stored server-side keyed by state (10-min TTL, single use).
- **503** `OAUTH_NOT_CONFIGURED` — unknown or unconfigured provider.
- **Single-process limitation:** state/nonce live in an in-memory store; restarting the backend mid-flow invalidates pending OAuth attempts. Acceptable for the single-process deployment; revisit for multi-worker/multi-node.

#### `GET /api/v1/auth/oauth/{provider}/callback?code=&state=&redirect_uri=...`

Verification per directive §4.1: id_token **signature** (JWKS, cached 1 h), **audience** (`client_id`), **issuer** (Google exact match; Microsoft tenant-varying predicate), **nonce** (consumed with the state), expiry.

- **200** → `LoginResponse` + web session cookie (same as login/verify). Account resolution with **linking protection**:
  - Existing `(provider, subject)` link → login (must be active).
  - Email matches an **active** account → **409 `OAUTH_EMAIL_TAKEN`** — the account is NEVER silently merged; the user logs in with their existing method.
  - Email matches a **pending** email-OTP user → claimed: activated, `email_verified=true`, linked (provider-verified email).
  - No match → new active, verified user + link.
- Errors (flat envelope): **422** `OAUTH_INVALID_STATE` (unknown/expired/replayed state), **422** `OAUTH_INVALID_TOKEN` (signature/audience/issuer/nonce/exp failure), **502** `OAUTH_TOKEN_EXCHANGE_FAILED` (token endpoint non-200), **502** `OAUTH_PROVIDER_ERROR` (JWKS/transport).
- **Mocked-IdP tests:** the full signature-verification path is tested against an in-test RSA keypair over `httpx.MockTransport` — zero network; live IdP verification is deferred until owner credentials exist.

**Dependencies:** `pyjwt` (MIT) + `cryptography` (Apache-2.0) — classified in `docs/engineering/DEPENDENCY_POLICY.md` (CORE-SELF-HOSTED, ₹0).

### Verification — Selfie (E3 wave 1)

Mandatory live-selfie onboarding step (directive §5; binding security requirements in `docs/backend/E3_SELFIE_SECURITY_REVIEW.md`). **No automated liveness is claimed** at 2 GiB VRAM: the server issues a randomized 2-action challenge, the capture is taken during the challenge, and a **human manual-review queue** decides. Accounts created via email-OTP or OAuth signup now carry `verification_status = 'pending_verification'` (sessions work; feature gating via `require_verified_user` arrives with later waves). Admin-created users keep `'active'`.

#### `POST /api/v1/verification/selfie/consent`

Records explicit informed consent (type `selfie_liveness`, policy version, client IP) → `{"status": "granted"}`. **Required before challenge issuance.**

#### `POST /api/v1/verification/selfie/challenge`

- Preconditions: `verification_status == 'pending_verification'` (else **409 `NOT_PENDING`**); consent exists (else **409 `CONSENT_REQUIRED`**); ≤ 10 challenges/hour/user (else **429 `RATE_LIMITED`**).
- **200** → `{challenge_id, actions: [<2 random actions>], expires_in: 300}` — single-use, session-bound (user-scoped), 5-minute TTL; issuing a new challenge invalidates the previous unconsumed one.

#### `POST /api/v1/verification/selfie/upload` (multipart: `file`, `challenge_id`)

Validation order: pending status (409) → consent (409) → challenge consume (**422 `CHALLENGE_INVALID`** — invalid/expired/replayed/wrong-user) → magic-byte sniff JPEG/PNG (**415 `UNSUPPORTED_MEDIA_TYPE`**) → ≤ 5 MiB (**413**) → dimensions 512–4096 px (**422 `IMAGE_DIMENSIONS`**) → server-side re-encode **stripping all metadata (EXIF/GPS)** → stored **outside the repo and web roots** (0700 directory, uuid filename, 0600 file).
- **200** → `{"status": "received", "review_state": "pending_review"}` — **no path, filename, or URL is ever returned**; raw bytes are only ever accessible through an authenticated admin streaming endpoint (wave 2).
- An upload NEVER changes `verification_status` — only manual review (wave 2) does. A failed/abandoned capture keeps the account in `pending_verification` (never silently bypassed).

**Privacy/retention:** EXIF/GPS stripped at ingest; raw file deleted after the review decision (wave 2); only the decision + audit events persist; selfies are never used for training or advertising. `pillow` (HPND/MIT-style, ₹0) classified in DEPENDENCY_POLICY for re-encode/EXIF strip.

---

## Endpoints

### 1. Root Information

**GET** `/`

Returns basic project information.

#### Response (200 OK)

```json
{
  "project": "My Farm AI",
  "version": "0.1.0",
  "status": "running"
}
```

---

### 2. Health Check (Root — Liveness)

**GET** `/health`

Simple liveness probe — returns 200 if process is running.

#### Response (200 OK)

```json
{
  "status": "ok",
  "service": "backend",
  "check_type": "liveness"
}
```

---

### 3. Health Check (Liveness — Explicit)

**GET** `/health/live`

Explicit liveness probe — identical to `/health` for Kubernetes compatibility.

#### Response (200 OK)

```json
{
  "status": "ok",
  "service": "backend",
  "check_type": "liveness"
}
```

---

### 4. Health Check (Readiness)

**GET** `/health/ready`

Readiness probe — checks database and Ollama connectivity with short timeouts.

#### Response (200 OK — All Deps Healthy)

```json
{
  "status": "ok",
  "service": "backend",
  "check_type": "readiness",
  "dependencies": {
    "database": "ok",
    "ollama": "ok"
  }
}
```

#### Response (503 Service Unavailable — Degraded)

```json
{
  "status": "degraded",
  "service": "backend",
  "check_type": "readiness",
  "dependencies": {
    "database": "ok",
    "ollama": "unreachable"
  }
}
```

---

### 5. Health Check (Versioned)

**GET** `/api/v1/health`

Versioned health check endpoint — same as root `/health`.

#### Response (200 OK)

```json
{
  "status": "ok",
  "service": "backend"
}
```

---

### 6. Chat with AI Assistant

**POST** `/api/v1/chat`

Send a message to the agricultural AI assistant and receive a response. Supports conversation continuity.

#### Request Body

```json
{
  "message": "string (required, 1-2000 chars)",
  "conversation_id": "string (optional, UUID v4)",
  "language": "string (optional, ISO 639-1, default: 'en')",
  "crop": "string (optional, max 100 chars)",
  "location": "string (optional, max 200 chars)"
}
```

| Field | Required | Type | Constraints | Description |
|-------|----------|------|-------------|-------------|
| `message` | Yes | string | 1-2000 chars, non-empty | Farmer's question or message |
| `conversation_id` | No | string | UUID v4 format | Existing conversation to continue |
| `language` | No | string | 2-letter code (e.g., 'en', 'hi') | Response language |
| `crop` | No | string | max 100 chars | Current crop for context |
| `location` | No | string | max 200 chars | Farmer's location for localized advice |

#### Example Request

```json
{
  "message": "What fertilizer should I use for wheat in Punjab?",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "language": "en",
  "crop": "wheat",
  "location": "Punjab, India"
}
```

#### Success Response (200 OK)

```json
{
  "response": "For wheat in Punjab, the recommended fertilizer depends on soil type and local conditions. Generally: 1) Nitrogen: 120-150 kg/ha split in 3 doses... 2) Phosphorus: 60-80 kg/ha as basal... 3) Potassium: 40-60 kg/ha... Important: Get a soil test for precise recommendations. Consult your local Krishi Vigyan Kendra for region-specific advice.",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "model": "qwen3:0.6b"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | AI assistant's response |
| `conversation_id` | string | Conversation UUID (new or continued) |
| `model` | string | Ollama model used (e.g., "qwen3:0.6b") |

---

### 7. Weather Information

**GET** `/api/v1/weather`

Get current weather and 7-day forecast for a location using Open-Meteo.

#### Query Parameters

| Parameter | Required | Type | Constraints | Description |
|-----------|----------|------|-------------|-------------|
| `latitude` | Yes | float | -90.0 to 90.0 | Latitude in decimal degrees |
| `longitude` | Yes | float | -180.0 to 180.0 | Longitude in decimal degrees |
| `current` | No | bool | default: true | Include current weather |
| `daily` | No | bool | default: true | Include 7-day daily forecast |

#### Example Request

```
GET /api/v1/weather?latitude=28.6139&longitude=77.2090&current=true&daily=true
```

#### Success Response (200 OK)

```json
{
  "latitude": 28.6139,
  "longitude": 77.2090,
  "generationtime_ms": 0.427,
  "utc_offset_seconds": 19800,
  "timezone": "Asia/Kolkata",
  "timezone_abbreviation": "GMT+5:30",
  "elevation": 214.0,
  "current_weather": {
    "temperature": 28.5,
    "windspeed": 3.6,
    "winddirection": 333,
    "weathercode": 0,
    "weather_description": "Clear sky",
    "time": "2026-10-28T16:15"
  },
  "daily": [
    {
      "date": "2026-10-28",
      "temperature_2m_max": 28.8,
      "temperature_2m_min": 20.3,
      "precipitation_sum": 0.0,
      "precipitation_probability_max": 0,
      "weathercode": 0,
      "weather_description": "Clear sky"
    },
    {
      "date": "2026-10-29",
      "temperature_2m_max": 30.1,
      "temperature_2m_min": 21.0,
      "precipitation_sum": 2.5,
      "precipitation_probability_max": 30,
      "weathercode": 61,
      "weather_description": "Slight rain"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `latitude` | float | Requested latitude |
| `longitude` | float | Requested longitude |
| `generationtime_ms` | float | API response generation time |
| `utc_offset_seconds` | int | Timezone offset from UTC |
| `timezone` | string | IANA timezone identifier |
| `timezone_abbreviation` | string | Timezone abbreviation |
| `elevation` | float | Elevation in meters |
| `current_weather` | object | Current weather conditions (optional) |
| `daily` | array | 7-day forecast array (optional) |

#### Current Weather Object

| Field | Type | Description |
|-------|------|-------------|
| `temperature` | float | Air temperature at 2m in °C |
| `windspeed` | float | Wind speed at 10m in km/h |
| `winddirection` | int | Wind direction in degrees |
| `weathercode` | int | WMO weather condition code |
| `weather_description` | string | Human-readable weather description |
| `time` | string | Observation time in ISO 8601 |

#### Daily Forecast Object

| Field | Type | Description |
|-------|------|-------------|
| `date` | string | Date in YYYY-MM-DD |
| `temperature_2m_max` | float | Maximum temperature in °C |
| `temperature_2m_min` | float | Minimum temperature in °C |
| `precipitation_sum` | float | Total precipitation in mm |
| `precipitation_probability_max` | int | Max precipitation probability in % |
| `weathercode` | int | WMO weather condition code |
| `weather_description` | string | Human-readable weather description |

#### Weather Codes (WMO)

| Code | Description |
|------|-------------|
| 0 | Clear sky |
| 1 | Mainly clear |
| 2 | Partly cloudy |
| 3 | Overcast |
| 45 | Fog |
| 48 | Depositing rime fog |
| 51-57 | Drizzle (light to dense, freezing) |
| 61-67 | Rain (slight to heavy, freezing) |
| 71-77 | Snow fall (slight to heavy, grains) |
| 80-82 | Rain showers (slight to violent) |
| 85-86 | Snow showers (slight to heavy) |
| 95-99 | Thunderstorm (with/without hail) |

---

### 8. Current Weather Only

**GET** `/api/v1/weather/current`

Get only current weather (no forecast).

#### Query Parameters

| Parameter | Required | Type | Constraints | Description |
|-----------|----------|------|-------------|-------------|
| `latitude` | Yes | float | -90.0 to 90.0 | Latitude in decimal degrees |
| `longitude` | Yes | float | -180.0 to 180.0 | Longitude in decimal degrees |

#### Example Request

```
GET /api/v1/weather/current?latitude=28.6139&longitude=77.2090
```

#### Success Response (200 OK)

Same as `/api/v1/weather` but with `daily` set to `null`.

---

### 9. Agricultural Resources

**GET** `/api/v1/resources`

Get curated list of agricultural resources for Indian farmers.

#### Query Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `category` | No | string | Filter by category (e.g., 'schemes', 'advisory', 'market', 'weather', 'research', 'financial', 'digital') |

#### Example Request

```
GET /api/v1/resources?category=schemes
```

#### Success Response (200 OK)

```json
{
  "resources": [
    {
      "title": "PM-KISAN - Pradhan Mantri Kisan Samman Nidhi",
      "category": "schemes",
      "url": "https://pmkisan.gov.in",
      "source": "Ministry of Agriculture & Farmers Welfare",
      "description": "Income support scheme providing Rs. 6000/year to eligible farmer families."
    },
    ...
  ],
  "total": 12,
  "categories": ["advisory", "digital", "financial", "market", "research", "schemes", "weather"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `resources` | array | Array of resource objects |
| `total` | int | Total number of resources returned |
| `categories` | array | List of all available categories |

#### Resource Object

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Resource title |
| `category` | string | Resource category |
| `url` | string | Resource URL |
| `source` | string | Source organization |
| `description` | string | Short factual description |

---

### 10. List Categories

**GET** `/api/v1/resources/categories`

Get list of all available resource categories.

#### Example Request

```
GET /api/v1/resources/categories
```

#### Success Response (200 OK)

```json
["advisory", "digital", "financial", "market", "research", "schemes", "weather"]
```

---

### 11. Resources by Category (Path Parameter)

**GET** `/api/v1/resources/{category}`

Get resources filtered by category via path parameter.

#### Path Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `category` | Yes | string | Category name (e.g., 'schemes', 'advisory') |

#### Example Request

```
GET /api/v1/resources/schemes
```

#### Success Response (200 OK)

Same structure as `/api/v1/resources` but filtered.

#### Error Response (404 Not Found)

```json
{
  "detail": "Category 'invalid' not found",
  "error_code": "CATEGORY_NOT_FOUND",
  "request_id": "3f0c...",
  "errors": null
}
```

---

## Farms (P5A-01)

Farm CRUD and membership management. All endpoints require authentication. Authorization is deny-by-default:

- Non-members get `404 FARM_NOT_FOUND` (farm existence is not leaked).
- Roles: `owner` (creator), `member` (read + update farm fields), `viewer` (read-only).
- Member management (add/remove/role change) requires the `owner` role.
- Farm ownership is fixed to the creator; the owner member cannot be removed or demoted.

**POST** `/api/v1/farms`

```json
{
  "name": "North Field",
  "description": "optional",
  "address": "optional, max 500 chars",
  "latitude": 28.61,
  "longitude": 77.20,
  "timezone": "UTC"
}
```

Latitude must be −90..90 and longitude −180..180 (422 otherwise). Creates the farm and an owner membership for the caller. Returns `201` with the farm object (`id`, `name`, `description`, `address`, `latitude`, `longitude`, `timezone`, `owner_id`, `is_active`, `created_at`).

**GET** `/api/v1/farms` — farms the caller belongs to (newest first).

**GET** `/api/v1/farms/{farm_id}` — one farm; `404 FARM_NOT_FOUND` for non-members.

**PATCH** `/api/v1/farms/{farm_id}` — partial update of any creation field (+ `is_active`); requires `owner` or `member`. `403 FARM_FORBIDDEN` for viewers.

**GET** `/api/v1/farms/{farm_id}/members` — member list (`id`, `user_id`, `role`, `joined_at`).

**POST** `/api/v1/farms/{farm_id}/members` — owner only. Body: `{"user_id": "<uuid>", "role": "member" | "viewer"}`. `404 USER_NOT_FOUND` for unknown users; `403` if already a member; `422` for `role: "owner"`.

**PATCH** `/api/v1/farms/{farm_id}/members/{user_id}` — owner only. Body: `{"role": "member" | "viewer"}`.

**DELETE** `/api/v1/farms/{farm_id}/members/{user_id}` — owner only; `204`; `403` when targeting the farm owner.

---

## Farm Dashboard (P7A)

**GET** `/api/v1/dashboard?farm_id=<uuid>` — read-only aggregation of farm intelligence for the caller's farm. Requires authentication; farm members only (roles: owner/member/viewer); non-members get `404 FARM_NOT_FOUND` (no existence leak). Errors use the flat ADR-009 envelope.

Each block carries `available` (bool) and `updated_at`; blocks that can fail also carry `unavailable_reason`. Blocks degrade independently — one unavailable source never fails the request.

- `farm` — name, timezone, address, latitude, longitude.
- `crops` — active crop cycles (`crop`, `status`, `season_year`, `planting_date`, `expected_harvest_date`).
- `weather` — current conditions from Open-Meteo (fail-open: unavailable when the farm has no coordinates or the provider is down; reason given).
- `tasks` — upcoming expected-harvest windows derived from real cycle dates only.
- `alerts` — derived locally from real state (weather unavailable, no active cycles, passed harvest window).
- `recommendations` — currently `available: false` ("Saved recommendations are not available yet") — feature not built; shown as an honest empty state.
- `activity` — the caller's own 20 most recent audit events (never another user's).

No model inference is involved; no invented statistics are returned.

---

## Crop Plans (P7B)

Crop planning with seasonal milestones and farmer-controlled tasks. All endpoints require authentication; farm members only (denying by default — non-members get `404 FARM_NOT_FOUND`). Errors use the flat ADR-009 envelope. Viewer role is read-only; mutations require `owner` or `member`.

Milestones are **estimates derived locally** from `planting_date` + the crop's generic `growing_days_min`/`growing_days_max` — no external services, no invented data. Every plan response carries `assumptions` (rendered verbatim by clients): *"Milestones are estimates from generic growing-day ranges for the crop — variety, local climate and soil are not accounted for unless data exists."* No fertilizer or chemical quantities exist anywhere in this feature.

**Farmer decisions are never silently overwritten:** tasks created via the API are always `source: "user"` (the system cannot re-attribute or auto-modify them); task "deletion" is a soft cancel (`status: "cancelled"`) — history is preserved; every plan mutation appends an immutable revision recording the plan state **before** the change (`GET .../revisions`, oldest first).

**POST** `/api/v1/farms/{farm_id}/crop-plans`

```json
{
  "crop_cycle_id": "optional uuid — must belong to this farm",
  "variety": "optional, max 100 chars",
  "planting_date": "2026-06-01",
  "tasks": [{"title": "Buy seeds", "due_date": "2026-05-25"}]
}
```

Returns `201` with the plan. A revision (`"plan created"`) is recorded. `422 CROP_PLAN_INVALID` if `crop_cycle_id` references a cycle on another farm. With a linked cycle + planting date, `milestones` are derived (sowing date + earliest/latest harvest windows); without them, `milestones` is empty — never invented.

**GET** `/api/v1/farms/{farm_id}/crop-plans` — plans for the farm (newest first).

**GET** `/api/v1/crop-plans/{plan_id}` — plan detail (tasks included); `404 CROP_PLAN_NOT_FOUND` for non-members.

**PATCH** `/api/v1/crop-plans/{plan_id}` — partial update of `variety`, `planting_date`, `crop_cycle_id` (must belong to the farm). A revision with a before-change snapshot is appended automatically.

**GET** `/api/v1/crop-plans/{plan_id}/revisions` — append-only history: `[{id, changed_by, summary, snapshot, created_at}]`.

**POST** `/api/v1/crop-plans/{plan_id}/tasks` — `{title, due_date?}` → `201` (source always `user`).

**PATCH** `/api/v1/crop-plans/{plan_id}/tasks/{task_id}` — `{title?, due_date?, status?}` with `status` in `pending | done | cancelled`. `source` is immutable. Task-not-found is indistinguishable from plan-not-found (no existence leak).

---

## Crop Cycles (P5A-02)

Crop-cycle records (a crop growing season on a farm). All endpoints require authentication; authorization is farm-membership-scoped (deny-by-default, `404 CROP_CYCLE_NOT_FOUND` for non-members). Create/update require `owner` or `member`; viewers read-only.

**POST** `/api/v1/farms/{farm_id}/crop-cycles`

```json
{
  "crop_id": "<uuid>",
  "season_year": 2026,
  "season_name": "kharif (optional)",
  "planting_date": "2026-06-15 (optional)",
  "expected_harvest_date": "2026-10-15 (optional)",
  "area_hectares": 1.5,
  "expected_yield_kg": 4200,
  "notes": "optional"
}
```

Returns `201` with the cycle (status starts at `planned`). Errors: `404 CROP_NOT_FOUND` (unknown crop), `409 CROP_CYCLE_CONFLICT` (a cycle for the same crop + season_year already exists on the farm), `422` validation.

**GET** `/api/v1/farms/{farm_id}/crop-cycles?status=planted` — farm's cycles, newest season first, optional status filter.

**GET** `/api/v1/crop-cycles/{cycle_id}` — one cycle; non-members get `404`.

**PATCH** `/api/v1/crop-cycles/{cycle_id}` — partial update (fields, yields, dates, `status`). Status transitions are forward-only: `planned → planted → growing → harvested → archived`, any active state may become `failed` or `archived`, `archived` is terminal. Invalid transitions → `422 CROP_CYCLE_INVALID_TRANSITION`. Viewers → `403 FARM_FORBIDDEN`.

---

## Conversations (P5G)

Read-only conversation-history API. All endpoints require authentication; retrieval is user-scoped at the repository level (deny-by-default — cross-user access returns `404 CONVERSATION_NOT_FOUND`, per ADR-008).

**GET** `/api/v1/conversations?limit=20` — the authenticated user's non-archived conversations, newest first (`limit` 1–100, default 20).

```json
[
  {
    "id": "<uuid>",
    "language": "en",
    "crop": "tomato (or null)",
    "location": "text (or null)",
    "farm_id": "<uuid (or null)>",
    "created_at": "2026-10-31T12:00:00Z",
    "updated_at": "2026-10-31T12:05:00Z"
  }
]
```

**GET** `/api/v1/conversations/{conversation_id}` — one conversation with its messages (most recent 50, oldest-first). Non-owner or unknown id → `404 CONVERSATION_NOT_FOUND`. Malformed id → `422`.

```json
{
  "id": "<uuid>",
  "language": "en",
  "crop": null,
  "location": null,
  "farm_id": null,
  "created_at": "2026-10-31T12:00:00Z",
  "updated_at": "2026-10-31T12:05:00Z",
  "messages": [
    { "id": 1, "role": "user", "content": "…", "created_at": "…" },
    { "id": 2, "role": "assistant", "content": "…", "created_at": "…" }
  ]
}
```

Note: message `id` is an integer (the `messages` table uses an Integer autoincrement PK; only conversations are UUID-keyed). No create/update/delete endpoints — conversations and messages are written exclusively by the chat flow (P3-05); archival is via the chat service. Retention behavior is interim pending ADR-015.

---

## Voice Capabilities (P5F / ADR-016)

**GET** `/api/v1/voice/capabilities` — capability discovery. Requires authentication.

```json
{
  "server_stt": false,
  "server_tts": false,
  "client_platform_voice": true,
  "recommended_languages": ["en", "hi"],
  "note": "MVP voice uses client-platform speech APIs (ADR-016). Send recognized text as an ordinary chat message; no audio is accepted or stored server-side.",
  "environment": "development"
}
```

MVP voice is client-platform (Android SpeechRecognizer/TextToSpeech, Web Speech API) — the backend never receives or stores audio. Server-side STT/TTS is deferred pending ADR-016 owner acceptance and an authenticated design.

---

## Crop Image Assistance (P5E)

**POST** `/api/v1/vision/analyze` — one-shot crop-photo analysis. Requires authentication. Multipart form: `file` (jpeg/png/webp by magic bytes, max 5 MiB — declared content-type headers are untrusted), optional `question` (≤500), `crop` (≤100), `language` (2-letter, default en).

Images are processed **in memory only** — never written to disk and never logged (nothing is retained). The response is structured observations + possible explanations with uncertainty + recommended next steps; the assistant never claims a definitive disease diagnosis and no detection accuracy is claimed or implied. Errors: `415 UNSUPPORTED_IMAGE_FORMAT`, `413 IMAGE_TOO_LARGE`, `503 VISION_MODEL_UNAVAILABLE`/`AI_UNAVAILABLE`, `504 VISION_TIMEOUT`, `502 VISION_FAILED`.

```json
{ "response": "Observed: … Possible: … (uncertain). Next: …", "model": "qwen3-vl:2b", "language": "en" }
```

---

## Research (P5D)

**GET** `/api/v1/research?q=rice%20blast&limit=8` — agricultural web search with verifiable citations. Requires authentication. `q` 2–200 chars, `limit` 1–20 (default 8).

Results are provider-observed (SearXNG), URLs verbatim and http/https-only, official agricultural domains (gov.in, ICAR, edu) ranked first. Every response carries a UTC `retrieved_at` freshness stamp. Provider unavailable → `503 RESEARCH_UNAVAILABLE`. The API never fabricates citations and never fetches user-supplied URLs server-side.

```json
{
  "query": "rice blast",
  "results": [
    { "rank": 1, "title": "…", "url": "https://icar.org.in/…", "snippet": "…",
      "source_domain": "icar.org.in", "official_source": true }
  ],
  "provider": "searxng",
  "retrieved_at": "2026-10-31T12:00:00Z"
}
```

---

## User Preferences (P5G)

**PATCH** `/api/v1/auth/preferences` — update the authenticated user's own preferences. Requires a valid session; there is no user-id parameter (own-only by construction).

```json
{ "preferred_language": "hi" }
```

`preferred_language` must be a 2-letter lowercase code (`^[a-z]{2}$`). Returns `200` with the full user response (same shape as `/me`); the change is persisted. Errors: `401` unauthenticated, `422` invalid language.

---

## Error Responses

All errors return a consistent flat envelope (ADR-009):

```json
{
  "detail": "Human-readable error description",
  "error_code": "MACHINE_READABLE_CODE",
  "request_id": "3f0c...",
  "errors": [{"field": "...", "message": "..."}]  // optional, validation only
}
```

**Request Correlation:** Every response includes `X-Request-ID` header matching the `request_id` in error responses.

| Status | Error Code | Description |
|--------|------------|-------------|
| 400 | REQUEST_BODY_TOO_LARGE | Request body exceeds `MAX_REQUEST_BODY_SIZE` |
| 401 | UNAUTHORIZED | Missing/invalid access token (login required) |
| 401 | TOKEN_EXPIRED | Access token expired; refresh via `/api/v1/auth/refresh` |
| 404 | CONVERSATION_NOT_FOUND | Conversation ID not found (or not owned by caller) |
| 404 | CATEGORY_NOT_FOUND | Resource category not found |
| 413 | REQUEST_BODY_TOO_LARGE | Request body too large |
| 422 | VALIDATION_ERROR | Request validation failed (Pydantic) |
| 429 | RATE_LIMIT_EXCEEDED | Rate limit exceeded; `Retry-After` header included |
| 503 | MODEL_NOT_FOUND | Ollama model not available |
| 503 | OLLAMA_CONNECTION_FAILED | Cannot reach Ollama service |
| 503 | AI_BUSY | AI gateway queue depth exceeded; retry after backoff |
| 503 | WEATHER_CONNECTION_FAILED | Cannot reach weather service |
| 504 | OLLAMA_TIMEOUT | Ollama request timed out |
| 504 | WEATHER_TIMEOUT | Weather request timed out |
| 500 | INTERNAL_ERROR | Unexpected server error |

Plain-string `HTTPException` details (legacy paths) map to `error_code: "HTTP_ERROR"`.

#### Example Error Response (404)

```json
{
  "detail": "Conversation 550e8400-e29b-41d4-a716-446655440000 not found",
  "error_code": "CONVERSATION_NOT_FOUND",
  "request_id": "3f0c8a1b-9e2f-4d1a-8b7c-6d5e4f3a2b1c",
  "errors": null
}
```

#### Example Validation Error (422)

```json
{
  "detail": "Request validation failed",
  "error_code": "VALIDATION_ERROR",
  "request_id": "3f0c8a1b-9e2f-4d1a-8b7c-6d5e4f3a2b1c",
  "errors": [
    {"field": "message", "message": "String should have at least 1 character"},
    {"field": "latitude", "message": "Input should be a valid number"}
  ]
}
```

---

## Rate Limiting

- **Default:** 60 requests per 60 seconds per client
- **Configuration:** `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS`
- **Trusted Proxies:** `TRUSTED_PROXY_CIDRS` (required in production)
- **Excluded:** Health endpoints (`/health*`, `/api/v1/health`)
- **Response on Limit:** HTTP 429 with `Retry-After` header (seconds)

---

## Request Limits

- **Max Request Body:** 1,048,576 bytes (1 MB) default
- **Configuration:** `MAX_REQUEST_BODY_SIZE`
- **Response on Exceed:** HTTP 413 with `Retry-After: 60`

---

## Conversation Management

Conversations are identified by UUID v4. The `conversation_id` is:
- Returned on first message (new conversation)
- Required for continuing existing conversations
- Not user-owned until Phase 3 auth; currently uses `legacy_import` user (UUID nil)

### Message Roles

| Role | Description |
|------|-------------|
| `user` | Farmer's message |
| `assistant` | AI response |
| `system` | Internal system prompt (not returned in history) |

### Context Window

- Last 10 messages loaded per conversation
- Messages ordered by `created_at` ascending for context
- User message persisted before Ollama call; assistant response after

---

## Model Information

- **Default Model:** `qwen3:0.6b` (522 MB, fits 2 GiB VRAM)
- **Configured via:** `OLLAMA_MODEL` environment variable
- **Available:** `qwen3:4b`, `qwen3-embedding:0.6b`, `nomic-embed-text:latest` (not yet integrated)

---

## OpenAPI Documentation

- **Swagger UI:** `/docs` (disabled in production)
- **ReDoc:** `/redoc` (disabled in production)
- **OpenAPI JSON:** `/openapi.json`
- **Artifact:** `docs/api/openapi.json` (committed, CI-validated)

---

## Versioning

- **API Version:** `/api/v1` prefix (all chat/weather/resources endpoints)
- **App Version:** `settings.app_version` (single source of truth)
- **Root endpoints** (`/`, `/health*`) unversioned for infrastructure compatibility

---

*API Reference reflects current implementation as of Phase 1 completion (2026-10-28, v0.1.0).*