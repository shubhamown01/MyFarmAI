# MyFarmAI — Combined Phase 0 + Phase 1 Execution Plan

**Document ID:** MYFARMAI-COMBINED-EXEC-001  
**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Active — Execution Authorized  
**Authority:** Combined Phase 0 + Phase 1 Completion Mandate  
**Repository:** `/data/MyFarmAI`

---

## 1. Purpose

This plan consolidates all Phase 0 governance prerequisites and Phase 1 implementation tasks into a single coordinated delivery program with explicit stage gates, dependency tracking, and evidence-based completion criteria. It maps every original Phase 0 prerequisite and Phase 1 task (P1-01 through P1-18) to requirements, dependencies, authorization status, affected files, acceptance criteria, tests, rollback strategy, and actual completion status.

---

## 2. Execution Authority & Constraints

**Authorized:** Autonomous execution of all safe, authorized engineering, documentation, testing, and implementation work.

**Not Authorized (require explicit owner decision):**
- Database deletion, overwrite, merge, relocation, migration
- License selection and LICENSE file creation
- Service stop/reconfiguration before consumer verification
- Secret rotation or public exposure
- Destructive Docker operations or volume removal
- Production deployment or irreversible operations

**Safety Rules:** Read-only investigation first. No `git reset --hard`, forced checkout, broad deletion, or destructive cleanup. Preserve unrelated user modifications.

---

## 3. Combined Task Registry

### Phase 0 Governance Gates (Must Complete Before Phase 1 Tasks)

| Gate | ID | Description | Source | Status | Owner | Evidence Required | Blocks |
|------|----|-------------|--------|--------|-------|-------------------|--------|
| **G1** | Canonical SQLite DB | Choose `backend/data/app.db` vs `data/app.db` | PRD §16, PHASE_01 §2 Prereq#4 | **BLOCKED** | Data Owner | `CANONICAL_DB_DECISION.md` with file path, row counts, preservation rationale, owner signature | P1-01, Phase 2 |
| **G2** | Project License | Select license or defer | PRD §16, PHASE_01 §2 Prereq#8 | **BLOCKED** | Owner/Legal | `LICENSE` file or deferral record + `THIRD_PARTY_NOTICES.md` | P1-16 |
| **G3** | 6 ADRs Approved | ADR-001, 002, 009, 010, 013, 014 | PRD §16, PHASE_01 §2 Prereq#1 | **BLOCKED** | Project Owner/Eng | Individual ADR review records with decision + comments | Phase 1 start, P1-07, P1-10, P1-18 |
| **G4** | Phase 1 Scope | In/out of scope lists approved | PRD §16, PHASE_01 §2 Prereq#1 | **BLOCKED** | Project Owner | Signed scope document | Phase 1 start |
| **G5** | Backup/Recovery | `/data/MyFarmAI-backups` drill | PRD §16, PHASE_01 §2 Prereq#7 | **BLOCKED** | Owner/Ops | Restore drill: checksums, integrity, row counts | P1-01 |
| **G6** | Voice Containment | Confirm no consumers, stop 0.0.0.0:8001 | PRD §16, PHASE_01 §2 Prereq#6 | **BLOCKED** | Product/Ops | Consumer grep evidence + Compose decision | P1-03 |

### Phase 0 Other Prerequisites (From PHASE_01_IMPLEMENTATION_PLAN.md §2)

| Prereq | ID | Description | Needed By | Status |
|--------|----|-------------|-----------|--------|
| Prereq 2 | Commit/bundle approach | Approve committing existing work, branch/remote/bundle | P1-01 | PENDING |
| Prereq 3 | Local-only deployment | Confirm Phase 1 target is loopback only | Before start | PENDING |
| Prereq 5 | Secret rotation approval | SearXNG secret rotation + restart | P1-02 | PENDING |
| Prereq 9 | CI platform/remote | Choose CI platform and remote | P1-12 | PENDING |
| Prereq 10 | Disk mitigation approval | If preflight shows <10 GB headroom | P1-15 | PENDING |
| Prereq 11 | Error envelope coordination | Client owner sign-off for flat envelope | P1-07 | PENDING |

### Phase 1 Implementation Tasks (P1-01 through P1-18)

| Task | ID | Description | Dependencies | Gaps Closed | Status |
|------|----|-------------|--------------|-------------|--------|
| **P1-01** | Baseline, repo safety, data backup | Prereq 2, 4 (G1), 7 (G5) | GAP-001, 002, 003, 004 | **BLOCKED (G1, G5)** |
| **P1-02** | Secret remediation, file perms | Prereq 5 | GAP-005, 027 | **BLOCKED (G2, Prereq 5)** |
| **P1-03** | Contain voice service | Prereq 6 (G6) | GAP-006 | **BLOCKED (G6)** |
| **P1-04** | Python 3.12, uv, lockfile | P1-01 | GAP-012 | ⏳ READY AFTER P1-01 |
| **P1-05** | Config profiles, safe defaults | P1-04 | GAP-011, 019 | ⏳ AFTER P1-04 |
| **P1-06** | App factory, module boundaries | P1-04, P1-05 | GAP-008, 019 | ⏳ AFTER P1-05 |
| **P1-07** | Consistent error envelope | P1-06, Prereq 11 | GAP-017 | **BLOCKED (G3: ADR-009)** |
| **P1-08** | Health endpoints, structured logging | P1-06 | GAP-018 | ⏳ AFTER P1-06 |
| **P1-09** | Request hardening | P1-05, P1-06 | GAP-013, 014 | ⏳ AFTER P1-06 |
| **P1-10** | Hermetic test suite | P1-06 | GAP-008 | ⏳ AFTER P1-06 |
| **P1-11** | Local quality gate (check.sh) | P1-04, P1-10 | GAP-012, 019 | ⏳ AFTER P1-10 |
| **P1-12** | CI and supply-chain checks | P1-04, P1-10, P1-11, Prereq 9 | GAP-012 | ⏳ AFTER P1-11 |
| **P1-13** | OpenAPI artifact, docs correction | P1-06, P1-07, P1-08 | GAP-019 | ⏳ AFTER P1-08 |
| **P1-14** | Container baseline | P1-04, P1-08, P1-15 | GAP-020 | ⏳ AFTER P1-08, P1-15 |
| **P1-15** | Disk/build preflight | Prereq 10 | GAP-015 | ⏳ READY (read-only) |
| **P1-16** | License/third-party notices | Prereq 8 (G2) | GAP-023 | **BLOCKED (G2)** |
| **P1-17** | Model benchmark (optional) | P1-15, owner approval | GAP-021 | ⏳ OPTIONAL |
| **P1-18** | Android base URL fix | Client owner, P1-07 | GAP-009 | **BLOCKED (G3: ADR-009)** |

---

## 4. Gate Resolution Strategy

### G1 — Canonical SQLite Database (Critical Path)
**Investigation Required (Read-Only):**
- [ ] Compare `backend/data/app.db` vs `data/app.db` — schema, row counts, timestamps, integrity
- [ ] Check all application references to database path in code and config
- [ ] Identify any other database files in repository
- [ ] Document which file is used by which workflow (local dev vs Compose)
- [ ] Prepare `CANONICAL_DB_DECISION.md` with recommendation

**Decision Options:**
- A) `backend/data/app.db` (122 conv/315 msgs, local dev default, not git-ignored)
- B) `data/app.db` (35 conv/74 msgs, Compose bind mount, git-ignored)
- C) Neither — start fresh (if owner confirms no data must be preserved)
- D) Both contain unique data — import both with `legacy_source` tag

**Recommendation:** Option A (larger dataset, actively used by local development). Requires owner sign-off.

### G2 — Project License
**Investigation Required:**
- [ ] Enumerate all third-party licenses (SearXNG AGPL-3.0, Ollama MIT, qwen3:4b Apache-2.0, faster-whisper MIT, Python deps)
- [ ] Evaluate MIT, Apache-2.0, AGPL-3.0 compatibility
- [ ] Document trade-offs and recommendation
- [ ] Prepare `LICENSE` decision record

**Recommendation:** MIT or Apache-2.0 (permissive, compatible with all deps). AGPL-3.0 only if SearXNG modifications are planned. Requires owner/legal sign-off.

### G3 — Six ADR Reviews
**Individual Reviews Required (all currently "Proposed"):**

| ADR | Title | Review Focus | Recommendation |
|-----|-------|--------------|----------------|
| ADR-001 | Modular monolith on FastAPI | Architecture fit for 7 GiB host | **Approve** — matches current structure |
| ADR-002 | Python 3.12 + uv lockfile | Reproducibility, supply chain | **Approve** — resolves DEP-01,02,03 |
| ADR-009 | Flat error envelope & request correlation | API contract, client compatibility | **Approve with Changes** — coordinate with web/Android |
| ADR-010 | Single-host Compose + Caddy + internal networks | Deployment, security, isolation | **Approve** — addresses S-03, S-09, S-12 |
| ADR-013 | Hermetic tests, disposable PostgreSQL, CI gates | Test reliability, quality gates | **Approve** — fixes 49/56 test failure |
| ADR-014 | Voice deferred from MVP | Scope reduction, security | **Approve** — removes S-03 High risk |

**Process:** Document each review with: reviewer, date, decision (Approve/Approve with Changes/Reject), comments, resolution of any conflicts.

### G4 — Phase 1 Scope
**Reconciliation Required:**
- [ ] Map PRD FR-01 to FR-12 to Phase 1 tasks
- [ ] Confirm in-scope/out-of-scope lists in PHASE_01_IMPLEMENTATION_PLAN.md §1.1/1.2
- [ ] Identify any scope gaps or conflicts with product docs
- [ ] Produce signed scope document

### G5 — Backup/Recovery Verification
**Actions Required:**
- [ ] Create `/data/MyFarmAI-backups` directory (mode 700)
- [ ] Design backup procedure for canonical SQLite (VACUUM INTO or stop-writes copy)
- [ ] Execute backup → compute SHA-256 → integrity check → restore to disposable path → verify row counts
- [ ] Document evidence in `BACKUP_AUDIT.md`

### G6 — Voice-Service Containment
**Investigation Required (Read-Only):**
- [ ] `grep -r "transcribe\|voice:8001\|8001" backend/ web/ android/` — confirm no consumers
- [ ] `docker inspect myfarmai-voice` — verify configuration
- [ ] Check `docker-compose.yml` for voice service definition
- [ ] Prepare containment plan: stop container, remove 8001:8001 publication, exclude from default profile
- [ ] Document reintroduction criteria per ADR-014

---

## 5. Execution Sequencing

### Wave 0 — Gate Investigation & Documentation (Parallel, Non-Destructive)
1. **G1 Investigation** — SQLite comparison, decision doc
2. **G2 Investigation** — License evaluation, decision doc  
3. **G3 Reviews** — Individual ADR review records
4. **G4 Scope** — Reconciliation, signed scope
5. **G5 Preparation** — Backup directory, procedure design
6. **G6 Investigation** — Voice consumer grep, containment plan
7. **Prereq 2, 3, 9, 10, 11** — Owner decisions on commit approach, local-only, CI platform, disk, error envelope

### Wave 1 — Gate Decisions (Owner Approval Required)
- Owner reviews all investigation docs and records decisions in `DECISION_REGISTER.md`
- Gates G1-G6 updated to APPROVED with evidence
- Prerequisites resolved

### Wave 2 — Phase 1 Implementation (Sequential per Dependencies)
```
P1-01 → P1-04 → P1-05 → P1-06 → (P1-07, P1-08, P1-09, P1-10) → P1-11 → P1-12, P1-13, P1-14, P1-15, P1-16
                                                    ↓
                                               P1-18 (after P1-07)
                                               P1-17 (optional, after P1-15)
```

### Wave 3 — Verification & Final Report
- All Phase 1 exit criteria verified with evidence
- Combined completion report produced

---

## 6. Status Tracking

Use labels from AGENTS.md §8:
- `PASS — verified with evidence`
- `FAIL — verification failed`
- `BLOCKED — approval or dependency required`
- `NOT TESTED — not verified`
- `PROPOSED — not approved`
- `COMPLETE — acceptance criteria verified`

---

## 7. Current Status (As of Plan Creation)

| Component | Status |
|-----------|--------|
| Repository audit | COMPLETE |
| Product documentation review | COMPLETE |
| Phase 0 audit documents | COMPLETE |
| Engineering docs (traceability, decision register, backup audit, readiness) | COMPLETE |
| Gate G1-G6 | **BLOCKED** (all 6) |
| Prerequisites 2,3,5,9,10,11 | **PENDING** |
| Phase 1 tasks P1-01 through P1-18 | **BLOCKED** (all) |
| Safe investigation work | **AUTHORIZED & READY** |

---

## 8. Next Immediate Actions (Authorized Now)

1. **G1 Investigation** — Complete SQLite comparison, write `CANONICAL_DB_DECISION.md`
2. **G2 Investigation** — Complete license evaluation, write decision record
3. **G3 Reviews** — Write individual ADR review records for all 6 required ADRs
4. **G4 Scope** — Write scope reconciliation document
5. **G5 Preparation** — Create `/data/MyFarmAI-backups`, design backup procedure
6. **G6 Investigation** — Complete voice consumer grep, write containment plan
7. **Prereq Decisions** — Request owner decisions on commit approach, local-only confirmation, CI platform, disk mitigation, error envelope coordination

**All above are read-only investigation and documentation — no code, database, service, or infrastructure changes.**