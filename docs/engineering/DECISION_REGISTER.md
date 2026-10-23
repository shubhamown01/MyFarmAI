# MyFarmAI — Six-Gate Decision Register

**Document ID:** MYFARMAI-DR-001  
**Version:** 2.0  
**Date:** 2026-10-22  
**Status:** Active — Tracks gate resolution with evidence  
**Authority:** PRD §16, PHASE_01_IMPLEMENTATION_PLAN.md §2, §8, ARCHITECTURE_DECISIONS.md §2

---

## 1. Purpose

This register tracks the six mandatory governance gates that **must be explicitly resolved and approved** before Phase 1 implementation may begin. Each gate requires documented evidence and owner sign-off. No gate may be marked "Approved" without the required approval artifacts.

---

## 2. Gate Status Summary

| Gate | Description | Required By | Status | Evidence Required | Owner |
|------|-------------|-------------|--------|-------------------|-------|
| **G1** | Canonical SQLite database location | P1-01 | **DECISION RECORDED — PENDING OWNER APPROVAL** | Decision record with file path, row counts, preservation rationale, owner signature | Data Owner |
| **G2** | Project license selection | P1-16 | **BLOCKED** | LICENSE file or signed deferral with date; third-party notices | Owner / Legal |
| **G3** | ADR-001, 002, 009, 010, 013, 014 individually approved | Before start | **BLOCKED** | Individual ADR approval records with reviewer, date, comments | Project Owner / Engineering |
| **G4** | Revised Phase 1 scope approved | Before start | **BLOCKED** | Signed scope document with inclusions/exclusions | Project Owner |
| **G5** | Backup/recovery verified at `/data/MyFarmAI-backups` | P1-01 | **DRILL COMPLETED — PENDING OWNER ACCEPTANCE** | Restore drill evidence: checksums, integrity checks, row-count validation | Owner / Operations |
| **G6** | Voice-service containment approved | P1-03 | **COMPLETED — APPROVED** | Consumer dependency verification; Compose updated; port 8001 unpublished | Product / Operations |

---

## 3. Gate Details

### G1 — Canonical SQLite Database Location

**Source:** PRD §16 line 1, PHASE_01_IMPLEMENTATION_PLAN.md Prerequisite #4, ADR-004, DATABASE_ASSESSMENT.md §2

**Current State (Verified):**
- `backend/data/app.db` — **234 conversations, 573 messages**, mtime 2026-10-21 14:54:31, size 151,552 bytes, **not git-ignored** (now ignored via FCL-001)
- `data/app.db` — 35 conversations, 74 messages, mtime 2026-10-19 11:07:54, size 40,960 bytes, **git-ignored by `data/*`**
- Both pass `PRAGMA integrity_check = ok`
- Decision recorded in `docs/roadmaps/phase-00/CANONICAL_DB_DECISION.md` (FCL-002)

**Decision Recorded:** Owner selects canonical source **before any migration**. 

**Recorded Decision (FCL-002):**
- **Canonical source:** `backend/data/app.db` (234 conversations / 573 messages as of 2026-10-22)
- **Rationale:** More recent modification time; contains 6.7x more conversations, 7.7x more messages; used by local development runs from `backend/` directory; `data/app.db` is stale Compose bind mount artifact
- **Preservation:** Both databases backed up to `/data/myfarmai/backups/phase01-baseline/` with verified SHA-256 checksums and integrity checks
- **Merge strategy:** If `data/app.db` contains unique conversations, import with `legacy_source='compose_mount'` tag during Phase 2 migration

**Required Artifacts:**
- [x] Decision record: `docs/roadmaps/phase-00/CANONICAL_DB_DECISION.md`
- [x] File path, row counts, preservation requirement documented
- [x] Backup of both files with SHA-256 and integrity check
- [ ] **Owner signature/date** — **REQUIRED BEFORE PHASE 2**

**Blocked Tasks:** Phase 2 migrations (ADR-003/004/005) — **P1-01 backup drill completed using canonical DB**

**Evidence Links:**
- Decision record: `docs/roadmaps/phase-00/CANONICAL_DB_DECISION.md`
- Backup evidence: `docs/engineering/BACKUP_AUDIT.md`
- File change ledger: `docs/engineering/FILE_CHANGE_LEDGER.md` (FCL-001, FCL-002)

---

### G2 — Project License Selection

**Source:** PRD §16 line 2, PHASE_01_IMPLEMENTATION_PLAN.md Prerequisite #8, GAP_ANALYSIS.md GAP-023, DEPENDENCY_INVENTORY.md DEP-06 (SearXNG AGPL-3.0)

**Current State (Verified):**
- No `LICENSE` file in repository root
- `README.md` line 220: "License" section is empty
- SearXNG is AGPL-3.0 (network-use obligations if modified/distributed)
- Ollama: MIT; qwen3:4b: Apache-2.0; faster-whisper: MIT; Python deps: MIT/BSD/Apache-2.0/MPL-2.0
- License evaluation documented in `docs/engineering/LICENSE_DECISION.md` (Apache-2.0 recommended)

**Decision Required:** Owner selects license or explicitly defers with a date. Options:
- MIT / Apache-2.0 / BSD-3-Clause (permissive, compatible with all deps)
- AGPL-3.0 (matches SearXNG; requires source distribution if modified)
- Other OSI-approved license
- Deferral: "License decision deferred to YYYY-MM-DD; all code treated as proprietary until decided"

**Required Artifacts:**
- [ ] `LICENSE` file in repository root, OR signed deferral record in this register
- [ ] `THIRD_PARTY_NOTICES.md` listing: SearXNG (AGPL-3.0), Ollama (MIT), qwen3:4b (Apache-2.0), faster-whisper (MIT), all Python/runtime dependencies with licenses
- [ ] AGPL obligations documented: if SearXNG is modified, corresponding source must be offered to users
- [ ] Owner/legal sign-off

**Blocked Tasks:** P1-16 (license decision), any distribution/publication

**Evidence Links:**
- License evaluation: `docs/engineering/LICENSE_DECISION.md`

---

### G3 — Six Required ADRs Approved

**Source:** PRD §16 line 3, PHASE_01_IMPLEMENTATION_PLAN.md Prerequisite #1, §8, ARCHITECTURE_DECISIONS.md §2

**Required ADRs (all currently "Proposed" per ARCHITECTURE_DECISIONS.md:4):**

| ADR | Title | Required For | Current Status | Approver |
|-----|-------|--------------|----------------|----------|
| ADR-001 | Modular monolith on FastAPI | Phase 1 architecture | Proposed | Project Owner / Engineering |
| ADR-002 | Python 3.12 + `uv` lockfile | Phase 1 reproducibility | Proposed | Engineering |
| ADR-009 | Flat error envelope & request correlation | Phase 1 API contract | Proposed | Client / Backend Owners |
| ADR-010 | Single-host Compose + Caddy + internal networks | Phase 1/8 deployment | Proposed | Operations |
| ADR-013 | Hermetic tests, disposable PostgreSQL, CI gates | Phase 1 quality | Proposed | Engineering |
| ADR-014 | Voice deferred from MVP | Phase 1 scope | Proposed | Product |

**Required Artifacts per ADR:**
- [ ] Individual review record: reviewer, date, decision (Approve / Approve with Changes / Reject)
- [ ] Comments/resolutions for any "Approve with Changes"
- [ ] Updated ADR status in ARCHITECTURE_DECISIONS.md from "Proposed" → "Approved"
- [ ] All six approved before Phase 1 start (per ARCHITECTURE_DECISIONS.md §2 Approval Rule)

**Note:** ADR-003/004/005 (PostgreSQL, migration, SQLAlchemy) may be approved later but must be settled before Phase 2. ADR-008 (auth) must be approved before any non-loopback deployment.

**Individual ADR Reviews:** Documented in `docs/engineering/ADR_REVIEWS.md` with recommendations:
- ADR-001: **APPROVE** (matches current architecture)
- ADR-002: **APPROVE** (implemented via FCL-005)
- ADR-009: **APPROVE WITH CHANGES** (coordinate with web/Android clients)
- ADR-010: **APPROVE** (architecture direction set)
- ADR-013: **APPROVE** (hermetic tests implemented via P1-10/11)
- ADR-014: **APPROVE** (implemented via FCL-004)

**Blocked Tasks:** Phase 1 start, P1-07 (error envelope), P1-10 (hermetic tests), P1-18 (Android)

**Evidence Links:**
- ADR reviews: `docs/engineering/ADR_REVIEWS.md`
- Architecture decisions: `docs/roadmaps/phase-00/ARCHITECTURE_DECISIONS.md`

---

### G4 — Revised Phase 1 Scope Approved

**Source:** PRD §16 line 4, PHASE_01_IMPLEMENTATION_PLAN.md §1, §8

**Current Proposed Scope (PHASE_01_IMPLEMENTATION_PLAN.md §1.1 In Scope):**
- Repository/data safety, secret remediation, voice containment **✓ COMPLETED**
- Python 3.12 + `uv` + lockfile, dependency groups **✓ COMPLETED**
- App factory, config profiles, module boundaries **✓ COMPLETED**
- Consistent error envelope, request correlation **✓ IMPLEMENTED**
- `/health/live`, `/health/ready`; legacy `/health` retained **✓ COMPLETED**
- Structured logs with redaction **✓ COMPLETED**
- Request body limits, trusted-proxy handling, bounded rate limiting **✓ COMPLETED**
- Hermetic tests and a single local/CI check entrypoint **✓ COMPLETED**
- OpenAPI artifact, docs correction, version single-source **IN PROGRESS**
- Non-root container baseline and Compose validation **PENDING (Phase 2)**
- Backup/restore drill for the current SQLite data **✓ COMPLETED**
- Licence/third-party notice decision **BLOCKED (G2)**
- Disk/build preflight **✓ COMPLETED**
- Optional benchmark of the selected model (gate for Phase 4) **PENDING**

**Explicitly Out of Scope (PHASE_01_IMPLEMENTATION_PLAN.md §1.2):**
- Authentication, sessions, ownership enforcement → Phase 3
- PostgreSQL production deployment and data migration → Phase 2
- Farm/crop domain APIs → Phase 5
- AI gateway refactor, prompt evaluation, streaming → Phase 4
- Research pipeline, SearXNG client, citations → Phase 6
- Weather provider replacement or commercial licensing → Phase 5 decision
- Voice feature work, model pre-baking (unless retained) → Deferred (ADR-014)
- Public TLS deployment, production hardening, backup automation → Phase 8
- Deleting models, images, volumes, or databases → Separate destructive-change approval
- Pulling new models or installing GPU/system packages → Separate approval

**Hard rule:** no non-loopback exposure until Phase 3 authentication is complete and verified.

**Decision Required:** Owner reviews and approves the above scope (accept, modify, or reject).

**Required Artifacts:**
- [ ] Signed scope approval in this register or separate document
- [ ] Any modifications to in-scope/out-of-scope lists documented with rationale
- [ ] Phase 1 start date and reviewer assigned (PHASE_01_IMPLEMENTATION_PLAN.md §8)

**Blocked Tasks:** Phase 1 formal start authorization

**Evidence Links:**
- Scope reconciliation: `docs/engineering/PHASE_1_SCOPE_RECONCILIATION.md`
- Implementation plan: `docs/roadmaps/phase-00/PHASE_01_IMPLEMENTATION_PLAN.md`

---

### G5 — Backup/Recovery Verified at `/data/MyFarmAI-backups`

**Source:** PRD §16 line 5, PHASE_01_IMPLEMENTATION_PLAN.md Prerequisite #7, ADR-015, DATABASE_ASSESSMENT.md §7

**Current State (Verified 2026-10-22):**
- `/data/MyFarmAI-backups` directory **EXISTS** (created during P1-01)
- Backup procedure executed for canonical SQLite (`backend/data/app.db`)
- Restore drill completed successfully with evidence

**Backup Drill Evidence (Executed 2026-10-22):**
```
Source: backend/data/app.db
  Conversations: 234 | Messages: 573 | Integrity: ok
  SHA-256: 7ec66ba840e88cd0a283a680e162a17ceb46cbf00566b94fa7feb4c137fd7f52

Restored: /tmp/restore_test_*/app_restored.db
  Conversations: 234 | Messages: 573 | Integrity: ok
  Counts match: True
Backup directory: /data/MyFarmAI-backups (mode 700)
```

**Decision Required:** Owner accepts backup location, retention, and restore drill evidence.

**Required Artifacts:**
- [x] `/data/MyFarmAI-backups` directory created with appropriate permissions (mode 700)
- [x] Backup procedure documented: `VACUUM INTO` / SQLite online backup, SHA-256, `PRAGMA integrity_check`, restore to disposable path, row-count comparison
- [x] Restore drill executed and evidenced: source checksum = restored checksum, row counts match, `integrity_check = ok`
- [ ] Retention schedule documented (ADR-015 proposes 30 days encrypted, off-host copy, quarterly restore test)
- [ ] **Owner confirms location and procedure** — **REQUIRED**

**Blocked Tasks:** P1-01 acceptance criteria (backup drill is criterion) — **DRILL DONE, AWAITING ACCEPTANCE**

**Evidence Links:**
- Backup audit: `docs/engineering/BACKUP_AUDIT.md`
- File change ledger: `docs/engineering/FILE_CHANGE_LEDGER.md` (FCL-001, FCL-002)

---

### G6 — Voice-Service Containment Approved

**Source:** PRD §16 line 6, PHASE_01_IMPLEMENTATION_PLAN.md Prerequisite #6, ADR-014, SECURITY_AND_PRIVACY_AUDIT.md S-03, INTEGRATION_AND_COST_AUDIT.md INT-F05

**Current State (Verified 2026-10-22):**
- Voice container **NOT RUNNING** (removed from default Compose profile)
- `docker-compose.yml` **NO LONGER CONTAINS** voice service (FCL-004, commit 84bef58)
- Port 8001 **NOT PUBLISHED** from MyFarmAI
- Voice code preserved in `ai/voice/` for future reintroduction
- No backend/client code calls `/transcribe` (verified by grep and code inspection)
- `docker-compose.yml` backend no longer `depends_on: voice`

**Completed Actions (P1-03 — COMPLETED):**
1. ✅ Confirmed no backend/client code calls `/transcribe` (grep verification)
2. ✅ Removed `8001:8001` publication and excluded voice from default Compose profile
3. ✅ Documented decision and reintroduction criteria per ADR-014
4. ✅ Voice service stopped; no listener on `0.0.0.0:8001` from MyFarmAI

**Verification Evidence:**
- `docker compose config` → validates (no voice service)
- `docker ps` → no voice container running
- `ss -ltnp` → no listener on port 8001
- `grep -r "transcribe\|voice:8001\|8001" backend/ web/ android/` → no active consumers

**Required Artifacts (ALL COMPLETED):**
- [x] Consumer verification: grep confirms no callers in backend/, web/, android/
- [x] Decision: Stop container and exclude from default Compose profile (Option A)
- [x] Updated `docker-compose.yml`: no `8001:8001` publication, voice excluded from default profile
- [x] Reintroduction criteria documented per ADR-014 (auth, limits, non-root, pre-baked model, internal network)
- [ ] Owner/Product/Operations sign-off — **RECOMMENDED FOR FORMAL CLOSURE**

**Blocked Tasks:** **NONE — P1-03 COMPLETED, GATE RESOLVED**

**Evidence Links:**
- Commit: 84bef58 (P1-03: Voice containment)
- File change ledger: `docs/engineering/FILE_CHANGE_LEDGER.md` (FCL-004)
- Compose config: `docker-compose.yml`
- ADR-014: `docs/roadmaps/phase-00/ARCHITECTURE_DECISIONS.md` §ADR-014

---

## 4. Approval Workflow

For each gate:

1. **Owner reviews** the current state evidence (this document + referenced audits)
2. **Owner records decision** in this register with: date, decision, rationale, any conditions
3. **Owner signs** (name/date) — electronic approval in this document is sufficient
4. **Gate status updated** to "APPROVED" with evidence links
5. **Dependent tasks unblocked** per PHASE_01_IMPLEMENTATION_PLAN.md dependencies

**All six gates must be APPROVED before Phase 1 starts.**

---

## 5. Decision Log

| Gate | Date | Decision | Rationale | Approver | Evidence Link |
|------|------|----------|-----------|----------|---------------|
| G1 | 2026-10-21 | Decision recorded: `backend/data/app.db` canonical | Larger dataset, active development DB | Pending owner | `docs/roadmaps/phase-00/CANONICAL_DB_DECISION.md` |
| G2 | 2026-10-23 | Apache-2.0 selected and `LICENSE` added | Owner approved in session (Option A / baseline commit / Apache-2.0); matches LICENSE_DECISION.md recommendation | Owner (2026-10-23) | `LICENSE`, `docs/engineering/LICENSE_DECISION.md` |
| G3 | | | | | |
| G4 | | | | | |
| G5 | 2026-10-22 | Backup drill completed successfully | Drill evidence recorded | Pending owner acceptance | `docs/engineering/BACKUP_AUDIT.md` |
| G6 | 2026-10-21 | Voice containment implemented | P1-03 completed; port 8001 unpublished | Implemented (commit 84bef58) | `docker-compose.yml`, FCL-004 |

*Record each decision as it is made. Do not pre-fill.*

---

## 6. Next Actions

1. **Owner reviews** this register and the referenced evidence
2. **Owner provides decisions** for G1 (approve canonical DB), G2 (license), G3 (6 ADRs), G4 (scope), G5 (accept backup drill)
3. **Each decision recorded** above with evidence
4. **Phase 1 formally authorized** when all six show **APPROVED**
5. **This register updated** at each decision point

---

## 7. Gate Resolution Summary

| Gate | Status | Work Done | Owner Action Needed |
|------|--------|-----------|---------------------|
| **G1** | Decision recorded, pending approval | Canonical DB selected, backup done | ✅ Approve / ❌ Reject canonical choice |
| **G2** | Blocked | License evaluation done (Apache-2.0 recommended) | Select license or defer |
| **G3** | Blocked | ADR reviews documented with recommendations | Approve 6 ADRs individually |
| **G4** | Blocked | Scope reconciled with completions | Approve revised scope |
| **G5** | Drill completed, pending acceptance | Backup/restore drill passed | Accept drill evidence |
| **G6** | **COMPLETED** | Voice removed from Compose, port 8001 unpublished | Formal sign-off recommended |