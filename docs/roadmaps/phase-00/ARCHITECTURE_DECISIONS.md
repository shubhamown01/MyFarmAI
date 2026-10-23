# Architecture Decision Records

**Phase:** 0 — proposed decisions  
**Date:** 2026-10-21  
**Status:** All records are **Proposed** unless stated otherwise. None is implemented or approved.  
**Related:** [`TARGET_BACKEND_ARCHITECTURE.md`](TARGET_BACKEND_ARCHITECTURE.md), [`GAP_ANALYSIS.md`](GAP_ANALYSIS.md), [`PHASE_01_IMPLEMENTATION_PLAN.md`](PHASE_01_IMPLEMENTATION_PLAN.md)

---

## 1. How to read these records

Each record follows the same structure: context, decision, consequences, alternatives, and verification. “Proposed” means the audit recommends it but the project owner has not approved it. A decision is not binding until it is accepted and the Phase 1 scope is approved.

| ID | Decision | Status | Needed by |
|---|---|---|---|
| ADR-001 | Modular monolith on FastAPI | Proposed | Phase 1 |
| ADR-002 | Python 3.12 + `uv` lockfile | Proposed | Phase 1 |
| ADR-003 | PostgreSQL 17 as system of record; SQLite tests only | Proposed | Phase 2 |
| ADR-004 | SQLite-to-PostgreSQL migration and canonical-data choice | Proposed | Phase 2 |
| ADR-005 | SQLAlchemy 2 + Alembic + asyncpg | Proposed | Phase 2 |
| ADR-006 | Provider-independent AI gateway over Ollama | Proposed | Phase 4 |
| ADR-007 | SearXNG + PostgreSQL FTS; Qdrant deferred | Proposed | Phase 6 |
| ADR-008 | Opaque sessions/tokens, Argon2id, service-layer authorization | Proposed | Phase 3 |
| ADR-009 | Flat error envelope and request correlation | Proposed | Phase 1 |
| ADR-010 | Single-host Compose + Caddy, internal networks | Proposed | Phase 1/8 |
| ADR-011 | Weather adapter; Open-Meteo non-commercial only | Proposed | Phase 5 |
| ADR-012 | Defer Valkey, workers, Qdrant, extra observability | Proposed | Phase 7 |
| ADR-013 | Hermetic tests, disposable PostgreSQL, CI gates | Proposed | Phase 1 |
| ADR-014 | Voice deferred from the MVP | Proposed | Phase 1 |
| ADR-015 | Backup, retention, and deletion policy | Proposed | Phase 1/2 |

---

## ADR-001 — Use a modular monolith on FastAPI

**Status:** Proposed  
**Context:** The current backend is already a single FastAPI process with routers, services, and raw SQL. The host has 7 GiB RAM and limited disk. The roadmap explicitly prefers a modular monolith and forbids unmeasured service splits.

**Decision:** Keep one deployable FastAPI backend. Organize it into domain modules with one-way dependencies (`api -> modules -> integrations/db`). Split a service only when a measured isolation, scaling, or security requirement cannot be met inside the monolith, and only through a new ADR.

**Consequences:**

- Positive: one runtime, one deployment, simple local development, low memory, shared transactions, easy refactoring.
- Negative: a single process is a single failure domain; module boundaries must be enforced by review and import rules.
- Neutral: the process can run multiple workers later, but shared state (rate limits, sessions) must move out first.

**Alternatives:** Microservices (rejected: operational and RAM cost); serverless (rejected: local AI, long requests, persistent DB); separate AI service (deferred until isolation is measured).

**Verification:** No cross-module imports of ORM models; routers contain no SQL; one Compose service for the backend; module ownership documented.

---

## ADR-002 — Standardise on Python 3.12 with `uv` and a committed lockfile

**Status:** Proposed  
**Context:** The local virtualenv is Python 3.14.4, while the container and `mypy.ini` target 3.12. Dependencies are unpinned; `requirements.txt` contains duplicates and test tooling that ships to production. This is a reproducibility and supply-chain risk (DEP-01, DEP-02, DEP-03).

**Decision:** Target **Python 3.12** for development, CI, and runtime. Use `pyproject.toml` with runtime and development dependency groups and a committed `uv.lock`. Use `uv sync --frozen` in CI and `uv sync --frozen --no-dev` in the runtime image. Keep `requirements.txt` only as a temporary compatibility shim, then remove it.

**Consequences:**

- Positive: one interpreter version; reproducible installs; smaller runtime image; faster installs.
- Negative: the existing 3.14 virtualenv must be recreated; contributors need `uv`; lockfile updates become reviewable changes.
- Risk: a 3.12-only pin may lag newer library features, which is acceptable for stability.

**Alternatives:** Keep unpinned `pip` (rejected); pin 3.14 (rejected: container/mypy mismatch and broader ecosystem risk); Poetry (viable, but `uv` is faster and already aligned with the roadmap).

**Verification:** `uv lock --check`, `uv sync --frozen` on a clean checkout, `python --version` = 3.12.x in CI and image, no duplicate dependencies.

---

## ADR-003 — PostgreSQL 17 is the system of record; SQLite is test-only

**Status:** Proposed  
**Context:** SQLite currently stores conversations and messages with no ownership columns, no enforced foreign keys, no migration history, and no backup procedure. Two divergent files exist (122/315 and 35/74 rows). Production needs multi-user concurrency, ownership, constraints, migrations, and reliable recovery.

**Decision:** Use **PostgreSQL 17** (pin the exact minor/digest at implementation) as the production database. Use SQLite only for unit tests and isolated local development. Do not run SQLite in production after the migration is accepted.

**Consequences:**

- Positive: real constraints, transactions, `TIMESTAMPTZ`, full-text search, mature backup/restore, path to row-level security.
- Negative: an extra service to operate and back up; more RAM (≈100–600 MB); migration work; developers need Docker or a local Postgres.
- Neutral: SQLite remains useful for fast tests, but tests must run the same logical schema and enable foreign keys.

**Alternatives:** SQLite in production (rejected: concurrency, ownership, migrations, backup discipline); MySQL/MariaDB (viable but no advantage here); hosted Postgres (rejected as a mandatory paid service).

**Verification:** Alembic migration from empty; foreign keys and checks enforced; concurrent write test; backup/restore drill; no SQLite path in the production configuration.

---

## ADR-004 — Migrate existing SQLite data explicitly; do not merge blindly

**Status:** Proposed  
**Context:** Two SQLite files exist:

| File | Conversations | Messages | Used by | Git status |
|---|---:|---:|---|---|
| `backend/data/app.db` | 122 | 315 | Local runs from `backend/` | Untracked, **not ignored** |
| `data/app.db` | 35 | 74 | Compose bind mount | Untracked, ignored by `data/*` |

Neither is declared canonical. Both pass `PRAGMA integrity_check`. The data may contain real user conversations, crop/location context, and personal data. The schema has no owner, so migrated rows need an ownership decision.

**Decision:**

1. The project owner chooses the canonical source before any migration. The audit does **not** assume that the larger file is authoritative.
2. Back up both files before any change: SQLite online backup or `VACUUM INTO`, SHA-256 checksum, integrity check on the copy, stored outside the repository.
3. If only one file contains real data, migrate that file. If both contain unique real data, import both with a `legacy_source` tag and deduplicate by conversation ID; never overwrite by row count.
4. Assign migrated conversations to an explicitly approved legacy user/farm (for example `legacy_import`) or to a mapped owner. Do not leave `user_id` null after cutover.
5. Export, transform, load, and validate in a maintenance window. Preserve conversation IDs; convert timestamps to UTC `TIMESTAMPTZ`; validate roles and lengths; reset identity sequences.
6. Validate row counts, per-conversation message counts, min/max timestamps, foreign keys, and a small owner-approved sample.
7. Keep the source SQLite files read-only until acceptance. Rollback is restoring the pre-migration files; writes after cutover would be lost, so prefer forward-fix once new writes begin.

**Consequences:**

- Positive: explicit ownership, auditable migration, no silent data loss, reversible cutover.
- Negative: requires a maintenance window and owner decisions; legacy rows may need manual mapping.
- Risk: if both files contain overlapping but edited conversations, deduplication needs a documented rule.

**Alternatives:** Start empty (acceptable only if the owner confirms no data must be preserved); dual-write (rejected: complexity and split-brain); SQLite-to-Postgres automated tool without review (rejected: ownership and data-loss risk).

**Verification:** Acceptance checklist in [`DATABASE_ASSESSMENT.md`](DATABASE_ASSESSMENT.md) §8.8; backup checksum and integrity check; row/per-conversation counts match; chat create/continue works; restore drill succeeds.

---

## ADR-005 — SQLAlchemy 2 + Alembic + asyncpg

**Status:** Proposed  
**Context:** Current data access is raw SQL through `aiosqlite`, with startup `CREATE TABLE IF NOT EXISTS`. The application is async. PostgreSQL needs typed models, migrations, and a driver compatible with the async stack.

**Decision:** Use SQLAlchemy 2.x typed ORM models, Alembic migrations, and **asyncpg** through SQLAlchemy’s async engine. Use an async Alembic environment so migrations and runtime share one driver. Keep repositories thin; transactions belong to the service layer. Configure a small connection pool (`pool_size`/`max_overflow` tuned for 7 GiB), `pool_pre_ping`, and statement timeouts.

**Consequences:**

- Positive: parameterized queries, schema metadata, migration history, async performance, one driver.
- Negative: ORM learning/maintenance cost; async migrations are less familiar; SQLAlchemy adds a dependency.
- Neutral: raw SQL remains allowed for reporting, but must use bound parameters and be reviewed.

**Alternatives:** psycopg 3 (viable; LGPL-3.0; sync/async mix); raw asyncpg (no migration/metadata layer); Django ORM (would replace FastAPI patterns).

**Verification:** `alembic upgrade head` on empty Postgres; downgrade/forward-fix tested; no startup DDL; SQL injection regression tests; pool exhaustion behaviour tested.

---

## ADR-006 — Provider-independent AI gateway over Ollama

**Status:** Proposed  
**Context:** `services/chat.py` calls a concrete `OllamaClient` directly. Prompt construction, history, persistence, and provider errors are coupled. There is no model allowlist, prompt versioning, evaluation, or concurrency control. `qwen3:4b` does not fit in 2 GiB VRAM and has not been benchmarked.

**Decision:** Introduce an internal `AIProvider` interface with a `chat` capability (and later `embed`) returning a typed result: text, model identifier/digest, token usage if available, finish reason, and latency. Implement an Ollama adapter first. Centralize prompt templates with version identifiers, model allowlist, timeouts, retry policy, and a bounded concurrency semaphore. Record model name/digest and template version per message. Do not expose provider-specific errors to clients.

**Consequences:**

- Positive: replaceable provider, testable domain logic, consistent failure handling, reproducibility.
- Negative: one more abstraction; must avoid leaking provider options into the interface.
- Risk: model quality/latency on this host remains unknown until benchmarked.

**Model gate:** Before Phase 4, benchmark `qwen3:4b` and at least one smaller candidate on representative agriculture prompts at the intended context size. Measure first-token latency, total latency, peak RAM/VRAM, and failure under 1/2/4 concurrent requests. If targets fail, select a smaller model or reduce context; do not silently ship an unusable default.

**Alternatives:** Direct Ollama calls (current; rejected for coupling); hosted LLM (violates requirement); llama.cpp/vLLM (possible adapters; vLLM is too heavy for this host); multiple providers now (premature).

**Verification:** Gateway contract tests; provider error mapping; prompt-injection regression tests; benchmark report; no paid API key required.

---

## ADR-007 — SearXNG plus PostgreSQL full-text search; defer Qdrant

**Status:** Proposed  
**Context:** SearXNG is running locally but unused. The research phase needs search, safe page fetching, provenance, and citations. The host cannot comfortably run an additional vector database alongside Postgres, Ollama, and SearXNG.

**Decision:** Use self-hosted **SearXNG** behind a search adapter for discovery, and **PostgreSQL full-text search** for stored sources/chunks. Add Qdrant only if an evaluation shows PostgreSQL FTS is insufficient. Run SearXNG unmodified on an internal network, pin its image digest, load the server secret from the environment, and review per-engine terms/robots policies. Implement a separate SSRF-safe fetcher; never fetch arbitrary URLs from a request without controls.

**Consequences:**

- Positive: no paid search API; one fewer datastore; provenance can live in Postgres; AGPL obligations are manageable if SearXNG remains unmodified.
- Negative: FTS quality for Hindi/regional languages is uncertain; SearXNG upstream engines may rate-limit or block; page extraction is a new attack surface.
- Risk: AGPL-3.0 network-use obligations if SearXNG is modified. Legal review required.

**Alternatives:** Hosted search API (rejected: paid/key); Elasticsearch/OpenSearch (too heavy); Qdrant now (deferred); direct scraping (rejected: terms, robustness, SSRF).

**Verification:** Search adapter contract tests; SSRF test suite (loopback, private, link-local, redirects, DNS rebinding); citation/provenance tests; retrieval evaluation before considering Qdrant.

---

## ADR-008 — Opaque sessions and tokens, Argon2id, service-layer authorization

**Status:** Proposed  
**Context:** No authentication or ownership exists. Conversation IDs act as bearer secrets. The web client is browser-based; Android is a native app. A public deployment requires revocable sessions and immediate logout.

**Decision:**

- **Passwords:** Argon2id via a maintained library, parameters tuned to ≈100–300 ms on the target host; rehash on parameter change.
- **Web:** opaque random session ID in an `HttpOnly`, `Secure`, `SameSite=Lax` cookie; store only a hash server-side; rotate on login; idle and absolute expiry; CSRF token or strict Origin check for state-changing requests.
- **Android:** short-lived opaque access token plus rotating refresh token; store hashes server-side; revoke on logout, password change, or suspicion.
- **Authorization:** resolve a principal on every request; enforce ownership in the SQL predicate/service layer, not in the UI. Cross-user object access returns `404` to avoid existence disclosure.
- **Roles:** MVP farm roles `owner`/`member`; no global admin UI until required.
- **Registration/reset:** deployment-dependent. For a private deployment, admin-created accounts are acceptable. For public registration, add abuse controls and a reset mechanism that does not require a paid email provider (admin-assisted reset or recovery codes); document the choice.

**Consequences:**

- Positive: immediate revocation, no JWT key management, simple mental model, works for web and mobile.
- Negative: session table growth and cleanup; cookie/CSRF configuration must be correct; mobile token rotation adds client work.
- Risk: building auth in-house is security-sensitive; require review and tests, or adopt a maintained library for primitives.

**Alternatives:** JWT access tokens (rejected for MVP: revocation complexity); Auth0/Keycloak (paid or heavy); API keys only (insufficient for user accounts).

**Verification:** Auth matrix tests (anonymous, expired, revoked, cross-user, cross-farm); CSRF test; password-hash timing; session cleanup; no credentials in logs.

---

## ADR-009 — One flat error envelope with request correlation

**Status:** Proposed  
**Context:** Handlers currently raise `HTTPException(detail={...})`, producing `{"detail":{"detail":...,"error_code":...}}`, while schemas/docs describe a flat object. Web handles both; Android displays `[object Object]`. Request IDs are generated for logs but not standardized in responses.

**Decision:** Return one flat JSON envelope for all application errors:

```json
{
  "detail": "Conversation not found.",
  "error_code": "CONVERSATION_NOT_FOUND",
  "request_id": "3f0c...",
  "errors": [{"field": "message", "message": "Must not be blank."}]
}
```

`errors` is optional and used for validation. HTTP status conveys the class; `error_code` is stable and documented. Map validation errors (422) into the same envelope. Return `X-Request-ID` on every response; accept an inbound ID only if it is 8–128 safe characters, otherwise generate one. Never return stack traces, upstream response bodies, SQL, or secrets.

| Status | Use |
|---|---|
| 400 | Malformed request that is not a schema validation error |
| 401 | Missing/invalid authentication |
| 403 | Authenticated but not allowed (only when existence is not sensitive) |
| 404 | Missing object or unauthorized object access |
| 409 | Conflict (duplicate, state transition) |
| 422 | Request schema validation |
| 429 | Rate limit/concurrency limit; include `Retry-After` |
| 503 | Dependency unavailable/overloaded |
| 504 | Upstream timeout |

**Consequences:**

- Positive: one client parser; stable codes; easier support; request correlation.
- Negative: a breaking change for any consumer that expects the nested shape; web and Android must be updated together.
- Neutral: FastAPI’s default validation handler must be overridden.

**Alternatives:** Keep the nested shape (rejected: documented contract is already flat); RFC 7807 problem+json (viable; more verbose and no client benefit here).

**Verification:** Contract tests for every code/status; web and Android parse the same shape; request ID present and unique; no stack traces in responses.

---

## ADR-010 — Single-host Docker Compose with Caddy and internal networks

**Status:** Proposed  
**Context:** Current Compose uses `network_mode: host`, publishes voice on `0.0.0.0:8001`, runs as root, has no health checks or limits, and uses floating images. The backend is not running. The host’s `/` has 5.3 GB free and Docker data is on `/`.

**Decision:** Deploy the first production-capable version as a single-host Compose stack:

- **Caddy** is the only public service (80/443), terminating TLS and enforcing body/header/timeouts and coarse rate limits.
- **Backend** runs non-root on an internal network with no published port. It reaches PostgreSQL, Ollama, SearXNG, and voice through private addresses.
- **PostgreSQL** has no published port; data and backups live on `/data`.
- **Ollama** stays a host process bound to loopback, reached through a controlled host gateway; do not expose `11434`.
- **SearXNG** and **voice** are internal only; neither is published.
- Pin image digests; add health checks, `restart: unless-stopped`, `cap_drop: [ALL]`, `no-new-privileges`, read-only root filesystems where practical, and resource limits after measurement.
- Keep secrets out of the repository; use environment files with restrictive permissions or Docker secrets.

**Consequences:**

- Positive: isolation, TLS, reproducible deployment, no accidental LAN exposure.
- Negative: more configuration than host networking; Ollama host-gateway networking needs care; Caddy becomes a critical service.
- Risk: building images may fail until `/` space is freed or Docker’s root moves to `/data` (HW-02). That relocation requires a daemon restart and explicit approval.

**Alternatives:** Host networking (rejected: exposure); Kubernetes (too heavy); a cloud load balancer (unnecessary/paid); Nginx (viable; Caddy has simpler TLS automation).

**Verification:** `docker compose config`; only 80/443 published; backend/DB/search/voice not reachable from LAN; containers non-root; health checks pass; TLS certificate valid; secrets absent from images and Git.

---

## ADR-011 — Weather adapter with Open-Meteo restricted to non-commercial use

**Status:** Proposed  
**Context:** The weather feature calls Open-Meteo directly on every request with no cache or attribution. The free tier is **non-commercial only**; commercial use requires a paid subscription. This conflicts with the zero-paid requirement if MyFarmAI is commercialised.

**Decision:** Keep a provider-neutral weather adapter. Open-Meteo may be used for **non-commercial prototyping only**, with attribution and caching. Before any commercial launch, choose one of:

1. A commercial Open-Meteo licence (introduces a paid dependency; requires explicit exception).
2. Self-hosted Open-Meteo with independently licensed data (AGPL software; data licences vary).
3. A different provider whose terms permit the intended use (review licence, limits, attribution, and cost).

Do not hard-code Open-Meteo field names in domain code. Cache responses for the configured TTL, respect rate limits, validate upstream fields, and return attribution metadata to clients. Do not store coordinates longer than the feature requires.

**Consequences:**

- Positive: replaceable provider; legal risk made explicit; fewer upstream calls.
- Negative: provider replacement work; some alternatives may still cost money or have restrictive terms.
- Risk: self-hosting weather data may be operationally heavy and still licence-constrained.

**Alternatives:** Keep Open-Meteo and accept non-commercial status (acceptable for a prototype, not a commercial launch); remove weather from the MVP (possible but reduces usefulness); scrape a website (rejected: terms/robustness).

**Verification:** Attribution visible in API/UI; cache hit behaviour; provider terms recorded; a documented decision before commercial release; adapter contract tests.

---

## ADR-012 — Defer Valkey, background workers, Qdrant, and extra observability

**Status:** Proposed  
**Context:** The host is memory- and disk-constrained. There is no measured need for a queue, vector database, or distributed cache. Premature services increase operational burden and failure modes.

**Decision:** Do not add Valkey, a worker framework, Qdrant, or a full observability stack in Phases 1–6. Use PostgreSQL and in-process concurrency controls first. Revisit only when one of these is measured:

- Request latency repeatedly exceeds the product target because of slow work that can be deferred.
- Multi-page research or document extraction cannot complete within an HTTP request.
- PostgreSQL FTS fails a defined retrieval evaluation.
- A second backend worker is required, making in-process rate limits/sessions unsafe.

When justified, add one service at a time with a resource budget, health check, backup/recovery plan, and an ADR.

**Consequences:**

- Positive: lower RAM/disk use, fewer moving parts, faster delivery.
- Negative: some work remains synchronous and may time out; scaling is limited.
- Neutral: interfaces should allow a future queue without rewriting domain logic.

**Alternatives:** Add everything now (rejected: resource and complexity cost); never add (rejected: may block future research).

**Verification:** A documented measurement triggers any addition; optional services are absent from the minimum Compose profile.

---

## ADR-013 — Hermetic tests, disposable PostgreSQL, and CI quality gates

**Status:** Proposed  
**Context:** The suite reports 49 passed / 7 failed on a clean database because chat tests use the application’s global settings and do not initialize their own schema. There is no CI, no OpenAPI artifact, and test tooling ships in the runtime image.

**Decision:**

- Introduce an app factory (`create_app(settings)`) and dependency injection; no import-time global settings in tests.
- Unit tests use a per-test temporary SQLite database and run the same logical schema through Alembic (or a documented metadata path with a migration-parity test). Enable `PRAGMA foreign_keys=ON`.
- Integration tests use a disposable PostgreSQL instance (Compose service in CI) and run `alembic upgrade head`.
- Contract tests assert the error envelope, OpenAPI snapshot, auth matrix, and health semantics.
- Security regression tests cover cross-user access, rate limits, body limits, and (later) SSRF/prompt injection.
- `scripts/check.sh` is the single local/CI entrypoint: format check, lint, type check, tests, OpenAPI diff, Compose validation, secret scan, dependency audit.
- CI platform is chosen when a remote is configured; the script must work locally first.

**Consequences:**

- Positive: trustworthy test signal, no dev-data writes, reproducible CI, reviewable API changes.
- Negative: slower integration tests; Docker/Postgres required for the full suite.
- Risk: SQLite/PostgreSQL schema drift; mitigated by a migration-parity test.

**Alternatives:** Keep the current suite (rejected: false green); test only against SQLite (insufficient for Postgres features); no CI (rejected: supply-chain and regression risk).

**Verification:** Clean checkout + `scripts/check.sh` passes; tests never touch `backend/data/app.db`; CI runs the same script; OpenAPI diff fails on unintended changes.

---

## ADR-014 — Defer the voice service from the MVP

**Status:** Proposed  
**Context:** The voice container is running as root, published on `0.0.0.0:8001`, unauthenticated, with no size/type/duration/rate limits. It has no consumers in the backend or clients, forces Hindi, downloads its model at runtime, and costs 0.6–1.2 GB RAM when loaded.

**Decision:** Remove voice from the default MVP profile. Do not publish port 8001. Keep the code in the repository for a later phase, or delete it if the product does not need it. If voice is reintroduced:

- Expose transcription only through an authenticated backend endpoint.
- Enforce max upload size, allowed MIME types, duration, and per-user rate limits.
- Run non-root, read-only root filesystem, internal network, bounded temp storage.
- Pre-bake/pin the model and mount a persistent cache.
- Add a queue/concurrency cap and timeout.
- Decide language handling explicitly (auto-detect vs selected language).

**Consequences:**

- Positive: removes an unauthenticated high-cost endpoint; lowers RAM; reduces attack surface.
- Negative: no voice feature until reintroduced.
- Neutral: the code and model remain available for a later product decision.

**Alternatives:** Secure it now (more Phase 1 work, no current consumer); leave it exposed (rejected: S-03).

**Verification:** Port 8001 not published; default Compose has no voice service; any future voice endpoint requires auth and limits.

---

## ADR-015 — Backup, retention, and deletion policy

**Status:** Proposed  
**Context:** No backup or restore procedure exists. Conversations, crop/location context, and AI responses are stored indefinitely. Two divergent SQLite files increase recovery risk. Privacy obligations are unknown but plausible.

**Decision (proposed defaults, owner/legal confirmation required):**

| Data class | Retention | Backup |
|---|---|---|
| Conversations/messages | Until user deletes; no indefinite orphan data | Included in DB backups |
| Account/session data | Account lifetime; sessions expire | Included; tokens not recoverable (hashes) |
| Audit events | 90 days (proposal) | Included; restricted access |
| Application logs | 14 days (proposal) | Not backed up; rotated |
| Research sources | Per licence/terms and product need; review in Phase 6 | Metadata only unless permitted |
| Backups | 30 days (proposal), encrypted, off-host copy | Restore tested quarterly |

- **Phase 1 (SQLite):** online backup/`VACUUM INTO`, SHA-256, integrity check, restore drill to a disposable path. No cron until approved.
- **Phase 2 (PostgreSQL):** daily `pg_dump -Fc`; WAL archiving only if the approved RPO is below 24 hours. Encrypt at rest; store outside the DB volume; restrict access.
- **Deletion:** user-initiated deletion cascades to owned rows; backups age out on the documented schedule; export is available before deletion.
- **RPO/RTO:** proposal RPO 24 h, RTO 4 h for a single host; owner must confirm.

**Consequences:**

- Positive: recoverability, privacy alignment, clear deletion behaviour.
- Negative: storage and operational cost; retention limits may conflict with product/legal requirements.
- Risk: backups can retain deleted data until expiry; document this in the privacy notice.

**Alternatives:** No backups (rejected: S-06); infinite retention (rejected: privacy and cost); cloud backup only (may violate self-hosting/cost constraints; optional off-host copy is acceptable).

**Verification:** Restore drill evidence; checksums; row-count validation; deletion cascade test; backup access restricted; retention documented.

---

## 2. Decision log and approval

| ID | Recommended decision | Approval needed from | Blocking |
|---|---|---|---|
| ADR-001 | Modular monolith | Project owner / engineering | Phase 1 |
| ADR-002 | Python 3.12 + uv | Engineering | Phase 1 |
| ADR-003 | PostgreSQL 17 production | Owner / operations | Phase 2 |
| ADR-004 | Canonical DB + migration | Data owner | Phase 2 |
| ADR-005 | SQLAlchemy/Alembic/asyncpg | Engineering | Phase 2 |
| ADR-006 | AI gateway + model benchmark | Product/engineering | Phase 4 |
| ADR-007 | SearXNG + PG FTS | Engineering/legal | Phase 6 |
| ADR-008 | Sessions/tokens + Argon2id | Security/engineering | Phase 3 |
| ADR-009 | Flat error envelope | Client/backend owners | Phase 1 |
| ADR-010 | Compose + Caddy | Operations | Phase 1/8 |
| ADR-011 | Weather provider | Product/legal | Phase 5 / commercial launch |
| ADR-012 | Defer optional services | Engineering | Phase 7 |
| ADR-013 | Test/CI strategy | Engineering | Phase 1 |
| ADR-014 | Defer voice | Product | Phase 1 |
| ADR-015 | Backup/retention | Owner/legal | Phase 1/2 |

**Approval rule:** Phase 1 may start only after ADR-001, ADR-002, ADR-009, ADR-010, ADR-013, ADR-014, and the Phase 1 scope are approved. ADR-003/004/005 may be approved later but must be settled before Phase 2 starts. ADR-008 must be approved before any non-loopback deployment.

No decision in this document has been implemented.
