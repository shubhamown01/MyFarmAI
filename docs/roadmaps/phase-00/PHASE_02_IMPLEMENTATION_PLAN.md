# Phase 2 Implementation Plan — Database Architecture & Migration Readiness

**Phase:** 2  
**Status:** IN_PROGRESS  
**Prerequisites:** Phase 1 complete (56/56 tests, quality gates passing)  
**Related:** [`Phase_02_Database_Architecture.md`](../phases/Phase_02_Database_Architecture.md), [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md) ADR-003/004/005, [`GAP_ANALYSIS.md`](GAP_ANALYSIS.md) GAP-016/024/025

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
- [ ] **P2-02** Configure async database session management (engine, sessionmaker)
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
| P2-01 | TODO | | |
| P2-02 | TODO | | |
| P2-03 | TODO | | |
| P2-04 | TODO | | |
| P2-05 | TODO | | |
| P2-06 | TODO | | |
| P2-07 | TODO | | |
| P2-07 | TODO | | |
| P2-08 | TODO | | |
| P2-09 | TODO | | |
| P2-10 | TODO | | |
| P2-11 | TODO | | |
| P2-12 | TODO | | |
| P2-13 | TODO | | |
| P2-14 | TODO | | |
| P2-15 | TODO | | |
| P2-16 | TODO | | |
| P2-17 | TODO | | |
| P2-18 | TODO | | |
| P2-19 | TODO | | |
| P2-20 | TODO | | |
| P2-21 | TODO | | |
| P2-21b | TODO | | |
| P2-22 | TODO | | |
| P2-23 | TODO | | |
| P2-24 | TODO | | |
| P2-25 | TODO | | |
| P2-26 | TODO | | |
| P2-27 | TODO | | |
| P2-28 | TODO | | |
| P2-29 | TODO | | |
| P2-30 | TODO | | |
| P2-31 | TODO | | |

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