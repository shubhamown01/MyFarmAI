# MyFarmAI — Phase 1 Readiness Report

**Document ID:** MYFARMAI-P1READY-001  
**Version:** 1.0  
**Date:** 2026-10-21  
**Status:** Draft — Owner Review Required  
**Assessment Type:** Read-only documentation and governance audit — **no implementation executed**

---

## 1. Executive Summary

| Dimension | Status | Evidence |
|-----------|--------|----------|
| **Phase 1 Authorized** | ❌ **NO** — 6 governance gates unresolved | DECISION_REGISTER.md, PRD §18, IMPLEMENTATION_PLAN.md §18 |
| **Documentation Complete** | ✅ **YES** — All product docs present and current | docs/product/ (8 files), flows/ (5 files) |
| **Phase 0 Audit Complete** | ✅ **YES** — 13 audit docs in phase-00/ | VERIFICATION_REPORT.md §4 |
| **Codebase Baseline Known** | ✅ **YES** — Inventory, gaps, risks documented | CURRENT_STATE_AUDIT.md, GAP_ANALYSIS.md |
| **Architecture Decisions** | ⚠️ **PROPOSED** — 15 ADRs, none approved | ARCHITECTURE_DECISIONS.md §1 table |
| **Implementation Plan** | ⚠️ **PROPOSED** — 18 tasks, dependencies mapped | PHASE_01_IMPLEMENTATION_PLAN.md |
| **Test Baseline** | ⚠️ **KNOWN BROKEN** — 49/56 pass on clean DB | VERIFICATION_REPORT.md §3.1, API_CONTRACT_INVENTORY.md §7 |
| **Security Posture** | ⚠️ **HIGH RISK** — 18 findings, 5 High/Critical | SECURITY_AND_PRIVACY_AUDIT.md §2 |
| **Backup/Recovery** | ❌ **NOT READY** — No backup dir, no procedure | BACKUP_AUDIT.md |
| **Android Integration** | ❌ **BROKEN** — Relative URLs, no base URL wiring | GAP-009, API-C-04 |

**Overall Phase 1 Readiness: BLOCKED** — Cannot start until all 6 gates approved.

---

## 2. Governance Gate Status (Blocking)

| Gate | ID | Description | Status | Required Before | Owner |
|------|----|-------------|--------|-----------------|-------|
| **G1** | Canonical SQLite DB | `backend/data/app.db` vs `data/app.db` | **BLOCKED** | P1-01, Phase 2 | Data Owner |
| **G2** | Project License | No LICENSE file; SearXNG AGPL-3.0 | **BLOCKED** | P1-16 | Owner / Legal |
| **G3** | 6 ADRs Approved | ADR-001, 002, 009, 010, 013, 014 | **BLOCKED** | Phase 1 Start | Project Owner / Eng |
| **G4** | Phase 1 Scope | In-scope/out-of-scope lists | **BLOCKED** | Phase 1 Start | Project Owner |
| **G5** | Backup/Recovery Verified | `/data/MyFarmAI-backups` drill | **BLOCKED** | P1-01 | Owner / Ops |
| **G6** | Voice Containment | Confirm no consumers, stop 0.0.0.0:8001 | **BLOCKED** | P1-03 | Product / Ops |

**All six must be APPROVED with evidence before Phase 1 begins.**

---

## 3. Documentation Inventory (Verified Current)

### Product Documents (`/data/MyFarmAI/docs/product/`)

| File | Status | Version | Last Reviewed |
|------|--------|---------|---------------|
| PRD.md | Draft — Owner Review Required | 1.0 | 2026-10-21 |
| TRD.md | Draft — Owner Review Required | 1.0 | 2026-10-21 |
| APP_FLOW.md | Draft — Owner Review Required | 1.0 | 2026-10-21 |
| UI_UX_DESIGN_BRIEF.md | Draft — Owner Review Required | 1.0 | 2026-10-21 |
| UI_UX_DESIGN_SYSTEM.md | Proposed — Owner Review Required | 1.0 | 2026-10-21 |
| BACKEND_SCHEMA.md | Draft — Owner Review Required | 1.0 | 2026-10-21 |
| IMPLEMENTATION_PLAN.md | Draft — Owner Review Required | 1.0 | 2026-10-21 |
| flows/APPLICATION_ENTRY_FLOW.md | Draft — Owner Review Required | 1.0 | 2026-10-21 |
| flows/AGRICULTURAL_QA_FLOW.md | Draft — Owner Review Required | 1.0 | 2026-10-21 |
| flows/RESEARCH_FLOW.md | Draft — Owner Review Required | 1.0 | 2026-10-21 |
| flows/AUTHENTICATION_FLOW.md | Conditional Draft — Owner Review Required | 1.0 | 2026-10-21 |
| flows/ERROR_RECOVERY_FLOW.md | Draft — Owner Review Required | 1.0 | 2026-10-21 |

### Phase 0 Audit Documents (`/data/MyFarmAI/docs/roadmaps/phase-00/`)

| File | Purpose | Status |
|------|---------|--------|
| CURRENT_STATE_AUDIT.md | Full repo inventory, 13 sections | Complete |
| DATABASE_ASSESSMENT.md | Dual SQLite analysis, migration plan | Complete |
| SECURITY_AND_PRIVACY_AUDIT.md | 18 findings (S-01 to S-18) | Complete |
| API_CONTRACT_INVENTORY.md | 11 endpoints, 12 contract risks | Complete |
| DEPENDENCY_INVENTORY.md | All deps with licenses, 10 risks | Complete |
| INTEGRATION_AND_COST_AUDIT.md | 16 integrations, Open-Meteo blocker | Complete |
| GAP_ANALYSIS.md | 37 gaps (15 P0, 12 P1, 7 P2, 3 P3) | Complete |
| TARGET_BACKEND_ARCHITECTURE.md | Proposed modular monolith | Proposed |
| ARCHITECTURE_DECISIONS.md | 15 ADRs, all Proposed | Proposed |
| PHASE_01_IMPLEMENTATION_PLAN.md | 18 tasks, 11 prerequisites | Proposed |
| VERIFICATION_REPORT.md | Phase 0 evidence, no-change confirmation | Complete |
| HARDWARE_AND_DEPLOYMENT_ASSESSMENT.md | 7 GiB RAM, 2 GiB VRAM, disk constraints | Complete |

### New Engineering Documents (Created This Audit)

| File | Purpose | Status |
|------|---------|--------|
| REQUIREMENTS_TRACEABILITY.md | Req → Flow → Design → API → Data → Task → Test → Evidence | Draft |
| DECISION_REGISTER.md | Six-gate decision log with evidence requirements | Draft |
| BACKUP_AUDIT.md | `/data/MyFarmAI-backups` capacity, procedure, risks | Verified |
| PHASE_1_READINESS_REPORT.md | This document | Draft |

---

## 4. Codebase Baseline (Verified Read-Only)

### Repository State
- **Root:** `/data/MyFarmAI` ✅
- **Branch:** `phase-01-foundation` (not `main` as audit reported — branch was created post-audit)
- **Commit:** `3cd1a6e chore: initialize My Farm AI foundation` (single commit)
- **Remote:** None configured ✅ (GAP-001)
- **Untracked:** 50+ files/dirs including all Phase 0 docs, clients, infra ✅
- **Modified (pre-existing):** `.gitignore`, `backend/app/main.py`, `backend/requirements.txt`, `docker-compose.yml` ✅

### Backend (`backend/`)
| Component | Status | Key Files |
|-----------|--------|-----------|
| FastAPI App Factory | Implemented | `app/factory.py`, `app/main.py` |
| Config Profiles | Implemented | `app/core/config.py`, `app/core/config_profiles.py` |
| Health Endpoints | Implemented | `/health`, `/health/live`, `/health/ready` in factory |
| Chat API | Implemented | `app/api/v1/chat.py` (uses `/api/v1/chat`, not `/api/v1/ai/answer`) |
| Weather API | Implemented | `app/api/v1/weather.py` |
| Resources API | Implemented | `app/api/v1/resources.py` |
| Ollama Client | Implemented | `app/services/ollama.py` (concrete, no gateway) |
| SQLite Persistence | Implemented | `app/db/connection.py`, `app/db/conversations.py` |
| Rate Limiting | Implemented | `app/middleware/rate_limit.py` (bypassable via X-Forwarded-For) |
| Request Body Limit | Implemented | `app/factory.py:RequestBodyLimitMiddleware` |
| Structured Logging | Implemented | `app/factory.py` request ID middleware |
| Tests | 56 tests, 7 fail on clean DB | `backend/tests/` |

### Web (`web/`)
| Component | Status | Key Files |
|-----------|--------|-----------|
| Next.js 15 | Configured | `package.json`, `next.config.js` |
| API Client | Working | `src/lib/api/client.ts` (handles nested + flat errors) |
| Tailwind CSS | Configured | `tailwind.config.js`, `postcss.config.js` |
| Tests | 19 Jest tests (prior report) | `src/__tests__/`, `jest.config.js` |

### Android (`android/`)
| Component | Status | Key Files |
|-----------|--------|-----------|
| Expo 51 / RN 0.74 | Configured | `package.json`, `app.json` |
| API Client | **BROKEN** | `src/lib/api/client.ts:29` uses relative `fetch(endpoint)` |
| Base URL Config | Unused | `src/config/api.ts:10-18` `getApiBaseUrl()` never called |
| Secure Storage | Configured | `expo-secure-store` for conversations |

### Infrastructure
| Component | Status | Issues |
|-----------|--------|--------|
| Docker Compose | Valid config | `network_mode: host`, root containers, no healthchecks, floating tags |
| Voice Service | **EXPOSED** | `0.0.0.0:8001`, unauthenticated, no limits, root |
| SearXNG | Running | `127.0.0.1:8890`, hardcoded secret in config |
| Ollama | Running | `127.0.0.1:11434`, `qwen3:4b` (2.5 GB > 2 GiB VRAM) |

---

## 5. Test Baseline (Verified)

### Backend Tests (`backend/tests/`)
| Test File | Tests | Clean-DB Result | Notes |
|-----------|-------|-----------------|-------|
| test_health.py | 3 | PASS | `/`, `/health`, `/api/v1/health` |
| test_chat.py | 7 | **FAIL** | App lifespan not executed; DB schema not initialized |
| test_weather.py | 10 | PASS | Mocked client |
| test_resources.py | 12 | PASS | In-memory catalogue |
| test_schemas.py | 12 | PASS | Pydantic validation |
| test_database.py | 9 | PASS | Temp DB CRUD |
| **Total** | **56** | **49 pass / 7 fail** | **Not hermetic** |

### Static Checks (Backend)
| Tool | Result | Notes |
|------|--------|-------|
| Ruff | PASS | `ruff check app tests` |
| mypy | PASS with warning | Duplicate `[tool.mypy.overrides]` in INI; config not applied correctly |
| pytest | 49/56 | Clean DB run; dev DB untouched |

### Docker Compose
- `docker compose config --quiet` → exit 0 (syntactically valid)

### Web (Prior Maintenance Report)
- 19 Jest tests passed (not re-run in this audit)
- TypeScript/build not verified in this audit

### Android (Prior Maintenance Report)
- Typecheck/lint failed: missing local binaries, wrong `npx` packages
- Not verified in this audit

---

## 6. Security Baseline (Critical Findings)

| ID | Finding | Severity | Phase 1 Task |
|----|---------|----------|--------------|
| S-01 | No authentication on any endpoint | High/Critical | Phase 3 (blocks non-loopback) |
| S-02 | No ownership/tenant boundary | High | Phase 3 |
| S-03 | Voice endpoint unauthenticated, unbounded, root, 0.0.0.0:8001 | High | **P1-03** (contain) |
| S-04 | Hardcoded SearXNG secret in config | High | **P1-02** (rotate) |
| S-05 | Conversation DB not git-ignored | High | **P1-01** (ignore) |
| S-06 | No backup/restore procedure | High | **P1-01** (backup drill) |
| S-07 | Rate limit bypassable via X-Forwarded-For | Medium | **P1-09** (trusted proxy) |
| S-08 | No request body size / AI concurrency limit | Medium | **P1-09** (semaphore) |
| S-09 | CORS/host/transport gaps | Medium | **P1-05** (config profiles) |
| S-10 | Inconsistent error contract, verbose logging | Medium | **P1-07** (flat envelope) |
| S-11 | No retention/deletion/export policy | Medium | Phase 2/3 (ADR-015) |
| S-12 | Container hardening gaps | Medium | **P1-14** (non-root, healthchecks) |
| S-13 | Unpinned deps, no supply-chain gates | Medium | **P1-04**, **P1-12** (uv.lock, CI scans) |
| S-14 | Prompt injection exposure | Medium | Phase 4/6 (ADR-006, 007) |
| S-15 | SSRF surface imminent (research) | Info/High later | Phase 6 (ADR-007) |
| S-16 | .env mode 664 | Low | **P1-02** (chmod 600) |
| S-17 | SQL injection | Low (controlled) | Parameterized queries; maintain |
| S-18 | Unauthenticated resource consumption | Medium | Phase 3 (auth) + P1-09 |

---

## 7. Requirements Traceability Coverage

| Category | Requirements | Traced to Implementation | Traced to Tests | Gaps |
|----------|--------------|--------------------------|-----------------|------|
| Functional (FR-01 to FR-12) | 12 | Partial (FR-01, FR-10, FR-11 partial) | Partial | FR-02, 03, 04, 05, 06, 07, 08, 09 blocked |
| Non-Functional (NFR-01 to NFR-08) | 8 | Partial (NFR-05, NFR-08 partial) | Minimal | NFR-01, 02, 03, 04, 06, 07 blocked |
| Phase 1 Tasks (P1-01 to P1-18) | 18 | 0/18 started | 0/18 verified | All blocked on gates |

**Full traceability matrix:** `docs/engineering/REQUIREMENTS_TRACEABILITY.md`

---

## 8. Phase 1 Task Readiness (Per PHASE_01_IMPLEMENTATION_PLAN.md)

| Task | ID | Prerequisites | Gate Dependency | Ready? |
|------|----|---------------|-----------------|--------|
| Baseline, repo safety, data backup | P1-01 | Prereq 2, 4, 7 | **G1, G5** | ❌ BLOCKED |
| Secret remediation, file perms | P1-02 | Prereq 5 | G2 (secret rotation) | ❌ BLOCKED |
| Contain voice service | P1-03 | Prereq 6 | **G6** | ❌ BLOCKED |
| Python 3.12, uv, lockfile | P1-04 | P1-01 | — | ⏳ AFTER P1-01 |
| Config profiles, safe defaults | P1-05 | P1-04 | — | ⏳ AFTER P1-04 |
| App factory, module boundaries | P1-06 | P1-04, P1-05 | — | ⏳ AFTER P1-05 |
| Consistent error envelope | P1-07 | P1-06, Prereq 11 | **G3 (ADR-009)** | ❌ BLOCKED |
| Health endpoints, structured logging | P1-08 | P1-06 | — | ⏳ AFTER P1-06 |
| Request hardening | P1-09 | P1-05, P1-06 | — | ⏳ AFTER P1-06 |
| Hermetic test suite | P1-10 | P1-06 | **G3 (ADR-013)** | ⏳ AFTER P1-06 |
| Local quality gate (check.sh) | P1-11 | P1-04, P1-10 | — | ⏳ AFTER P1-10 |
| CI and supply-chain checks | P1-12 | P1-04, P1-10, P1-11, Prereq 9 | — | ⏳ AFTER P1-11 |
| OpenAPI artifact, docs correction | P1-13 | P1-06, P1-07, P1-08 | — | ⏳ AFTER P1-08 |
| Container baseline | P1-14 | P1-04, P1-08, P1-15 | — | ⏳ AFTER P1-08, P1-15 |
| Disk/build preflight | P1-15 | Prereq 10 | — | ⏳ READY (read-only) |
| License/third-party notices | P1-16 | Prereq 8 | **G2** | ❌ BLOCKED |
| Model benchmark (optional) | P1-17 | P1-15, owner approval | — | ⏳ OPTIONAL |
| Android base URL fix | P1-18 | Client owner, P1-07 | **G3 (ADR-009)** | ❌ BLOCKED |

**Critical Path:** P1-01 → P1-04 → P1-05 → P1-06 → (P1-07, P1-08, P1-09, P1-10) → P1-11 → P1-12, P1-13, P1-14, P1-16

**P1-01 is blocked on G1 and G5. No Phase 1 work can start until both are APPROVED.**

---

## 9. Risk Register (Top 10)

| Risk | Likelihood | Impact | Current Mitigation | Residual |
|------|------------|--------|-------------------|----------|
| G1/G5 not resolved → Phase 1 cannot start | High | Schedule slip | Clear gate documentation; owner escalation | HIGH |
| Disk fills during Docker build (`/` 5.3 GB free) | High | Build failure, host instability | P1-15 preflight; requires owner approval for cleanup/relocation | HIGH |
| Test refactor (P1-10) introduces regressions | Medium | Hidden bugs | Characterization tests first; keep success shapes | MEDIUM |
| Error contract change (P1-07) breaks web/Android | Medium | Client errors | Coordinate release; contract tests; update both parsers | MEDIUM |
| uv/Python 3.12 migration breaks dependency | Medium | Setup failure | Lockfile, CI, keep old requirements until green | MEDIUM |
| Secret rotation disrupts SearXNG | Low | Brief search outage | Expected; restart and verify; document | LOW |
| Voice stop affects unknown consumer | Low | Feature loss | Confirm no callers; keep code; loopback fallback | LOW |
| CI platform undecided → P1-12 blocked | Medium | CI delay | Local `scripts/check.sh` first; add CI when decided | MEDIUM |
| Scope creep into auth/DB migration | Medium | Phase 1 slip | Enforce §1.2 exclusions; new work needs approval | MEDIUM |
| Shared host contention (Langfuse/Sentinel) | High | Flaky benchmarks/tests | Measure with controlled profile; avoid unrelated stacks | HIGH |

---

## 10. Required Owner Actions (Priority Order)

| # | Action | Gate | Artifact Required | Deadline |
|---|--------|------|-------------------|----------|
| 1 | Choose canonical SQLite file (`backend/data/app.db` or `data/app.db` or neither) | G1 | `CANONICAL_DB_DECISION.md` with owner signature | Before P1-01 |
| 2 | Create and approve backup procedure for `/data/MyFarmAI-backups` | G5 | Restore drill evidence (checksums, row counts, integrity) | Before P1-01 |
| 3 | Approve all 6 ADRs (001, 002, 009, 010, 013, 014) individually | G3 | ADR review records with decision + comments | Before Phase 1 start |
| 4 | Approve Phase 1 scope (in/out of scope lists) | G4 | Signed scope document | Before Phase 1 start |
| 5 | Select project license or defer with date | G2 | `LICENSE` file or deferral record + `THIRD_PARTY_NOTICES.md` | Before P1-16 |
| 6 | Confirm no voice consumers; approve containment | G6 | Consumer grep evidence + Compose decision | Before P1-03 |
| 7 | Approve disk mitigation if P1-15 preflight shows <10 GB headroom | Prereq 10 | Cleanup/relocation approval | Before P1-15 |
| 8 | Choose CI platform/remote | Prereq 9 | CI config in repo | Before P1-12 |
| 9 | Approve error envelope change + coordinated client release | Prereq 11 | Client owner sign-off | Before P1-07 |
| 10 | Approve secret rotation + SearXNG restart | Prereq 5 | Rotation plan + rollback steps | Before P1-02 |

---

## 11. Next Steps

1. **Owner reviews** this report, `DECISION_REGISTER.md`, `BACKUP_AUDIT.md`, `REQUIREMENTS_TRACEABILITY.md`
2. **Owner provides decisions** for Gates G1–G6 (can be batched)
3. **Each decision recorded** in `DECISION_REGISTER.md` with evidence links
4. **Phase 1 begins** only when all six gates show **APPROVED**
5. **Progress tracked** against `PHASE_01_IMPLEMENTATION_PLAN.md` task acceptance criteria

---

## 12. No-Change Confirmation

This readiness audit performed **read-only operations only**:

- ✅ No source code, configuration, or data files modified
- ✅ No databases opened for write; `PRAGMA integrity_check` read-only
- ✅ No containers started, stopped, or rebuilt
- ✅ No packages installed, upgraded, or removed
- ✅ No secrets printed, rotated, or exposed
- ✅ No Git commits, stages, or history changes
- ✅ No Docker images built or pulled
- ✅ No external API calls made (Open-Meteo terms read from public web only)

**Evidence:** All `shell` commands were read-only (`ls`, `df`, `sqlite3 .dump`, `git status`, `cat`, `stat`). No `write`, `edit`, or destructive commands executed.