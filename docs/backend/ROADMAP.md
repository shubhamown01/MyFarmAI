# MyFarm AI Backend — Roadmap

**Current Status:** Phase 1 Complete ✅ — Quality Gates Passing  
**Date:** 2026-10-28  
**Version:** 0.1.0 (aligned with `settings.app_version`)

---

## Phase 0: Read-Only Audit ✅ COMPLETE

**Completed:** 2026-10-24  
**Documents:** 13 audit docs in `docs/roadmaps/phase-00/`

| Deliverable | Status |
|-------------|--------|
| Current State Audit | ✅ Complete |
| Database Assessment | ✅ Complete |
| Security & Privacy Audit (18 findings) | ✅ Complete |
| API Contract Inventory | ✅ Complete |
| Dependency Inventory | ✅ Complete |
| Integration & Cost Audit | ✅ Complete |
| Gap Analysis (37 gaps) | ✅ Complete |
| Target Backend Architecture | ✅ Complete |
| Architecture Decisions (15 ADRs) | ✅ Complete |
| Phase 1 Implementation Plan | ✅ Complete |
| Phase 2 Implementation Plan | ✅ Complete |
| Hardware & Deployment Assessment | ✅ Complete |
| Verification Report | ✅ Complete |

**Governance Gates (All APPROVED 2026-10-24):**
| Gate | Description | Status |
|------|-------------|--------|
| G1 | Canonical SQLite DB (`backend/data/app.db`) | ✅ APPROVED |
| G2 | Project License (Apache-2.0) | ✅ APPROVED |
| G3 | 6 ADRs Approved (001, 002, 009, 010, 013, 014) | ✅ APPROVED |
| G4 | Phase 1 Scope Approved | ✅ APPROVED |
| G5 | Backup/Recovery Verified at `/data/MyFarmAI-backups` | ✅ APPROVED |
| G6 | Voice Service Contained | ✅ APPROVED |

**Phase 2 Authorization:** ADR-003, 004, 005 APPROVED — Migration authorized.

---

## Phase 1: Backend Foundation ✅ COMPLETE

**Completed:** 2026-10-28  
**Quality Gate:** All checks passing

| Task | Status | Evidence |
|------|--------|----------|
| P1-01: Baseline, repo safety, backup | ✅ | FCL-001, FCL-002, G1, G5 |
| P1-02: Secret remediation, file perms | ✅ | FCL-003, G2 |
| P1-03: Voice containment | ✅ | FCL-004, FCL-012, G6 |
| P1-04: Python 3.12, uv, lockfile | ✅ | FCL-005 |
| P1-05: Config profiles, safe defaults | ✅ | `config_profiles.py` |
| P1-06: App factory, module boundaries | ✅ | `factory.py` |
| P1-07: Error envelope, request IDs | ✅ | ADR-009 implemented |
| P1-08: Health endpoints, logging | ✅ | `/health/live`, `/health/ready` |
| P1-09: Request hardening | ✅ | Body limits, trusted proxy, bounded limiter |
| P1-10: Hermetic test suite | ✅ | 56/56 pass, dev DB untouched |
| P1-11: Local quality gate | ✅ | `scripts/check.sh` passes |
| P1-12: CI and supply-chain | ⏳ | CI platform TBD (Prereq 9) |
| P1-13: OpenAPI artifact, docs | ✅ | `docs/api/openapi.json` generated, docs updated |
| P1-14: Container baseline | ⏳ | Phase 2 (Compose ready, non-root) |
| P1-15: Disk/build preflight | ✅ | 74 GB free on `/` |
| P1-16: License/third-party notices | 🔄 | Apache-2.0 LICENSE, THIRD_PARTY_NOTICES.md pending |
| P1-17: Model benchmark | ⏳ | Optional, Phase 4 gate |
| P1-18: Android base URL fix | ✅ | FCL-010, compiles clean |

### Test Results
- **Backend:** 56/56 tests passing (health, chat, weather, resources, schemas, database)
- **Ruff format:** 37 files formatted
- **Ruff lint:** All checks passed
- **MyPy:** Success — no issues in 39 source files
- **Quality Gate:** `scripts/check.sh` passes completely

### Key Deliverables
1. **FastAPI App Factory** with DEVELOPMENT/TEST/PRODUCTION profiles
2. **Configuration Validation** — fails fast on unsafe production config
3. **Health Endpoints** — `/health` (liveness), `/health/live`, `/health/ready` (readiness)
4. **Structured Logging** — Request ID correlation, JSON-ready, secret redaction
4. **Rate Limiting** — Bounded LRU/TTL, trusted proxy handling, per-route limits, 429 + Retry-After
5. **Request Body Limits** — 1 MB default, configurable, 413 before buffering
6. **Error Envelope** — Flat JSON (ADR-009), stable error codes, request_id correlation
7. **Hermetic Tests** — Per-test temp SQLite, Alembic schema init, FK enforcement
8. **SQLAlchemy 2 + Alembic** — Async models, repositories, initial migration tested
9. **OpenAPI Artifact** — `docs/api/openapi.json` committed, CI-diffable
10. **Docker Compose** — PostgreSQL + backend, internal network, secrets, healthchecks

---

## Phase 2: Database Architecture & Migration ✅ REHEARSAL COMPLETE (Cutover Pending Approval)

**Status:** All rehearsal tasks complete and verified; production cutover requires separate owner approval

**Approved ADRs:**
- ADR-003: PostgreSQL 17 as system of record; SQLite test-only
- ADR-004: Explicit SQLite-to-PostgreSQL migration with canonical data decision
- ADR-005: SQLAlchemy 2 + Alembic + asyncpg

### Infrastructure Complete ✅
| Task | Status |
|------|--------|
| P2-01: SQLAlchemy 2, asyncpg, alembic, psycopg in pyproject.toml | ✅ |
| P2-02: Async database session management | ✅ |
| P2-03: PostgreSQL in docker-compose.yml | ✅ |
| P2-04 through P2-14: All SQLAlchemy models | ✅ |
| P2-15 through P2-19: Alembic setup, initial migration, upgrade/downgrade tested | ✅ |
| P2-20: Repositories replacing raw SQL | ✅ |
| P2-21: init_db runs migrations | ✅ |
| P2-21b: SQLite test path works with FKs | ✅ |

### Migration Rehearsal — COMPLETE ✅ (2026-10-28, FCL-018)
| Task | Status | Evidence |
|------|--------|----------|
| P2-22: Services use repositories | ✅ | Chat service uses ConversationRepository/MessageRepository |
| P2-23: Export canonical SQLite with SHA-256 | ✅ | 236 conv / 577 msg, SHA-256 `e27319f7...` |
| P2-24: Transform (UTC TIMESTAMPTZ, legacy_import user, role validation) | ✅ | `migrate_sqlite_to_pg.py` |
| P2-25: Load via COPY in transaction | ✅ | Single transaction; refuses non-empty target |
| P2-26: Validate counts/FK integrity | ✅ | All 7 checks PASS |
| P2-27: App read/write on migrated PostgreSQL | ✅ | Repository read + write + read-back; sequence fix verified |
| P2-28: Backup runbook | ✅ | `docs/backend/BACKUP_RUNBOOK.md` |
| P2-29: Restore drill | ✅ | `pg_dump -Fc` → fresh DB → 1/236/577, 0 orphans PASS |
| P2-30: ER diagram + data dictionary | ✅ | `docs/backend/DATABASE_SCHEMA.md` |
| P2-31: Cross-user/farm isolation tests | ✅ | 4/4 PASS, cleanup verified |

**Findings fixed during rehearsal:**
- psycopg3 `cursor.copy()` context-manager usage (silent 0-row insert)
- COPY does not advance the serial sequence — `setval` added to load step
- `alembic.ini` hardcoded dev URL → `DATABASE_URL` override in `env.py`
- Compose backend hardcoded wrong DB password → `DATABASE_PASSWORD_FILE` secret injection

**Canonical Source:** `backend/data/app.db` (236 conversations / 577 messages as of 2026-10-28, SHA-256 verified)

**Acceptance Criteria (from roadmap):**
- [x] Canonical source and data retention approved (owner decision recorded) ✅
- [x] Schema changes are versioned and reviewable (Alembic migrations) ✅
- [x] Clean database can be created from migrations (`alembic upgrade head`) ✅
- [x] Migration rehearsal preserves expected records and relationships ✅ (236/577, 0 orphans)
- [x] Cross-user/farm data isolation is tested ✅ (4/4)
- [x] Restore from backup is demonstrated ✅ (drill evidence in runbook)
- [x] No production data changed without explicit approval ✅ (rehearsal only; SQLite untouched)

**⚠️ Production cutover (repointing live data to PostgreSQL) requires separate explicit owner approval — NOT performed.**

---

## Phase 3: Authentication and Security ⏳ PLANNED

**Prerequisites:** Phase 2 migration complete, ADR-008 approved

**Approved ADR:** ADR-008 (Opaque sessions/tokens, Argon2id, service-layer authorization) — Proposed, needs approval

| Feature | Status |
|---------|--------|
| User registration/login | ⏳ |
| Password hashing (Argon2id) | ⏳ |
| Session/token lifecycle | ⏳ |
| Authentication middleware | ⏳ |
| Authorization & resource ownership | ⏳ |
| Conversation/farm-profile isolation | ⏳ |
| Rate limiting & abuse controls | ⏳ |
| Secure secret configuration | ⏳ |
| Logout, expiry, revocation | ⏳ |
| Privacy-aware logs/errors | ⏳ |
| Auth matrix tests | ⏳ |

**Hard Rule:** No non-loopback exposure until Phase 3 complete and verified.

---

## Phase 4: Local AI (AI Gateway) ⏳ PLANNED

**Prerequisites:** Phase 3 complete, ADR-006 approved, model benchmark (P1-17)

**Approved ADR:** ADR-006 (Provider-independent AI gateway over Ollama) — Proposed

| Feature | Status |
|---------|--------|
| AIProvider interface | ⏳ |
| Ollama adapter | ⏳ |
| Model allowlist + prompt versioning | ⏳ |
| Bounded concurrency semaphore | ⏳ |
| Timeouts + retry policy | ⏳ |
| Resource-aware fallback | ⏳ |
| Structured errors + model status | ⏳ |
| Testable adapters (mockable) | ⏳ |

**Model Gate:** Before Phase 4, benchmark `qwen3:4b` and smaller candidate on ag prompts. Measure latency, RAM/VRAM, concurrency behavior. If targets fail, select smaller model or reduce context.

---

## Phase 5: Agriculture Integrations ⏳ PLANNED

**Prerequisites:** Phase 3 complete, ADR-011 decision

**Approved ADR:** ADR-011 (Weather adapter, Open-Meteo non-commercial only) — Proposed

| Feature | Status |
|---------|--------|
| Farm/crop domain APIs | ⏳ |
| Weather provider decision (commercial license or alternative) | ⏳ |
| Licensed public data adapters | ⏳ |
| Provenance-aware data | ⏳ |

---

## Phase 6: Research Engine ⏳ PLANNED

**Prerequisites:** Phase 3 complete, ADR-007 approved

**Approved ADR:** ADR-007 (SearXNG + PostgreSQL FTS; Qdrant deferred) — Proposed

| Feature | Status |
|---------|--------|
| Search adapter (SearXNG) | ⏳ |
| Safe page fetching (SSRF protection) | ⏳ |
| Source ranking + provenance | ⏳ |
| Citations + stored provenance | ⏳ |
| Retrieval evaluation (PG FTS vs Qdrant) | ⏳ |

---

## Phase 7: Optional Jobs & Search Upgrades ⏳ DEFERRED

**Prerequisites:** Measured need per ADR-012

| Feature | Trigger |
|---------|---------|
| Valkey + background workers | Request latency exceeds target due to deferrable work |
| Qdrant vector search | PostgreSQL FTS fails defined retrieval evaluation |
| Extra observability | Second backend worker requires external session/rate limit state |

---

## Phase 8: Deployment Hardening ⏳ PLANNED

| Feature | Status |
|---------|--------|
| Caddy TLS termination (80/443) | ⏳ |
| Least privilege containers | ⏳ |
| Network boundaries | ⏳ |
| Backup automation (pg_dump + WAL) | ⏳ |
| Operations runbooks | ⏳ |

---

## Phase 9: CI & Release Readiness ⏳ PLANNED

| Feature | Status |
|---------|--------|
| CI platform selection | ⏳ |
| Repeatable tests + security checks | ⏳ |
| Release gates | ⏳ |
| Recovery validation | ⏳ |

---

## PersonaPlex Voice Integration (Optional, Gated)

**Status:** Deferred from MVP (ADR-014). All phases gated.

| Phase | Name | Depends On |
|-------|------|------------|
| P0 | Feasibility & Access | HF approval, license review, GPU gate |
| P1 | Shared Model Storage | P0 |
| P2 | Inference Runtime Prototype | P1 |
| P3 | Hardware Deployment Strategy | P2 |
| P4 | Reusable Voice Service | P3, Phase 3 |
| P5 | AI Gateway Integration | P4, Phase 3 |
| P6 | Web Integration | P5, Phase 7 |
| P7 | Android Integration | P5, Phase 8 |
| P8 | Agricultural Conversational Behavior | P5, Phase 5 |
| P9 | Security, Privacy & Compliance | P4, Phase 3 |
| P10 | Performance & Reliability | P4, P8, P9 |
| P11 | Production Readiness & Reuse | P10 |

**Gates:** Each phase requires explicit approval. Not part of core MVP.

---

## Execution Order & Hard Gates

1. **Phase 0 complete and reviewed** ✅ — Before any implementation
2. **Phase 1 must not begin until explicit approval recorded** ✅ — All G1-G6 APPROVED
3. **Preserve pre-existing uncommitted work and both SQLite databases** ✅ — Until roles approved
4. **Investigate 7 clean-DB test failures** ✅ — Fixed via hermetic test refactor (56/56 pass)
5. **Contain unauthenticated voice service** ✅ — Removed from Compose, port 8001 unpublished
6. **Remediate hardcoded SearXNG secret** ✅ — Rotated, externalized to env (FCL-003)
7. **No public exposure until auth, TLS, host/CORS, rate limiting reviewed** ✅ — Loopback only
8. **No commercial weather provider until license permits** ⏳ — ADR-011 decision pending
9. **Test SQLite-to-PostgreSQL migration on disposable copy** ⏳ — Phase 2 rehearsal
10. **Defer voice, Valkey, workers, Qdrant, extra observability** ✅ — ADR-012, ADR-014

---

## Technology Direction (Implemented)

- ✅ FastAPI, Pydantic, Python 3.12, `uv` with committed `uv.lock`
- ✅ SQLAlchemy 2 + Alembic (async)
- ✅ PostgreSQL 17 for production (Compose ready)
- ✅ SQLite for isolated tests only (FK enforcement)
- ✅ Ollama behind provider-independent gateway (Phase 4)
- ✅ SearXNG for self-hosted search; PG FTS initially (Phase 6)
- ✅ Docker Compose: non-root, internal networks, health checks, secrets
- ✅ Pytest, Ruff, MyPy, dependency/license checks, security regression tests

---

## Definition of Done (Per Phase)

A phase is complete only when:
- [ ] Deliverables exist and are implemented
- [ ] Acceptance tests pass with evidence
- [ ] Security and licensing implications reviewed
- [ ] Documentation updated (API, ARCHITECTURE, CHANGELOG, etc.)
- [ ] Unresolved issues marked and tracked
- [ ] Phase exit gate explicitly accepted

---

*Roadmap reflects current state as of Phase 1 completion (2026-10-28). Phase 2 migration rehearsal is the next major implementation milestone.*