# Target Backend Architecture

**Phase:** 0 — proposed design, not implemented  
**Date:** 2026-10-21  
**Status:** Proposed. Requires approval before any Phase 1 work.  
**Related:** [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md), [`GAP_ANALYSIS.md`](GAP_ANALYSIS.md), [`PHASE_01_IMPLEMENTATION_PLAN.md`](PHASE_01_IMPLEMENTATION_PLAN.md), [`../MyFarmAI_Backend_Roadmap.md`](../MyFarmAI_Backend_Roadmap.md)

---

## 1. Design goals

The target is a **secure, self-hostable, modular monolith** for a small agricultural assistant. It must run on the audited 7 GiB RAM / 2 GiB VRAM host, use no mandatory paid API, and remain understandable by one developer.

| Goal | Architectural consequence |
|---|---|
| No paid AI or search APIs | Ollama and SearXNG stay local; every external provider sits behind an adapter that can be replaced. |
| Multi-user safety | Authentication and ownership are enforced in the service layer for every farm/conversation/research object. |
| Reproducible operations | Pinned Python environment, locked dependencies, pinned images, versioned migrations, health checks, backups. |
| Constrained hardware | One backend process; PostgreSQL and Ollama as the only required extras; optional services deferred until measured. |
| Replaceable integrations | Weather, search, extraction, and public-data sources are adapters, not domain logic. |
| Testability | App factory, injected settings, hermetic tests, disposable PostgreSQL for integration tests. |
| Safe failure | Chat, weather, and research degrade independently; readiness reflects dependencies. |

**Explicit non-goals for the first production-capable version:** microservices, Kubernetes, multi-region deployment, event streaming, vector search, a separate search cluster, and a third-party identity provider.

## 2. System context

```text
 Web (Next.js)          Android (Expo)          Operators / CI
        \                    /                        |
         \                  /                         |
          +---- HTTPS 443 ---+                         |
                   |                                  |
                Caddy  (TLS, body limits, security headers)
                   |
          internal Docker network
                   |
             FastAPI backend
          /        |         |        \
     PostgreSQL   AI gateway  Weather   Research (Phase 6)
      (system      |          adapter      |
       of record)  |             |         +--> SearXNG (internal)
                   |             +--> Open-Meteo (external, non-commercial)
                   +--> Ollama (host loopback / private gateway)

 Optional, internal only: voice service (Phase 4 decision), background worker (Phase 7)
```

### 2.1 Trust zones

| Zone | Components | Allowed ingress | Controls |
|---|---|---|---|
| Public | Caddy on 80/443 | Internet/LAN as approved | TLS, HSTS, request/body limits, timeouts, rate limits, security headers |
| Application | FastAPI | Caddy only | Authentication, authorization, validation, structured errors, audit events |
| Data | PostgreSQL | Backend only | No published port, least-privilege DB role, encrypted backups, `/data` volume |
| Inference | Ollama | Backend only | Loopback/host gateway, no public bind, model allowlist, concurrency cap |
| Search | SearXNG | Research adapter only | Internal network, no published port, secret from environment, SSRF-safe fetcher |
| Voice (optional) | faster-whisper | Backend only | Auth at backend, size/type/duration limits, non-root, internal network |
| Egress | Backend | Allowlisted destinations | Weather host, search engines via SearXNG; everything else denied where the platform permits |

**Rule:** the backend must bind to `127.0.0.1` until authentication exists. No service may be published on `0.0.0.0` by default. This directly addresses security findings S-01, S-03, S-09 and S-12.

## 3. Layering and dependency rules

```text
app/
├── api/v1/              HTTP routers, dependencies, status mapping
├── core/                config, logging, errors, security primitives
├── modules/             domain/application logic
│   ├── auth/
│   ├── users/
│   ├── farms/
│   ├── crops/
│   ├── crop_cycles/
│   ├── chat/
│   ├── weather/
│   ├── resources/
│   ├── research/
│   ├── knowledge/
│   └── audit/
├── integrations/        ollama, weather, search, extraction, public_data
├── db/                  session, models, repositories
└── workers/             optional, Phase 7+
```

Dependency direction is one way:

```text
api -> modules -> integrations
 |        |
 +------> db <------ modules
```

Rules:

1. Routers contain no SQL and no provider-specific code.
2. Domain modules do not import FastAPI request/response types.
3. Integration adapters do not import domain modules; they expose typed, provider-neutral results.
4. Cross-module calls go through service interfaces, not another module’s ORM models.
5. Every state-changing operation is wrapped in a transaction and emits an audit event when security-relevant.
6. Configuration is injected; no module-level singleton reads the environment at import time.

This is a refactor of the existing `api -> services -> db` shape, not a rewrite. Existing route paths and response shapes are preserved unless an ADR says otherwise.

## 4. Module responsibilities

| Module | Responsibility | MVP phase | Notes |
|---|---|---|---|
| `core/config` | Typed settings, environment profiles, startup validation | 1 | Fail fast on unsafe production settings; no secrets in logs. |
| `core/errors` | Error envelope, exception handlers, stable codes | 1 | Replaces the current nested `detail` object. |
| `core/logging` | JSON logs, request ID, redaction | 1 | No message content or credentials. |
| `health` | `/health/live`, `/health/ready`, legacy `/health` | 1 | Readiness checks DB and Ollama; liveness does not. |
| `auth` | Registration/login/logout, sessions, tokens, password hashing | 3 | Required before any non-loopback exposure. |
| `users` | Profile, account status, deletion/export | 3 | Ownership root. |
| `farms` | Farm profile, coordinates, membership | 2 (model) / 5 (API) | Coordinates are personal data; minimise precision. |
| `crops`, `crop_cycles` | Crop catalogue and season tracking | 2 / 5 | Only build confirmed workflows. |
| `chat` | Conversation lifecycle, history, prompt assembly, orchestration | 4 | Existing behaviour retained; persistence and prompt logic separated. |
| `weather` | Coordinates, forecast normalization, cache, attribution | 5 | Provider-neutral adapter; Open-Meteo is one implementation. |
| `resources` | Static agricultural catalogue | 1 (keep) | Low risk; keep as-is until domain work. |
| `research` | Query planning, search, safe fetch, ranking, citations | 6 | SearXNG adapter plus hardened extractor. |
| `knowledge` | Stored sources, chunks, FTS, provenance | 6 | PostgreSQL FTS first. |
| `audit` | Append-only security events | 2/3 | Login, authorization denial, deletion, admin actions. |
| `workers` | Slow/background work | 7 (optional) | Only after latency measurements justify a queue. |

## 5. Core request flows

### 5.1 Chat

```text
Client -> Caddy -> POST /api/v1/chat
  -> authenticate principal
  -> validate message and context
  -> load or create conversation scoped to principal
  -> load recent messages ordered by (created_at, id)
  -> assemble system policy + delimited untrusted context
  -> AI gateway (timeout, semaphore, model allowlist)
  -> persist user message and assistant response in one transaction
  -> return response, conversation_id, model metadata, request_id
```

Requirements:

- A conversation ID is never sufficient authorization; ownership is checked in the query.
- `language`, `crop`, and `location` are stored on the conversation and reused when a follow-up omits them (fixes API-C-05).
- History order is deterministic: `(created_at, id)` (fixes API-C-06).
- The AI call has a bounded concurrency semaphore and explicit timeout; overload returns `429` or `503` with `Retry-After` (fixes S-08).
- Model name and prompt-template version are recorded for reproducibility.
- On model failure, the user message is preserved; the error is not stored as assistant prose. The API returns a stable error code.
- Streaming is out of scope until the UI and proxy support it; the current client timeout is 120 s.

### 5.2 Weather

```text
Client -> GET /api/v1/weather?latitude&longitude
  -> authenticate (by default)
  -> validate ranges and precision
  -> cache lookup (rounded coordinates + options, TTL)
  -> weather adapter -> Open-Meteo or approved replacement
  -> normalize, validate units/fields, attach attribution
  -> return; on timeout/upstream failure return 503/504 with a stable code
```

The adapter interface accepts coordinates and options and returns a normalized forecast. Open-Meteo field names never leak into domain code. Caching and attribution are required by the provider terms (INT-F02). The provider choice is an open legal/product decision (ADR-011).

### 5.3 Authentication

```text
Web:     POST /auth/login -> Argon2id verify -> opaque session ID
         Set-Cookie: HttpOnly; Secure; SameSite=Lax; Path=/
         Server stores only a hash of the session ID.

Android: POST /auth/login -> short-lived access token + rotating refresh token
         Both stored as hashes server-side; revocation is immediate.
```

Every request resolves a principal, then authorization runs in the service layer. Resource ownership is part of the SQL predicate, not a post-fetch check. See ADR-008.

### 5.4 Research (Phase 6, not MVP)

```text
Query -> SearXNG -> candidate URLs
  -> SSRF-safe fetcher (scheme/port allowlist, DNS revalidation, private-IP block,
     redirect revalidation, size/time/content-type limits)
  -> extraction (text only, active content stripped)
  -> provenance record (URL, title, publisher, retrieved_at, licence/terms)
  -> rank -> prompt with delimited evidence -> answer with citations
```

Fetched content is untrusted data. It can inform an answer but cannot change system policy, call tools, or authorize actions. PostgreSQL FTS is the first retrieval mechanism; a vector database is deferred until evaluation shows it is needed (ADR-007).

### 5.5 Voice (optional, decision required)

If retained: client calls an authenticated backend endpoint; the backend enforces size, MIME type, duration, and rate limits, then calls the internal voice service. The voice container is never published, runs non-root, and uses a pre-baked model with a read-only cache. If voice is not in the MVP, remove it from the default Compose profile and stop publishing port 8001 (ADR-014).

## 6. Persistence model

The system of record is PostgreSQL 17 (ADR-003). SQLite remains a test/local convenience only.

Core entities and ownership:

| Entity | Owner / scope | Key rules |
|---|---|---|
| `users` | self | Unique normalized login identifier; status; timestamps. |
| `farms` | user via membership | Coordinates optional; precision minimised; soft-delete policy decided in Phase 2. |
| `farm_members` | farm + user | Unique `(farm_id, user_id)`; roles `owner`/`member` for MVP. |
| `conversations` | user, optional farm | `user_id NOT NULL`; `farm_id` optional; indexed `(user_id, updated_at)`. |
| `messages` | conversation | `role CHECK IN ('user','assistant','system')`; cascade delete; index `(conversation_id, created_at, id)`. |
| `sessions` / `refresh_tokens` | user | Store token hashes only; expiry, revocation, rotation metadata. |
| `audit_events` | actor + subject | Append-only; no message content or secrets. |
| `research_queries`, `research_sources`, `citations` | user | Provenance and licence fields; added in Phase 6. |
| `knowledge_chunks` | source | PostgreSQL FTS index; added after evaluation. |

Rules:

- Use `TIMESTAMPTZ` in UTC; serialize ISO-8601 with offset.
- Use database-enforced foreign keys, `CHECK` constraints, and unique constraints. SQLite tests must enable `PRAGMA foreign_keys=ON`.
- Use opaque UUIDs generated by the database (`gen_random_uuid()`); ordering uses `created_at, id`.
- Every query for a user-owned object includes the owner predicate. Authorization tests cover cross-user and cross-farm access.
- No startup DDL. Alembic is the only schema authority.
- Deletion is explicit: user-initiated deletion cascades to owned data; retention rules and backups are documented (S-11, ADR-015).

The concrete migration from the two existing SQLite files is in ADR-004. **No migration is performed in Phase 0 or Phase 1.**

## 7. Failure modes and degradation

| Failure | Detection | Behaviour | Recovery |
|---|---|---|---|
| PostgreSQL unavailable | `/health/ready` fails; query errors | Mutating and read APIs return `503`; liveness stays `200`; no partial writes | Restore service; check disk/connections; alert. |
| Ollama unavailable | Readiness probe / connection error | Chat returns `503 AI_UNAVAILABLE`; weather/resources remain available | Restart Ollama; verify model; queue is bounded. |
| Ollama timeout / OOM | Timeout / 5xx | `504 AI_TIMEOUT` or `503 AI_OVERLOADED`; no retry storm | Reduce concurrency; smaller model/context; measure. |
| Open-Meteo timeout/limit | Adapter error / 429 | Serve fresh cache if available; otherwise `503 WEATHER_UNAVAILABLE` | Back off; respect quota; consider replacement. |
| SearXNG unavailable | Adapter error | Research returns `503 RESEARCH_UNAVAILABLE`; chat/weather unaffected | Restart search; check egress. |
| Voice unavailable | Adapter error | Transcription returns `503`; text chat unaffected | Restart; model cache is persistent. |
| Disk full | Write errors; disk alert | Writes fail closed; readiness degrades; logs rotate | Free space; restore from backup; investigate growth. |
| Caddy down | External probe | No ingress; internal services unaffected | Restart proxy; TLS certificate check. |
| Secrets rotated | Auth/search failures | Existing sessions may be revoked; document expected impact | Re-login; update secret store. |

The minimum viable degraded mode is: **chat unavailable, weather and resources still available**. This must be tested, not assumed.

## 8. Resource budget

Estimates are from [`HARDWARE_AND_DEPLOYMENT_ASSESSMENT.md`](HARDWARE_AND_DEPLOYMENT_ASSESSMENT.md); they must be replaced by measurements.

| Profile | Services | Estimated RAM | Feasibility on audited host |
|---|---|---:|---|
| Minimum | Caddy + backend + PostgreSQL | 0.5–1.0 GiB | Feasible if unrelated stacks are not consuming RAM. |
| AI | Minimum + Ollama with one small model | 3.5–5.5 GiB | Tight; 2.3 GiB was available at audit. Requires measurement and likely a smaller model. |
| Full | AI + SearXNG | 4–6 GiB | Only with a reduced model/context and no voice. |
| Full + voice | Full + faster-whisper small | 4.6–7.2 GiB | Not recommended on this host. |

Operational rules:

- One backend worker until measurement shows otherwise. Multiple Uvicorn workers multiply memory and break the in-process rate limiter.
- One concurrent chat by default; queue depth is bounded and observable.
- Store PostgreSQL data, backups, and logs on `/data`; keep images and code on `/` only if space allows.
- Docker’s data root is currently on `/` with 5.3 GB free — a build blocker (HW-02). Relocate or prune only with explicit approval.
- Do not run SearXNG, voice, Valkey, Qdrant, and multiple models concurrently on this host.

## 9. Deployment topology

### 9.1 Development

- Backend on `127.0.0.1:8000`, SQLite isolated per test, Ollama on host.
- No Caddy required; no public bind.
- Android emulator uses `10.0.2.2` only after the client base-URL fix (API-C-04).
- Voice disabled by default.

### 9.2 Single-host production (recommended first target)

```text
Caddy :443
  -> backend (internal network, non-root, no published port)
       -> postgres (internal, volume on /data)
       -> ollama (host loopback or private gateway)
       -> searxng (internal, Phase 6)
       -> voice (internal, only if approved)
```

- Caddy terminates TLS and enforces body/header/timeouts and coarse rate limits.
- Backend enforces authentication, authorization, validation, and per-route quotas.
- PostgreSQL and SearXNG have no published ports.
- Images are pinned by digest; health checks gate startup; restart policies are explicit.
- Secrets come from the host environment or Docker secrets, not the repository.
- Backups run outside the request path and are stored off the database volume.

### 9.3 Future scale (not now)

Horizontal scaling requires shared sessions, a shared rate-limit store (Valkey), a background worker, and object storage. None is justified by current evidence. Revisit only after measurements show a single process cannot meet demand.

## 10. Cross-cutting conventions

| Area | Convention |
|---|---|
| API prefix | `/api/v1`; health endpoints unversioned or under `/health/*`. |
| Content type | JSON; UTF-8; ISO-8601 UTC timestamps. |
| IDs | Opaque UUID strings; never expose sequential database IDs. |
| Errors | Flat envelope with `detail`, `error_code`, `request_id`, optional `errors[]` (ADR-009). |
| Auth | Cookie session for web; bearer access/refresh for mobile; no API keys in URLs. |
| Rate limits | Per principal and per route; trusted-proxy-aware; bounded storage. |
| Logging | JSON, request ID, latency, status, route; no prompts, message bodies, tokens, or raw IP retention beyond operational need. |
| Audit | Security-relevant events only; append-only; privacy-aware retention. |
| OpenAPI | Generated artifact reviewed in CI; no hand-maintained duplicate. |
| Configuration | `.env.example` placeholders only; production fails fast on unsafe defaults. |
| Migrations | Alembic only; forward-fix preferred; backups before migration. |
| Tests | Hermetic unit tests; disposable PostgreSQL integration tests; contract and security regressions. |

## 11. Alternatives considered

| Alternative | Why rejected for the first production version |
|---|---|
| Microservices | Operational overhead, multiple runtimes, more RAM, no measured need. |
| Serverless backend | Local Ollama, long requests, persistent DB connections, self-hosting requirement, cost/egress uncertainty. |
| Hosted LLM API | Violates the no-paid-AI requirement and sends user data off-host. |
| SQLite as production DB | Weak multi-user concurrency, no roles/RLS, manual migrations, backup discipline required. Kept for tests. |
| Separate search cluster / Qdrant now | Extra RAM/disk with no retrieval benchmark; PostgreSQL FTS first. |
| Keycloak/OIDC now | Heavy for a 7 GiB host; no enterprise SSO requirement yet. |
| GraphQL | No client need; adds authorization and caching complexity. |
| Message queue now | No measured long-running workload; request/response is sufficient for MVP. |
| Host networking for the backend | Removes isolation and exposes ports; replaced by an internal Docker network and Caddy. |

## 12. Architecture conformance checklist

A change conforms to this architecture only if:

- [ ] It keeps one deployable backend unless an approved ADR justifies a split.
- [ ] It adds no mandatory paid API, hosted AI, or proprietary service.
- [ ] It routes all external data through an adapter with timeout, validation, and failure mapping.
- [ ] It enforces authentication and ownership for private data.
- [ ] It adds a migration for every schema change and a test for every new behaviour.
- [ ] It documents new configuration, failure modes, and resource impact.
- [ ] It keeps optional services out of the minimum profile.
- [ ] It passes the Phase 1 quality gate and the relevant security tests.

## 13. Open decisions

These block finalisation, not the audit:

1. Deployment target: local-only, private LAN, single VPS, or public internet.
2. Canonical SQLite database and whether existing conversations must be preserved.
3. Weather provider for commercial use (Open-Meteo is non-commercial only).
4. Python/runtime standardisation (recommended: 3.12 + `uv`).
5. Voice: defer from MVP or secure and keep.
6. Model: benchmark `qwen3:4b` or select a smaller model.
7. Project licence and AGPL-3.0 obligations for SearXNG.
8. Backup RPO/RTO and retention periods.

See [`README.md`](README.md) §6 and [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md) for the decision records.

---

**Status:** Proposed architecture. No code, configuration, database, dependency, or deployment change was made in Phase 0.
