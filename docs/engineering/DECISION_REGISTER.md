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
| **G1** | Canonical SQLite database location | P1-01 | **APPROVED** | Decision record with file path, row counts, preservation rationale, owner signature | Data Owner |
| **G2** | Project license selection | P1-16 | **APPROVED** | LICENSE file (Apache-2.0); third-party notices | Owner / Legal |
| **G3** | ADR-001, 002, 009, 010, 013, 014 individually approved | Before start | **APPROVED** | Individual ADR approval records with reviewer, date, comments | Project Owner / Engineering |
| **G4** | Revised Phase 1 scope approved | Before start | **APPROVED** | Signed scope document with inclusions/exclusions | Project Owner |
| **G5** | Backup/recovery verified at `/data/MyFarmAI-backups` | P1-01 | **APPROVED** | Restore drill evidence: checksums, integrity checks, row-count validation | Owner / Operations |
| **G6** | Voice-service containment approved | P1-03 | **APPROVED** | Consumer dependency verification; Compose updated; port 8001 unpublished | Product / Operations |

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
- [x] **Owner signature/date** — **APPROVED 2026-10-24**

**Blocked Tasks:** **NONE — GATE APPROVED**

**Evidence Links:**
- Decision record: `docs/roadmaps/phase-00/CANONICAL_DB_DECISION.md`
- Backup evidence: `docs/engineering/BACKUP_AUDIT.md`
- File change ledger: `docs/engineering/FILE_CHANGE_LEDGER.md` (FCL-001, FCL-002)

---

### G2 — Project License Selection

**Source:** PRD §16 line 2, PHASE_01_IMPLEMENTATION_PLAN.md Prerequisite #8, GAP_ANALYSIS.md GAP-023, DEPENDENCY_INVENTORY.md DEP-06 (SearXNG AGPL-3.0)

**Current State (Verified):**
- `LICENSE` file in repository root: **Apache-2.0** (11,358 bytes, added 2026-10-23)
- SearXNG is AGPL-3.0 (network-use obligations if modified/distributed)
- Ollama: MIT; qwen3:4b: Apache-2.0; faster-whisper: MIT; Python deps: MIT/BSD/Apache-2.0/MPL-2.0
- License evaluation documented in `docs/engineering/LICENSE_DECISION.md` (Apache-2.0 recommended)

**Decision Recorded:** Owner selected **Apache-2.0** (2026-10-23), `LICENSE` file present.

**Required Artifacts:**
- [x] `LICENSE` file in repository root (Apache-2.0)
- [ ] `THIRD_PARTY_NOTICES.md` listing: SearXNG (AGPL-3.0), Ollama (MIT), qwen3:4b (Apache-2.0), faster-whisper (MIT), all Python/runtime dependencies with licenses
- [ ] AGPL obligations documented: if SearXNG is modified, corresponding source must be offered to users
- [x] Owner/legal sign-off — **APPROVED 2026-10-24**

**Blocked Tasks:** **NONE — GATE APPROVED** (THIRD_PARTY_NOTICES.md tracked as follow-up)

**Evidence Links:**
- License evaluation: `docs/engineering/LICENSE_DECISION.md`
- License file: `LICENSE`

---

### G3 — Six Required ADRs Approved

**Source:** PRD §16 line 3, PHASE_01_IMPLEMENTATION_PLAN.md Prerequisite #1, §8, ARCHITECTURE_DECISIONS.md §2

**Required ADRs (all currently "Proposed" per ARCHITECTURE_DECISIONS.md:4):**

| ADR | Title | Required For | Current Status | Approver |
|-----|-------|--------------|----------------|----------|
| ADR-001 | Modular monolith on FastAPI | Phase 1 architecture | **APPROVED** | Project Owner / Engineering |
| ADR-002 | Python 3.12 + `uv` lockfile | Phase 1 reproducibility | **APPROVED** | Engineering |
| ADR-009 | Flat error envelope & request correlation | Phase 1 API contract | **APPROVED** | Client / Backend Owners |
| ADR-010 | Single-host Compose + Caddy + internal networks | Phase 1/8 deployment | **APPROVED** | Operations |
| ADR-013 | Hermetic tests, disposable PostgreSQL, CI gates | Phase 1 quality | **APPROVED** | Engineering |
| ADR-014 | Voice deferred from MVP | Phase 1 scope | **APPROVED** | Product |

**Required Artifacts per ADR:**
- [x] Individual review record: reviewer, date, decision (Approve / Approve with Changes / Reject)
- [x] Comments/resolutions for any "Approve with Changes"
- [x] Updated ADR status in ARCHITECTURE_DECISIONS.md from "Proposed" → "Approved"
- [x] All six approved before Phase 1 start (per ARCHITECTURE_DECISIONS.md §2 Approval Rule)

**Note:** ADR-003/004/005 (PostgreSQL, migration, SQLAlchemy) may be approved later but must be settled before Phase 2. ADR-008 (auth) must be approved before any non-loopback deployment.

**Individual ADR Reviews:** Documented in `docs/engineering/ADR_REVIEWS.md` with recommendations:
- ADR-001: **APPROVE** (matches current architecture)
- ADR-002: **APPROVE** (implemented via FCL-005)
- ADR-009: **APPROVE WITH CHANGES** (coordinate with web/Android clients)
- ADR-010: **APPROVE** (architecture direction set)
- ADR-013: **APPROVE** (hermetic tests implemented via P1-10/11)
- ADR-014: **APPROVE** (implemented via FCL-004)

**Owner Decision:** All six ADRs individually **APPROVED 2026-10-24**.

**Blocked Tasks:** **NONE — GATE APPROVED**

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
- Licence/third-party notice decision **✓ RESOLVED (G2)**
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

**Owner Decision:** Scope **APPROVED 2026-10-24** as documented in PHASE_01_IMPLEMENTATION_PLAN.md §1.1/§1.2.

**Required Artifacts:**
- [x] Signed scope approval in this register
- [x] Phase 1 start date and reviewer assigned: **2026-10-24**

**Blocked Tasks:** **NONE — GATE APPROVED**

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
- [x] **Owner confirms location and procedure** — **APPROVED 2026-10-24**

**Blocked Tasks:** **NONE — GATE APPROVED** (retention schedule tracked as follow-up)

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
- [x] Owner/Product/Operations sign-off — **APPROVED 2026-10-24**

**Blocked Tasks:** **NONE — GATE APPROVED**

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
| G1 | 2026-10-24 | Canonical DB `backend/data/app.db` approved | Larger dataset (234 conv/573 msg), active development DB; Compose mount fixed to use canonical | Owner (2026-10-24) | `docs/roadmaps/phase-00/CANONICAL_DB_DECISION.md`, `docker-compose.yml` |
| G2 | 2026-10-23 | Apache-2.0 selected and `LICENSE` added | Matches LICENSE_DECISION.md recommendation; permissive, compatible with all deps | Owner (2026-10-23) | `LICENSE`, `docs/engineering/LICENSE_DECISION.md` |
| G3 | 2026-10-24 | All six ADRs (001, 002, 009, 010, 013, 014) individually approved | ADR reviews documented with recommendations; all match implemented architecture | Owner (2026-10-24) | `docs/engineering/ADR_REVIEWS.md`, `docs/roadmaps/phase-00/ARCHITECTURE_DECISIONS.md` |
| G4 | 2026-10-24 | Phase 1 scope approved as documented | In-scope items match completed work; out-of-scope items properly deferred | Owner (2026-10-24) | `docs/roadmaps/phase-00/PHASE_01_IMPLEMENTATION_PLAN.md` |
| G5 | 2026-10-24 | Backup drill accepted | Drill evidence: checksums match, row counts match, integrity_check=ok | Owner (2026-10-24) | `docs/engineering/BACKUP_AUDIT.md` |
| G6 | 2026-10-24 | Voice containment formally approved | No consumers, port 8001 unpublished, voice excluded from Compose | Owner (2026-10-24) | `docker-compose.yml`, FCL-004 |

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
| **G1** | **APPROVED** | Canonical DB selected, backup done, Compose mount fixed | ✅ Done |
| **G2** | **APPROVED** | License evaluation done, Apache-2.0 LICENSE file added | ✅ Done |
| **G3** | **APPROVED** | ADR reviews documented, all six approved | ✅ Done |
| **G4** | **APPROVED** | Scope reconciled with completions, approved | ✅ Done |
| **G5** | **APPROVED** | Backup/restore drill passed, accepted | ✅ Done |
| **G6** | **APPROVED** | Voice removed from Compose, port 8001 unpublished, sign-off complete | ✅ Done |

---

## 8. Phase 2 Authorization

### Phase 2 Approval Gate

| Requirement | Description | Status | Evidence |
|---|---|---|---|
| **ADR-003** | PostgreSQL 17 as system of record; SQLite test-only | **APPROVED 2026-10-24** | Owner authorization per ARCHITECTURE_DECISIONS.md approval rule |
| **ADR-004** | SQLite-to-PostgreSQL migration and canonical-data choice | **APPROVED 2026-10-24** | Owner authorization; canonical DB `backend/data/app.db` (236 conv/577 msg) confirmed |
| **ADR-005** | SQLAlchemy 2 + Alembic + asyncpg | **APPROVED 2026-10-24** | Owner authorization; infrastructure complete per PHASE_02_IMPLEMENTATION_PLAN.md |
| **Canonical DB Confirmation** | `backend/data/app.db` is source of truth | **CONFIRMED 2026-10-24** | 236 conversations / 577 messages, SHA-256 verified |
| **Backup Current** | Updated backup of canonical DB | **REQUIRED** | New backup and restore drill before migration |
| **Phase 2 Scope** | Migration per ADR-003/004/005, PHASE_02_IMPLEMENTATION_PLAN.md | **APPROVED 2026-10-24** | Owner authorization for full Phase 2 execution |

**Owner Decision:** Phase 2 implementation **AUTHORIZED 2026-10-24**. All three ADRs (003, 004, 005) individually approved per governance rule. Proceed with migration implementation per PHASE_02_IMPLEMENTATION_PLAN.md.

---

## 9. Decision Log (Extended)

| Gate | Date | Decision | Rationale | Approver | Evidence Link |
|------|------|----------|-----------|----------|---------------|
| G1 | 2026-10-24 | Canonical DB `backend/data/app.db` approved | Larger dataset (234 conv/573 msg), active development DB; Compose mount fixed to use canonical | Owner (2026-10-24) | `docs/roadmaps/phase-00/CANONICAL_DB_DECISION.md`, `docker-compose.yml` |
| G2 | 2026-10-23 | Apache-2.0 selected and `LICENSE` added | Matches LICENSE_DECISION.md recommendation; permissive, compatible with all deps | Owner (2026-10-23) | `LICENSE`, `docs/engineering/LICENSE_DECISION.md` |
| G3 | 2026-10-24 | All six ADRs (001, 002, 009, 010, 013, 014) individually approved | ADR reviews documented with recommendations; all match implemented architecture | Owner (2026-10-24) | `docs/engineering/ADR_REVIEWS.md`, `docs/roadmaps/phase-00/ARCHITECTURE_DECISIONS.md` |
| G4 | 2026-10-24 | Phase 1 scope approved as documented | In-scope items match completed work; out-of-scope items properly deferred | Owner (2026-10-24) | `docs/roadmaps/phase-00/PHASE_01_IMPLEMENTATION_PLAN.md` |
| G5 | 2026-10-24 | Backup drill accepted | Drill evidence: checksums match, row counts match, integrity_check=ok | Owner (2026-10-24) | `docs/engineering/BACKUP_AUDIT.md` |
| G6 | 2026-10-24 | Voice containment formally approved | No consumers, port 8001 unpublished, voice excluded from Compose | Owner (2026-10-24) | `docker-compose.yml`, FCL-004 |
| **P2** | **2026-10-24** | **Phase 2 authorized: ADR-003, 004, 005 approved; migration execution approved** | ADR-003/004/005 settled per governance rule; canonical DB confirmed; infrastructure ready | **Owner (2026-10-24)** | `docs/roadmaps/phase-00/ARCHITECTURE_DECISIONS.md`, `docs/roadmaps/phase-00/PHASE_02_IMPLEMENTATION_PLAN.md` |
| **Blanket** | **2026-10-28** | **Owner granted blanket approval ("all permissions approved") via session directive** | Covers: ADR-008 review/approval and Phase 3 auth work; production PostgreSQL cutover (to be executed as a deliberate documented step with a fresh backup first); P1-17 model benchmark; P1-12 CI decision; container/infra remediations under FCL-019. Scope is limited to the items pending approval at grant time — not an open-ended grant | **Owner (2026-10-28, session directive)** | Session record 2026-10-28; FCL-019 |
| **Phase 3 gate** | **2026-10-29** | **Phase 3 authentication implemented per ADR-008 (P3-01..P3-15 complete; FCL-020..024)** | Opaque sessions (web cookie / Android bearer + refresh rotation), Argon2id, admin-created accounts, per-IP + per-account limits, trusted-proxy client IP, CSRF/Origin enforcement, audit events, auth matrix + async regression tests (113 passing). **Non-loopback exposure remains gated** on the security-engineer exit-gate review (P3 exit criterion) | Implemented under Owner blanket approval (2026-10-28) | FCL-020..024 |

---

## 10. Gate Resolution Summary (Extended)

| Gate | Status | Work Done | Owner Action Needed |
|------|--------|-----------|---------------------|
| **G1** | **APPROVED** | Canonical DB selected, backup done, Compose mount fixed | ✅ Done |
| **G2** | **APPROVED** | License evaluation done, Apache-2.0 LICENSE file added | ✅ Done |
| **G3** | **APPROVED** | ADR reviews documented, all six approved | ✅ Done |
| **G4** | **APPROVED** | Scope reconciled with completions, approved | ✅ Done |
| **G5** | **APPROVED** | Backup/restore drill passed, accepted | ✅ Done |
| **G6** | **APPROVED** | Voice removed from Compose, port 8001 unpublished, sign-off complete | ✅ Done |
| **P2** | **APPROVED** | ADR-003/004/005 approved; canonical DB confirmed; Phase 2 authorized | ✅ Done |
| **Blanket** | **APPROVED** | Owner blanket approval (2026-10-28) covering ADR-008/cutover/P1-17/P1-12 | ✅ Done (scope-limited; see Decision Log) |