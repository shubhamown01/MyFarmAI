# Changelog

All notable changes to MyFarmAI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Phase 3 authentication foundation (P3-01..P3-08): Argon2id password hashing (`app/core/security.py`, m=131072 t=3 p=4, ~114 ms verify); opaque session IDs / refresh tokens stored as SHA-256 hashes only; `AuthService` (login with audit, session validate with expiry+revocation+idle-timeout, logout, single-use refresh rotation with reuse detection that revokes the chain and all user sessions); `POST /auth/login` (web: HttpOnly/SameSite=Lax cookie; Android: bearer access + refresh tokens), `POST /auth/logout`, `GET /auth/me`, `POST /auth/token/refresh`, `POST /auth/admin/users` (admin-only account creation, no public registration per ADR-008 MVP policy)
- Ownership predicates (P3-05): all `ConversationRepository` single-record methods require `user_id` and filter in SQL (deny-by-default, cross-user = 404)
- Chat auth-gating (P3-09): `POST /api/v1/chat` requires authentication (401 otherwise); conversations attributed to the authenticated user instead of the legacy UUID; `get_current_user_id` principal dependency (cookie + bearer paths)
- Resource bounds (P3-12): rate-limit counters are bounded against memory exhaustion (stale-bucket eviction over 10k tracked IPs); new `ai_max_concurrent_requests` setting (default 2) caps in-flight AI requests via semaphore in the async chat path
- Security middleware (P3-10/P3-11): trusted-proxy-aware client IP (`app/core/client_ip.py` — spoofed `X-Forwarded-For` no longer bypasses rate limits); CSRF/Origin enforcement for cookie-authenticated state changes (mismatched Origin/Referer → 403); stricter per-IP limit on auth endpoints (10 req/min); per-account failed-login lockout (5 failures / 15 min → 429)
- Auth tests: 9 security-primitive + 17 service + 16 API + 6 ownership-predicate + 6 middleware + 2 auth-matrix/async-regression integration tests
- Phase 7A COMPLETE (FCL-079): independent QA verdict CONFIRMED WITH EXCEPTIONS — all 20 claims reproduced (backend 200-passed gate, web 25/25, android typecheck/lint, no dependency changes); exceptions: android device QA not tested, mypy non-blocking gate weakness
- Phase 7A-4 (FCL-078): Android farm-intelligence dashboard consuming the same /dashboard endpoint (first Android auth wiring: SecureStore bearer tokens + inline sign-in); typecheck/lint clean — device QA still pending
- Phase 7A-3 (FCL-077): dashboard documented in API.md (endpoint contract) and APP_FLOW.md (§3a dashboard flow with degradation semantics)
- Phase 7A-2 (FCL-076): web farm-intelligence dashboard — live blocks from the new /dashboard endpoint with loading/empty/error/offline states, explicit unavailable reasons and last-updated timestamps; 25/25 web tests, typecheck/lint/build clean
- Phase 7A-1 (FCL-075): new auth-gated GET /api/v1/dashboard aggregation endpoint (farm/crops/weather/tasks/alerts/recommendations/activity) with per-block availability + fail-open weather; 5 new tests — gate 200 passed
- Owner ACCEPTED Phase 6 (2026-11-01); Phase 7 opened with the 7A farm-intelligence-dashboard implementation plan (single auth-gated aggregation endpoint on existing services; no new tables, no invented metrics)
- Report 1 re-issued (FCL-073): Phase 6 verdict READY FOR OWNER RELEASE APPROVAL — full testing battery evidence, 0 unresolved findings, named deployment-track blockers
- Zero-cost & open-source policy applied (FCL-072): docs/engineering/DEPENDENCY_POLICY.md classifies every external service and code stack (no paid dependencies; Open-Meteo fail-open verified; SearXNG AGPL posture documented)
- Request-ID now rendered in log lines (FCL-071): formatter fix in factory.py — IDs previously echoed in responses but dropped from logs; graceful-shutdown smoke verified (SIGTERM -> clean exit, port released)
- Fixed live chat regression (FCL-070): async endpoint path crashed with UnboundLocalError on farm-less messages (unreachable by pytest's test-mode routing); 500 handler now logs unexpected errors; live chat verified 3x 200 on qwen3:0.6b
- Phase 6 final testing opened: baseline inspection report, timed DR exercise (backup 1s -> restore 7s -> app boots on restored DB -> login 200), QA-caught auth gap on /resources/categories + /resources/{category} closed — gate 195 passed
- Owner decisions executed (FCL-068): /weather + /resources now require authentication (6C M1 closed, 2 new 401 tests); nightly pg_dump backup ACTIVE (cron 02:00, owner-approved, integrity-checked runs verified)
- Report 2 (Phase 6 Production Readiness) issued: verdict PARTIAL — repo-ready, deployment track awaits owner decisions (hosting, domain, backup schedule, M1) — docs/backend/PHASE_6_PRODUCTION_READINESS_REPORT.md
- Phase 6D/6L pre-work: backup.sh (pg_dump, integrity-checked, UNSCHEDULED pending owner approval) + restore drill PASSED — 14/14 tables restored into an isolated throwaway container; live DB touched read-only only
- Phase 6F web standalone production build verified locally (output: standalone, API URL baked at build, server boots 200) + Phase 6G Android release audit delivered (PASS WITH GAPS: no keystore material in git, signing/versionCode/prod-URL/device-QA are owner-side; .gitignore now blocks *.keystore/*.jks/*.pem)
- 6C audit fixes: production validator requires explicit allowed_hosts (M2) and drops a dead secret_key check (L1); logout delete_cookie now matches login cookie attributes so the session cookie is reliably cleared (L2) — gate 192 passed
- Live research evidence (FCL-063): one-shot SearXNG loopback container + live GET /research → 200 with official gov.in domains ranked first (two-tier ranking demonstrated live); Docker/containerd storage verified already on /data — no relocation needed
- Phase 6C/6E production-readiness audits delivered (PASS WITH GAPS, no Critical/High) + live vision evidence: POST /vision/analyze 200 from live qwen3-vl:2b (G2 closed); vision now gated through the model registry (6E G1 fix); cold-start 504 finding: warm VL model before serving or raise OLLAMA_TIMEOUT_SECONDS>=300
- Phase 6I incident runbooks (10 scenarios) + Phase 6N legal/privacy/licensing inventory delivered — public launch gated on privacy policy/ToS/consent/retention + qualified legal review (AGPL, Open-Meteo, DPDP, codebase license choice)
- Phase 6B environment separation verified (production validator, secrets hygiene) + Phase 6J CI pipeline added (.github/workflows/ci.yml: backend/web/android/compose gates, no automated deploy)
- Phase 6A architecture review delivered (read-only): single-host Caddy/proposal, risk register (backups + TLS top risks); awaiting owner approvals before 6B (`docs/backend/PHASE_6A_ARCHITECTURE_REVIEW.md`)
- P5F voice: architecture decision ADR-016 (PROPOSED) — client-platform speech APIs for MVP, no server-side voice service (Phase 0 unauthenticated-voice finding class eliminated); GET /voice/capabilities endpoint; 2 new tests — gate 188 passed
- P5E crop-image assistance: POST /api/v1/vision/analyze (multipart, magic-byte validation, 5 MiB cap, in-memory-only processing) via qwen3-vl:2b — enabled in registry (Model 3 gate resolved); outputs observations/uncertainty/next-steps only, no diagnosis-accuracy claims; 6 new tests — gate 186 passed
- P5D research API: GET /api/v1/research via SearXNG — verbatim http/https citations, official agri-source prioritization, freshness stamps, auth + bounded query, 503 provider-failure mapping; SSRF-safe by construction; 7 new tests — gate 180 passed
- P5C weather-aware chat: prompt template v3 attaches provider-observed, timestamped weather (Open-Meteo) for authorized farm coordinates — fail-open, never invented; 2 new tests — gate 173 passed
- Phase 5 final testing: full regression green (backend 171, web 19/19 + build, android typecheck/lint, compose OK), live API smoke pass, security conditions fixed (prompt-slot sanitization, crop-cycle bounds, no error echo) — **verdict PARTIAL: 5C/5D/5E/5F/5I not implemented** (`docs/backend/PHASE_5_FINAL_TESTING_REPORT.md`)
- Phase 5A/5B/5G committed (`7dafc8a`) together with previously-uncommitted owner work (`d39cb47`); SearXNG hardcoded-secret Phase 0 finding closed (already env-substituted in repo; service not deployed)
- P5G reviewer gate closed: independent QA (PASS) + security review (APPROVE, no conditions) — repo-level user-scoping validated; archived-conversation detail semantics documented; one lint fix (typed user param). Full gate 170 passed
- P5G conversation-history API (read-only, user-scoped: GET /conversations, GET /conversations/{id} with messages) + preferences endpoint (PATCH /auth/preferences, own-only); resolves the Phase 4 FCL-044 product-gap finding; 7 new tests — gate 170 passed
- P5B prompt template v2: safety rules (no invented doses/quantities/withdrawal periods) + farm-context block with injection sanitization; chat accepts farm_id (authorized context, 404 non-members); eval runner now evaluates the shipped system prompt — **live eval 10/10 against qwen3:0.6b**; 8 new tests — gate 163 passed
- P5A gate closed: independent qa (PASS) + security review (APPROVE-WITH-CONDITIONS) — both Medium conditions fixed (farm deactivation owner-only; notes bounded), Lows fixed (double-delete, UUID path params → 422); 1 new test — full gate 155 passed
- P5A-03/04 Farm context assembly service (read-only, membership-scoped; unknown fields never fabricated) + privacy pass (coordinates never logged/leaked); 3 new tests — full gate 154 passed
- P5A-02 Crop-cycle API implemented (`/api/v1/farms/{id}/crop-cycles`, `/api/v1/crop-cycles/{id}`): farm-scoped authz, forward-only status transitions, duplicate-season 409; 9 new tests — full gate 151 passed
- P5A-01 Farm API implemented (`/api/v1/farms*`): farm CRUD + membership with service-level role authz (owner/member/viewer, deny-by-default 404 for non-members) + audit events (ID-only, no coordinates); 12 new tests — full gate 142 passed
- Phase 5 implementation plan written (`docs/roadmaps/phases/PHASE_05_IMPLEMENTATION_PLAN.md`): 5A context engine first — farm/crop models + repositories already exist, only API/service surface missing; 5C/5D/5E/5F approval-gated
- Phase 4 final verification: project work committed (`3b2be0c`); live API matrix 15/16 through the real stack (gateway + Ollama + temp DB) — warm avg 10.6 s; finding recorded (no conversation-history API, Low, Phase 5G); final verification report written — awaiting owner acceptance for Phase 5
- Phase 4 execution report amended with post-report model-gate evidence (Models 3/4/6 states, FCL-042/043); mypy auth fast-follow recorded as PROPOSED
- Model 6 (ASR) asset evaluation (read-only): `ai/voice/` is faster-whisper "small", no local weights, no auth, port 8001 not listening (Phase 0 containment finding not live) — integration blocked on architecture decision + owner input
- Model gates post-exit: Model 3 (vision) BLOCKED on product scope (no image-upload API); Model 4 embedding candidates benchmarked (`qwen3-embedding` 1024d/0.4s, `nomic-embed-text` 768d/0.07s) — decision deferred pending retrieval eval + vector-store approval
- Phase 4 execution report: `docs/backend/PHASE_04_EXECUTION_REPORT.md` — status PARTIAL-by-design, model integration matrix, security findings, test/performance summaries, 3 blockers, 5 owner decisions, next safe step
- Phase 4 exit gate: security-engineer APPROVE-WITH-CONDITIONS (zero Critical/High) — all three conditions closed: local secret/artifact git-ignored, crop/location slot-injection covering test, client-facing error text genericized (no internal detail leakage). qa-reviewer independently verified 129-test gate (now 130)
- Phase 4F integration verification: web (typecheck/lint clean, 19/19 tests, production build OK) and android (typecheck/lint clean) both compile against the flat error envelope — no contract drift
- Phase 4D security pass: prompt-injection containment test at the gateway boundary (injection text stays user-role; system prompt never contaminated); secrets scan clean; full security inventory documented (FCL-039)
- Phase 4 docs pass (P4-09): openapi.json regenerated with `AI_BUSY` 503 documented; API.md error table updated (AI_BUSY/UNAUTHORIZED/TOKEN_EXPIRED/HTTP_ERROR); new `docs/backend/RESOURCE_BUDGET.md` (host limits, serial-inference rules, degradation contract); AGRICULTURAL_QA_FLOW error table aligned with gateway codes
- Eval set + runner (P4-08): `backend/evals/eval_set_v1.json` (versioned, machine-checkable criteria + human-review flags) and `backend/scripts/run_evals.py` — `qwen3:0.6b` passes 4/4 machine checks; groundedness items deferred to human review. Model 2 (`qwen3:4b`) benchmarked: 1/5 OK, stays disabled (does not fit 2 GB VRAM). Model 1 acceptance recorded
- Versioned prompt templates (P4-05): system prompt moved to `app/ai/prompts.py` with `PROMPT_TEMPLATE_VERSION`; system policy separated from user content (no user-text interpolation)
- Model registry (Phase 4B): `app/ai/registry.py` — capability/status/license metadata per model; only `qwen3:0.6b` enabled for per-request selection; gateway validates explicitly requested models before any Ollama call; drift detection vs live tags
- Model benchmarks (P4-04): 4 VRAM-fitting chat candidates measured on the live host (`docs/backend/MODEL_BENCHMARKS.md`) — `qwen3:0.6b` 5/5 prompts OK (avg 11.8 s), remains default; quality claims deferred to the P4-08 evaluation set
- Phase 4 preflight report (all 9 gates PASS) + Model 1 acceptance-matrix tests: empty/missing/oversized message → 422; model context bounded to 10 most recent messages; benchmark harness for chat candidates (`backend/scripts/benchmark_models.py`)
- Model inventory (P4-03): `docs/backend/MODEL_INVENTORY.md` — 16 models (44 GB) verified on `/data` HDD storage (HDD-first compliant); VRAM-fitting chat candidates identified; Gemma license flagged
- AI reliability bounds (P4-02): bounded queue depth (`ai_max_queue_depth`, default 10) — excess requests get 503 `AI_BUSY` instead of unbounded waits; degraded-mode contract documented in `ERROR_RECOVERY_FLOW.md` (no automatic paid-provider fallback; client-disconnect cancellation propagates into gateway calls)
- AI gateway interface (P4-01): provider-independent `AIGateway` protocol + Ollama adapter (`app/ai/gateway.py`); chat path depends on the interface; Ollama errors mapped to gateway types; provider specifics confined to the adapter
- `openapi.json` regenerated after the envelope change (FCL-028); Phase 4 implementation plan drafted (`docs/roadmaps/phases/PHASE_04_IMPLEMENTATION_PLAN.md` — 9 tasks P4-01..P4-09 with absorbed exit-gate fast-follows marked complete)
- Phase 4 fast-follows (from exit-gate review): refresh-token reuse now revokes **all** of the user's refresh tokens (chain-walking left tokens ≥2 generations old live); unified flat error envelope `{detail, error_code}` across endpoints and middlewares via a single exception handler (breaking: nested error bodies no longer returned)
- Exit-gate remediation (security-engineer APPROVE-WITH-CONDITIONS): configurable `ALLOWED_HOSTS` (production must declare real hostnames), chunked `Transfer-Encoding` rejected with 413, bounded lockout-tracking memory, admin account-creation audit now records `actor_id`
- Documentation pass (P3-16/P3-17): `openapi.json` regenerated with auth endpoints; `AUTHENTICATION_FLOW.md` finalized as implemented per ADR-008; new `docs/engineering/AUTHZ_MATRIX.md` (endpoint authorization matrix + STRIDE threat model); API/audit/architecture docs aligned; DECISION_REGISTER Phase 3 gate row added (cookie attributes, bearer path, refresh rotation/reuse-kill, admin gate, no account-enumeration) — `bash scripts/check.sh` 98 tests PASS
- New dependencies: `argon2-cffi` (BSD), `email-validator` (for pydantic `EmailStr`)
- Phase 1 authorization: all six governance gates (G1–G6) formally approved and recorded in `docs/engineering/DECISION_REGISTER.md`
- Owner blanket approval (2026-10-28) recorded: ADR-008/Phase 3 auth, production cutover, P1-17, P1-12
- ADR-008 review (opaque sessions, Argon2id, service-layer authZ) written in `docs/engineering/ADR_REVIEWS.md` — APPROVE; Phase 3 unblocked
- P1-14 container baseline completed: `backend/Dockerfile` rewritten (uv 0.5, `uv sync --frozen --no-dev` from `pyproject.toml`+`uv.lock`, non-root uid 10001, `HEALTHCHECK` on `/health/live`, uvicorn `--factory`); backend container verified healthy against PostgreSQL with real end-to-end chat (qwen3:0.6b) persisting to PostgreSQL (236/577 → 238/581 rows)
- `scripts/ollama-bridge.sh` + user `@reboot` crontab: rootless socat forwarder bridging the Docker bridge gateway → host-loopback Ollama
- Real `/health/ready` dependency checks (DB `SELECT 1` + Ollama health ping; 503 with per-dependency status when degraded) replacing a hardcoded stub
- Phase 1 Readiness Report v2.0 (`docs/engineering/PHASE_1_READINESS_REPORT.md`) — status changed from BLOCKED to APPROVED
- Stage 1 AI integration: `qwen3:0.6b` (522 MB, Q4_K_M) selected as default model — fits 2 GiB VRAM, verified on hardware
- `qwen3:0.6b` Ollama smoke tests: 3/3 agricultural prompts coherent, latency < 10 s
- Backend integration test: `/api/v1/chat` endpoint validated with real model — responses persisted to canonical DB
- End-to-end verification: Web → Backend → Ollama → Response confirmed working
- OpenAPI artifact: `docs/api/openapi.json` generated and committed (CI-validated)
- Documentation updates: `docs/backend/BACKEND_AUDIT.md`, `ARCHITECTURE.md`, `API.md`, `ROADMAP.md` synchronized with Phase 1 implementation
- Phase 2 migration rehearsal completed: `backend/scripts/migrate_sqlite_to_pg.py` (export/load/validate); 236 conversations + 577 messages migrated to disposable PostgreSQL 17 with all validation checks passing
- `docs/backend/DATABASE_SCHEMA.md`: ER diagram + data dictionary for the SQLAlchemy 2 schema
- `docs/backend/BACKUP_RUNBOOK.md`: verified `pg_dump -Fc` backup + restore drill procedure

### Changed
- `backend/app/api/v1/chat.py`: Fixed production-blocking 500 — the sync-session dependency crashed every async-mode request (`RuntimeError: Cannot use sync session in async mode`) before the endpoint body; replaced with `get_db_session_optional` (None in async mode, real session in test mode)
- `backend/app/services/chat.py`: **Data-loss fix** — `generate_chat_response`, `get_conversation_history`, `list_user_conversations` used `async for session in get_db_session()` whose post-yield `commit()` was skipped on `return` (silent rollback); converted to `async with db_manager.session()` which commits on clean exit. Chat writes now persist (verified 238/581 rows)
- `backend/app/core/config.py`: Validator now also normalizes bare `postgresql://` → `postgresql+asyncpg://` (psycopg2 not installed); password injection unchanged
- `backend/app/factory.py`: Alembic startup migrations escape `%` for configparser and run via `asyncio.to_thread` (async env.py `asyncio.run()` crashed inside the lifespan loop); startup DSN log redacted (password leak fixed)
- `docker-compose.yml`: Removed unreadable `.env` mount (12-factor config); backend runs as `${MYFARMAI_UID:-1000}:${MYFARMAI_GID:-1000}` (non-root, bind-mount ownership preserved); `OLLAMA_BASE_URL` + `extra_hosts` added for container→host Ollama
- `docker-compose.yml`: Fixed volume mount to use canonical database (`./backend/data:/app/data` instead of `./data:/app/data`) — resolves dual-DB write split (F2)
- `docker-compose.yml`: Backend now uses passwordless DSN + `DATABASE_PASSWORD_FILE` secret mount — fixes auth failure (hardcoded `myfarmai` password did not match the actual secret)
- `backend/alembic/env.py`: `DATABASE_URL` env var now overrides `alembic.ini` `sqlalchemy.url` (dev URL was hardcoded)
- `backend/app/core/config.py`: `database_password_file` setting with validator injecting the password into passwordless PostgreSQL URLs
- `backend/app/core/config.py`: Default model changed from `qwen3:4b` (2.5 GB) to `qwen3:0.6b` (522 MB) — matches `.env` and hardware constraints
- Governance documentation: All gates updated to APPROVED with owner signatures (2026-10-24)
- Backend documentation: Full synchronization of BACKEND_AUDIT.md, ARCHITECTURE.md, API.md, ROADMAP.md to reflect Phase 1 actual state
- `THIRD_PARTY_NOTICES.md`: SearXNG attribution corrected; versions verified against `uv.lock`

### Fixed
- Canonical database ambiguity resolved: `backend/data/app.db` (234 conv / 573 msg) confirmed as single source of truth
- Model config split-brain resolved: code default, `.env`, and docs now all specify `qwen3:0.6b`
- Swap saturation risk mitigated: default model now fits in available RAM without swap pressure
- All mypy type errors resolved (32 errors across session.py, base.py, chat.py, repositories.py, API)
- Ruff lint/format clean across entire backend

### Added
- Apache-2.0 LICENSE (governance gate G2 approved; decision recorded in `docs/engineering/DECISION_REGISTER.md`)
- `docs/repository-audit.md` — full 2026-10-23 audit: structure, governance status, risks, staged mapping plan
- Phase 6 documentation set verified against code: `docs/project-overview.md`, `docs/architecture.md`, `docs/setup-guide.md`, `docs/api-documentation.md`, `docs/database-design.md`, `docs/demo-guide.md`
- Root `Makefile` (backend-check/dev, web-check/build, android-check, docker up/down/logs, graph-update)
- VS Code workspace config: `.vscode/{settings,tasks,launch,extensions}.json` (tracked via .gitignore exceptions)
- Historical: `REPOSITORY_AUDIT.md` (2026-10-21 audit), `.agents/` project skills, `.opencode/` skills + agents config
- Baseline commits: `ea9d109` (docs/governance/tooling), `c4aece2` (web: Next.js 15 dashboard), `1f543a9` (android: Expo 51 + brand assets)

### Changed
- README: corrected voice-service containment status, Python 3.12 + uv tooling, `CORS_ALLOWED_ORIGINS`, backend uv commands, Apache-2.0 license reference
- `.gitignore`: track selected `.vscode` files; ignore `*.egg-info/`, `*.tsbuildinfo`, entire `graphify-out/` (rebuildable)

### Removed
- Stray scratch files `web/test.ts`, `web/test.tsx`, `web/test-component.tsx`
- Stale `opencode.json` backup files (consistent with prior CHANGELOG claim)
- Root maintenance reports relocated to `docs/engineering/`

### Added
- Repository audit and maintenance workflow (2026-10-21)
- README.md with project overview and quick start
- CONTRIBUTING.md with development workflow
- SECURITY.md with vulnerability reporting
- Maintenance script (scripts/maintenance.sh)
- Extended pre-commit hooks (ruff, mypy, graphify-update)
- Graphify generated artifacts added to .gitignore
- data/.gitkeep placeholder

### Changed
- Updated .gitignore to exclude generated graph files
- Dashboard/web: removed oversized hero and decorative Smart Farming illustrations from the Home dashboard; added compact welcome with "Ask the AI Assistant" and "Check Crop Health" actions (`docs/ui/MODERN_DASHBOARD_AND_UX.md`)

### Fixed
- Removed obsolete opencode.json backup files
- Removed empty resources/ directory

## [0.1.0] - 2026-10-18

### Added
- Initial backend architecture with FastAPI
- Chat endpoint with Ollama integration
- Weather endpoint with Open-Meteo integration
- Agricultural resources catalogue (12 verified Indian resources)
- SQLite async database with conversation persistence
- Voice service with faster-whisper (Hindi/English)
- Docker Compose development environment
- Web frontend foundation (Next.js 15, Tailwind, TanStack Query)
- Android app foundation (Expo, React Native Paper)
- Design system documentation (principles, tokens, components)
- Graphify knowledge graph initialization

### Backend
- REST API v1 with health, chat, weather, resources endpoints
- Pydantic Settings configuration with .env support
- Ollama client with connection pooling and error handling
- Weather client with WMO code mapping
- Conversation CRUD with SQLite

### Frontend (Web)
- Next.js 15 App Router with TypeScript
- Tailwind CSS 3.4 with custom primary scale
- Chat interface with voice input/output
- Weather card component
- Resources list with category filtering
- TanStack Query v5 for server state
- Zustand for client state

### Frontend (Android)
- Expo Router v3 file-based routing
- React Native Paper v5 (Material 3)
- React Native Reanimated 3 for animations
- Expo Speech / Speech Recognition for voice
- Expo SecureStore for local persistence
- Shared API client and types with web

### Documentation
- Backend architecture, API reference, roadmap
- Frontend design system, color system, interaction guidelines
- Integration guides for web and Android
- Frontend dashboard development roadmap

## [0.0.1] - 2026-10-17

### Added
- Initial project structure
- Basic FastAPI application skeleton
- Docker Compose with backend service
- Basic Next.js web application
- Basic Expo Android application