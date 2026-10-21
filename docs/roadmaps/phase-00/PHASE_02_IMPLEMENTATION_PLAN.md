# Phase 2 Implementation Plan — Database Architecture & Migration Readiness

**Phase:** 2 — proposed, not fully executed  
**Date:** 2026-10-21  
**Status:** Core schema and migration infrastructure complete; migration rehearsal and data preservation pending  
**Prerequisites:** Phase 1 complete (quality gates passing, 56/56 tests, ADR-003/004/005 approved)  
**Roadmap:** [`../MyFarmAI_Backend_Roadmap.md`](../MyFarmAI_Backend_Roadmap.md) §5, Phase 2  
**Related:** [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md) ADR-003/004/005, [`GAP_ANALYSIS.md`](GAP_ANALYSIS.md) GAP-016/024/025, [`PHASE_01_IMPLEMENTATION_PLAN.md`](PHASE_01_IMPLEMENTATION_PLAN.md)

---

## 1. Phase 2 Objectives

Per the roadmap and ADRs:
- **ADR-003**: PostgreSQL 17 as system of record; SQLite test-only
- **ADR-004**: Explicit SQLite-to-PostgreSQL migration with canonical data decision
- **ADR-005**: SQLAlchemy 2 + Alembic + asyncpg

**Deliverables:**
1. SQLAlchemy 2 async models for all MVP entities
2. Alembic migration environment (async)
3. Initial migration creating all tables
4. PostgreSQL in docker-compose (dev)
5. Migration rehearsal against disposable DB
6. Backup/restore runbook with evidence
7. ER diagram and data dictionary
8. Cross-user/farm isolation tests

---

## 2. Task Checklist

### 2.1 Dependencies & Configuration
- [x] **P2-01** Add SQLAlchemy 2, asyncpg, alembic, psycopg to `pyproject.toml` and `uv.lock`
- [x] **P2-02** Configure async database session management (engine, sessionmaker)
- [ ] **P2-03** Add PostgreSQL to `docker-compose.yml` (dev profile, internal network)

### 2.2 Domain Models (SQLAlchemy 2)
- [x] **P2-04** Create `Base` and common mixins (timestamps, UUID PK)
- [x] **P2-05** `User` model (auth, profile, status)
- [x] **P2-06** `Farm` model (location, coordinates, owner)
- [x] **P2-07** `FarmMember` model (farm_id, user_id, role, unique pair)
- [x] **P2-08** `Crop` model (catalogue)
- [x] **P2-09** `CropCycle` model (farm, crop, season dates, status)
- [x] **P2-10** `Conversation` model (user_id, farm_id nullable, language, crop, location)
- [x] **P2-11** `Message` model (conversation_id, role CHECK, content, ordering)
- [x] **P2-12** `ResearchQuery` / `ResearchSource` / `Citation` models (Phase 6 prep)
- [x] **P2-13** `AuditEvent` model (security events)
- [x] **P2-14** `Session` / `RefreshToken` models (auth, Phase 3 prep)

### 2.3 Alembic & Migrations
- [x] **P2-15** Initialize Alembic with async environment (`alembic.ini`, `env.py`)
- [x] **P2-16** Generate initial migration (`alembic revision --autogenerate`)
- [x] **P2-17** Review and edit migration (constraints, indexes, FKs, CHECKs)
- [x] **P2-18** Test `alembic upgrade head` on disposable PostgreSQL
- [x] **P2-19** Test `alembic downgrade` / forward-fix

### 2.4 Application Integration
- [x] **P2-20** Replace raw SQL (`db/connection.py`, `db/conversations.py`) with SQLAlchemy repositories
- [x] **P2-21** Update `init_db` to run migrations instead of `CREATE TABLE IF NOT EXISTS`
- [x] **P2-21b** Keep SQLite test path working (enable FKs, same schema via Alembic)
- [ ] **P2-22** Update services to use repositories (chat, weather, resources)

### 2.5 Migration Rehearsal & Data Preservation
- [ ] **P2-23** Export canonical SQLite (`backend/data/app.db`) to CSV/JSON with SHA-256
- [ ] **P2-24** Transform: timestamps → UTC `TIMESTAMPTZ`, roles validate, `legacy_import` user
- [ ] **P2-25** Load into PostgreSQL via `COPY` in transaction
- [ ] **P2-26** Validate: row counts, per-conversation counts, FK integrity, sample spot-check
- [ ] **P2-27** Test app read/write against migrated PostgreSQL

### 2.5 Backup/Restore & Documentation
- [ ] **P2-28** Backup runbook: `pg_dump -Fc`, encryption, `/data` storage, retention
- [ ] **P2-29** Restore drill evidence (disposable DB, verify counts)
- [ ] **P2-30** ER diagram + data dictionary (Mermaid or markdown)
- [ ] **P2-31** Cross-user/farm isolation tests (authorization matrix)

---

## 3. Progress Tracking

| Task | Status | Verified | Notes |
|------|--------|----------|-------|
| P2-01 | VERIFIED | ✅ | SQLAlchemy 2, asyncpg, alembic, psycopg added to pyproject.toml & uv.lock |
| P2-02 | VERIFIED | ✅ | Async session management in `app/db/session.py` |
| P2-03 | TODO | | PostgreSQL in docker-compose.yml (will add in next step) |
| P2-04 | VERIFIED | ✅ | `Base`, `TimestampMixin`, `UUIDMixin` in `app/db/models/base.py` |
| P2-05 | VERIFIED | ✅ | `User` model in `app/db/models/user.py` |
| P2-06 | VERIFIED | ✅ | `Farm` model in `app/db/models/farm.py` |
| P2-07 | VERIFIED | ✅ | `FarmMember` model in `app/db/models/farm.py` |
| P2-08 | VERIFIED | ✅ | `Crop` model in `app/db/models/crop.py` |
| P2-09 | VERIFIED | ✅ | `CropCycle` model in `app/db/models/crop.py` |
| P2-10 | VERIFIED | ✅ | `Conversation` model in `app/db/models/conversation.py` |
| P2-11 | VERIFIED | ✅ | `Message` model in `app/db/models/conversation.py` |
| P2-12 | VERIFIED | ✅ | Research models in `app/db/models/research.py` |
| P2-13 | VERIFIED | ✅ | `AuditEvent` model in `app/db/models/audit.py` |
| P2-14 | VERIFIED | ✅ | `Session`/`RefreshToken` models in `app/db/models/session.py` |
| P2-15 | VERIFIED | ✅ | Alembic async env in `alembic/env.py` |
| P2-16 | VERIFIED | ✅ | Initial migration `6cd2bffd9881_initial_schema.py` |
| P2-17 | VERIFIED | ✅ | Migration reviewed, all tables created |
| P2-18 | VERIFIED | ✅ | `alembic upgrade head` tested on PostgreSQL |
| P2-19 | VERIFIED | ✅ | `alembic downgrade base` tested |
| P2-20 | VERIFIED | ✅ | Repositories in `app/db/repositories.py` |
| P2-21 | VERIFIED | ✅ | `init_db` runs migrations in factory lifespan |
| P2-21b | VERIFIED | ✅ | SQLite test path works with FKs via Alembic |
| P2-22 | TODO | | Update services to use repositories |
| P2-23 | TODO | | Export canonical SQLite to CSV/JSON |
| P2-24 | TODO | | Transform timestamps, validate, legacy_import user |
| P2-25 | TODO | | Load into PostgreSQL via COPY |
| P2-26 | TODO | | Validate row counts, FK integrity |
| P2-27 | TODO | | Test app read/write against PostgreSQL |
| P2-28 | TODO | | Backup runbook: pg_dump, encryption, /data storage |
| P2-29 | TODO | | Restore drill evidence |
| P2-30 | TODO | | ER diagram + data dictionary |
| P2-31 | TODO | | Cross-user/farm isolation tests |

---

## 4. Acceptance Criteria (from roadmap)

- [ ] Canonical source and data retention approved (owner decision recorded)
- [ ] Schema changes are versioned and reviewable (Alembic migrations)
- [ ] Clean database can be created from migrations (`alembic upgrade head`)
- [ ] Migration rehearsal preserves expected records and relationships
- [ ] Cross-user/farm data isolation is tested
- [ ] Restore from backup is demonstrated
- [ ] No production data changed without explicit approval

---

## 5. Notes & Decisions

- **Canonical DB**: `backend/data/app.db` (122 conversations / 315 messages) per `CANONICAL_DB_DECISION.md`
- **Legacy user**: Create `legacy_import` user for migrated conversations without owner
- **PostgreSQL**: Version 17, asyncpg, internal Docker network, volume on `/data`
- **Tests**: Must enable `PRAGMA foreign_keys=ON` for SQLite; run same Alembic schema
- **No production data migration** until explicit approval (per ADR-004)