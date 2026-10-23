# MyFarmAI — File Change Ledger

**Document ID:** MYFARMAI-FCL-001  
**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Active — Tracks all file operations from Phase 0/Phase 1 work

---

## Change Record Format

| Field | Description |
|-------|-------------|
| **Change ID** | Unique identifier (FCL-XXX) |
| **Date/Time** | ISO 8601 with timezone |
| **Task Ref** | Phase/Task identifier (e.g., P1-01, P1-03) |
| **File Path** | Repository-relative path |
| **Operation** | CREATE / UPDATE / REWRITE / RENAME / MOVE / DELETE |
| **Reason** | Why this change was made |
| **Authority** | Requirement, ADR, decision, or issue authorizing the change |
| **Previous State** | Summary of prior content/behavior |
| **Changes Made** | Actual modifications |
| **Affected Interfaces** | Routes, schemas, dependencies, callers impacted |
| **Tests/Checks** | Commands executed and results |
| **Risks/Rollback** | Compatibility implications and recovery method |
| **Approval** | Status: PENDING / APPROVED / NOT REQUIRED |
| **Status** | COMPLETE / IN_PROGRESS / BLOCKED |

---

## Changes

### FCL-001 — .gitignore Update for Database Protection

| Field | Value |
|-------|-------|
| **Change ID** | FCL-001 |
| **Date/Time** | 2026-10-21T12:54:29+05:30 |
| **Task Ref** | P1-01 (Repository Safety) |
| **File Path** | `.gitignore` |
| **Operation** | UPDATE |
| **Reason** | Prevent accidental commit of SQLite databases and model caches; protect user conversation data |
| **Authority** | PRD §16 Gate 1, PHASE_01_IMPLEMENTATION_PLAN.md P1-01, GAP_ANALYSIS.md GAP-002 |
| **Previous State** | Only ignored root `data/*`; `backend/data/app.db` was tracked |
| **Changes Made** | Added: `backend/data/*`, `!backend/data/.gitkeep`, `*.db`, `*.sqlite`, `*.sqlite3`, `**/.cache/huggingface/`, `**/models/`, `.local/mcp-memory/`, `graphify-out/*.html`, `graphify-out/graph.json`, `graphify-out/graph.html` |
| **Affected Interfaces** | Git tracking; prevents database files from being committed |
| **Tests/Checks** | `git check-ignore -v backend/data/app.db` → matches; `git ls-files` contains no `*.db`/`*.sqlite*` |
| **Risks/Rollback** | Low risk; rollback = `git checkout HEAD -- .gitignore` |
| **Approval** | APPROVED (commit a82d709) |
| **Status** | COMPLETE |

---

### FCL-002 — Canonical Database Decision Record

| Field | Value |
|-------|-------|
| **Change ID** | FCL-002 |
| **Date/Time** | 2026-10-21T12:54:29+05:30 |
| **Task Ref** | P1-01 (Repository Safety) |
| **File Path** | `docs/roadmaps/phase-00/CANONICAL_DB_DECISION.md` |
| **Operation** | CREATE |
| **Reason** | Record canonical SQLite database decision per governance Gate G1 |
| **Authority** | PRD §16 Gate 1, PHASE_01_IMPLEMENTATION_PLAN.md Prereq #4, ADR-004 |
| **Previous State** | No decision record; two divergent databases existed |
| **Changes Made** | Created decision record selecting `backend/data/app.db` (122 conversations / 315 messages) as canonical; documented rationale, backup evidence, merge strategy for Phase 2 |
| **Affected Interfaces** | Phase 2 migration source; backup procedures |
| **Tests/Checks** | Verified both DBs: `PRAGMA integrity_check=ok`; row counts match backup/restore drill |
| **Risks/Rollback** | Owner approval required before Phase 2; rollback = use alternative source |
| **Approval** | PENDING (recorded for owner review; commit a82d709) |
| **Status** | COMPLETE (decision recorded; awaiting owner sign-off) |

---

### FCL-003 — SearXNG Secret Externalization

| Field | Value |
|-------|-------|
| **Change ID** | FCL-003 |
| **Date/Time** | 2026-10-21T12:57:02+05:30 |
| **Task Ref** | P1-02 (Secret Remediation) |
| **File Path** | `infra/searxng/config/settings.yml` |
| **Operation** | REWRITE (new file replacing hardcoded secret) |
| **Reason** | Remove hardcoded `server.secret_key` from config; load from `SEARXNG_SECRET` environment variable |
| **Authority** | PHASE_01_IMPLEMENTATION_PLAN.md P1-02, SECURITY_AND_PRIVACY_AUDIT.md S-04, GAP_ANALYSIS.md GAP-005 |
| **Previous State** | Hardcoded 64-hex `server.secret_key` in non-gitignored config file |
| **Changes Made** | New settings.yml with `secret_key: "${SEARXNG_SECRET}"`; uses environment variable |
| **Affected Interfaces** | SearXNG container startup; requires `SEARXNG_SECRET` in environment |
| **Tests/Checks** | SearXNG starts with env-provided secret; secret scan clean |
| **Risks/Rollback** | Requires SearXNG restart; rollback = restore previous config (never commit secret) |
| **Approval** | APPROVED (commit 97f913e) |
| **Status** | COMPLETE |

---

### FCL-004 — Voice Service Containment (Compose Removal)

| Field | Value |
|-------|-------|
| **Change ID** | FCL-004 |
| **Date/Time** | 2026-10-21T12:57:15+05:30 |
| **Task Ref** | P1-03 (Voice Containment) |
| **File Path** | `docker-compose.yml` |
| **Operation** | UPDATE (removed voice service) |
| **Reason** | Remove unauthenticated, unbounded voice endpoint from default Compose profile; unpublish port 8001 |
| **Authority** | PHASE_01_IMPLEMENTATION_PLAN.md P1-03, ADR-014, SECURITY_AND_PRIVACY_AUDIT.md S-03, GAP_ANALYSIS.md GAP-006 |
| **Previous State** | Compose had `voice` service with `ports: ["8001:8001"]`, `depends_on: voice`, running as root, no limits |
| **Changes Made** | Removed `voice` service entirely; removed `ports: ["8000:8000"]` and `depends_on: voice` from backend; backend now uses `network_mode: "host"` with volumes for data and .env |
| **Affected Interfaces** | No more public port 8001; backend no longer depends on voice; voice code preserved in `ai/voice/` for future reintroduction |
| **Tests/Checks** | `docker compose config` validates; no listener on `0.0.0.0:8001`; voice container not in default profile |
| **Risks/Rollback** | Voice feature unavailable until reintroduction; rollback = restore voice service in Compose (loopback only per ADR-014) |
| **Approval** | APPROVED (commit 84bef58) |
| **Status** | COMPLETE |

---

### FCL-005 — Python 3.12 + uv Lockfile

| Field | Value |
|-------|-------|
| **Change ID** | FCL-005 |
| **Date/Time** | 2026-10-21T13:04:14+05:30 |
| **Task Ref** | P1-04 (Python 3.12 + uv + Lockfile) |
| **File Path** | `backend/pyproject.toml`, `backend/uv.lock` |
| **Operation** | CREATE |
| **Reason** | Standardize on Python 3.12 with reproducible dependency locking; separate runtime/dev groups |
| **Authority** | PHASE_01_IMPLEMENTATION_PLAN.md P1-04, ADR-002, DEPENDENCY_INVENTORY.md DEP-01/02/03 |
| **Previous State** | Unpinned `requirements.txt`; Python 3.14 local vs 3.12 container; test tooling in production image |
| **Changes Made** | Created `pyproject.toml` with Python 3.12 target, runtime/dev dependency groups; generated `uv.lock` with 559 lines of pinned dependencies |
| **Affected Interfaces** | Backend dependency management; Docker builds; CI; local development |
| **Tests/Checks** | `uv lock --check` passes; `uv sync --frozen` works; `python --version` = 3.12.x in venv |
| **Risks/Rollback** | Keep old `requirements.txt` until new path passes; rollback = revert commit |
| **Approval** | APPROVED (commit d83e834) |
| **Status** | COMPLETE |

---

### FCL-006 — Type Annotations, Quality Gate, Config Profiles, Health Endpoints, Request Hardening

| Field | Value |
|-------|-------|
| **Change ID** | FCL-006 |
| **Date/Time** | 2026-10-21T16:12:00+05:30 (aggregate of f03821f, 067aed0) |
| **Task Ref** | P1-04/P1-11 (Type/Quality), P1-05/08/09 (Config/Health/Hardening) |
| **File Paths** | Multiple backend files (see details) |
| **Operation** | UPDATE / CREATE |
| **Reason** | Implement type safety, config profiles, health endpoints, request hardening per Phase 1 scope |
| **Authority** | PHASE_01_IMPLEMENTATION_PLAN.md P1-05, P1-08, P1-09, P1-11; ADR-009, ADR-010, ADR-013 |
| **Previous State** | Basic config, no health/ready split, no request body limits, basic rate limiting |
| **Changes Made** | 
- `backend/app/core/config_profiles.py`: DEVELOPMENT/TEST/PRODUCTION profiles with validation
- `backend/app/factory.py`: RequestBodyLimitMiddleware, structured logging with request IDs, `/health/live`, `/health/ready`
- `backend/app/middleware/rate_limit.py`: Trusted proxy handling, bounded LRU/TTL limiter
- `backend/pyproject.toml`: Added type annotations, fixed mypy config
- `scripts/check.sh`: Unified quality gate (ruff, mypy, pytest, openapi, compose, secret scan)
| **Affected Interfaces** | All API routes (request IDs, error handling); health checks; rate limiting; configuration |
| **Tests/Checks** | `scripts/check.sh` passes; pytest runs; health endpoints return correct status |
| **Risks/Rollback** | Profiles additive; revert commits if issues |
| **Approval** | APPROVED (commits f03821f, 067aed0) |
| **Status** | COMPLETE |

---

### FCL-007 — Phase 2 Implementation Plan Update

| Field | Value |
|-------|-------|
| **Change ID** | FCL-007 |
| **Date/Time** | 2026-10-21T16:12:00+05:30 |
| **Task Ref** | Phase 2 Planning |
| **File Path** | `docs/roadmaps/phase-00/PHASE_02_IMPLEMENTATION_PLAN.md` |
| **Operation** | UPDATE |
| **Reason** | Update Phase 2 plan with progress tracking from Phase 1 completions |
| **Authority** | Phase 2 planning |
| **Previous State** | Phase 2 plan without Phase 1 completion status |
| **Changes Made** | Updated task statuses to reflect P1-01 through P1-11 completions; adjusted dependencies |
| **Affected Interfaces** | Phase 2 task planning |
| **Tests/Checks** | Plan consistency with completed work |
| **Approval** | APPROVED (commit 3839cff) |
| **Status** | COMPLETE |

---

### FCL-008 — NVIDIA PersonaPlex Feasibility Report

| Field | Value |
|-------|-------|
| **Change ID** | FCL-008 |
| **Date/Time** | 2026-10-22T14:30:00+05:30 |
| **Task Ref** | NVIDIA PersonaPlex Future Voice Integration (Research & Design) |
| **File Path** | `docs/engineering/PERSONAPLEX_FEASIBILITY_REPORT.md` |
| **Operation** | CREATE |
| **Reason** | Document PersonaPlex evaluation for future voice integration decision per mandate |
| **Authority** | NVIDIA PersonaPlex Future Voice Integration mandate (additional requirements) |
| **Previous State** | No PersonaPlex evaluation document |
| **Changes Made** | Created comprehensive feasibility report with licensing, hardware, compatibility, risk assessment, and recommendation |
| **Affected Interfaces** | Future voice architecture decisions |
| **Tests/Checks** | Web search verification, source document retrieval (GitHub, Hugging Face, NVIDIA) |
| **Risks/Rollback** | None (documentation only); rollback = delete file |
| **Approval** | NOT REQUIRED (research/documentation only) |
| **Status** | COMPLETE |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total Changes | 8 |
| CREATE | 4 |
| UPDATE | 3 |
| REWRITE | 1 |
| COMPLETE | 8 |
| PENDING_APPROVAL | 1 (FCL-002 canonical DB) |
| BLOCKED | 0 |

---

## Files Not Modified (Pre-existing User Work Preserved)

The following files were present before Phase 0/1 work and have NOT been modified by this effort:

- `.env.example`, `.omo/`, `.opencode/`, `.pre-commit-config.yaml`, `.setup-backups/`
- `AGENTS.md` (updated separately with Document-First Policy)
- `CHANGELOG.md`, `CONTRIBUTING.md`, `README.md`, `REPOSITORY_AUDIT.md`, `SECURITY.md`
- `android/`, `web/`, `scripts/maintenance.sh`, `skills-lock.json`
- `docs/ADK_EVALUATION.md`, `docs/AGENT_TEAM.md`, `docs/AGENT_TEAM_DELEGATION.md`, `docs/PERSONAPLEX_BOUNDARY.md`
- `graphify-out/`, `maintenance-report-*.md`, `opencode.json*`

All Phase 0 audit documents in `docs/roadmaps/phase-00/` and engineering documents in `docs/engineering/` were created as new files during the audit phase and are tracked separately.