# MyFarmAI — Phase 1 Scope Reconciliation

**Document ID:** MYFARMAI-P1SCOPE-001  
**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Proposed — Owner Decision Required  
**Gate:** G4 (Blocks Phase 1 start)  
**Sources:** PRD.md, TRD.md, APP_FLOW.md, UI_UX docs, BACKEND_SCHEMA.md, IMPLEMENTATION_PLAN.md, flows/*, PHASE_01_IMPLEMENTATION_PLAN.md, Phase 0 audits

---

## 1. Purpose

Reconcile the Phase 1 scope in `PHASE_01_IMPLEMENTATION_PLAN.md` against:
- Product Requirements (PRD FR-01 to FR-12, NFR-01 to NFR-08)
- Technical Requirements (TRD)
- Application flows and UI/UX specifications
- Existing implementation baseline
- Phase 0 audit findings (GAP_ANALYSIS.md, SECURITY_AND_PRIVACY_AUDIT.md)

Produce an explicit, owner-approved scope record with in-scope/out-of-scope functionality, acceptance criteria, and known limitations.

---

## 2. Phase 1 Goal (Per PHASE_01_IMPLEMENTATION_PLAN.md §1)

> **Establish a reproducible, testable, safely operable FastAPI foundation without changing the product's API surface beyond the approved error contract and health endpoints.**

**Exit Gate:** Clean environment setup works; tests, linting, type checks, health endpoints, and local quality script pass; backend runs non-root and is not publicly exposed.

---

## 3. Requirements Mapping to Phase 1

### Functional Requirements (PRD §6)

| Req ID | Requirement | Phase 1 Coverage | Notes |
|--------|-------------|------------------|-------|
| **FR-01** | API Foundation | **FULL** | P1-06, P1-07, P1-08, P1-13 |
| **FR-02** | Auth & Authorization | **NONE** | Explicitly Phase 3 (out of scope) |
| **FR-03** | Agricultural QA | **PARTIAL** | Backend chat API exists; AI gateway deferred to Phase 4 |
| **FR-04** | AI Provider Management | **PARTIAL** | Ollama client exists; gateway abstraction deferred to Phase 4; P1-17 benchmarks |
| **FR-05** | Research Engine | **NONE** | Explicitly Phase 6 |
| **FR-06** | Source Citations | **NONE** | Explicitly Phase 6 |
| **FR-07** | Persistent Storage | **PARTIAL** | SQLite backup/restore (P1-01); migrations deferred to Phase 2 |
| **FR-08** | Web Client | **NONE** | Phase 6/7; web exists but not integrated to new error envelope |
| **FR-09** | Android Client | **PARTIAL** | P1-18 fixes base URL; full integration Phase 6/7 |
| **FR-10** | Operational Monitoring | **FULL** | P1-08 health endpoints, structured logging |
| **FR-11** | Configuration | **FULL** | P1-05 config profiles, safe defaults |
| **FR-12** | Documentation | **PARTIAL** | P1-13 OpenAPI + docs correction |

### Non-Functional Requirements (PRD §7)

| NFR ID | Requirement | Phase 1 Coverage | Notes |
|--------|-------------|------------------|-------|
| **NFR-01** | Security | **PARTIAL** | P1-02, P1-03, P1-05, P1-09, P1-14 address S-03, S-04, S-07, S-08, S-09, S-12, S-13, S-16; auth (S-01, S-02) deferred to Phase 3 |
| **NFR-02** | Performance | **PARTIAL** | P1-17 optional benchmark; P1-09 concurrency limits |
| **NFR-03** | Reliability | **PARTIAL** | P1-08 health checks; P1-09 bounded retries; full error recovery Phase 2+ |
| **NFR-04** | Scalability | **NONE** | Not measured; Phase 1 is single-process |
| **NFR-05** | Maintainability | **FULL** | P1-04 (uv/lockfile), P1-06 (app factory), P1-10 (hermetic tests), P1-11 (check.sh), P1-12 (CI) |
| **NFR-06** | Accessibility | **NONE** | Web/Android UI work deferred |
| **NFR-07** | Privacy | **PARTIAL** | P1-01 backup policy; P1-16 license; retention/deletion Phase 2/3 |
| **NFR-08** | Cost Efficiency | **PARTIAL** | P1-15 disk preflight; no paid services introduced |

---

## 4. Reconciled In-Scope Items (Per PHASE_01_IMPLEMENTATION_PLAN.md §1.1)

| # | Item | Tasks | Verification |
|---|------|-------|--------------|
| 1 | Repository and data safety | P1-01 | Git bundle, canonical DB decision, backup drill |
| 2 | Secret remediation | P1-02 | SearXNG secret rotated, file perms 600, secret scan |
| 3 | Voice exposure containment | P1-03 | Port 8001 unpublished, voice excluded from default Compose |
| 4 | Python 3.12 + uv + lockfile | P1-04 | uv.lock committed, 3.12 runtime, dev/runtime split |
| 5 | App factory, config profiles, module boundaries | P1-05, P1-06 | Factory pattern, profile configs, import boundaries |
| 6 | Consistent error envelope + request correlation | P1-07 | Flat envelope, X-Request-ID, contract tests |
| 7 | Health endpoints (live/ready) | P1-08 | /health/live, /health/ready, legacy /health |
| 8 | Structured logs with redaction | P1-08 | JSON logs, no secrets/prompts, request IDs |
| 9 | Request body limits, trusted proxy, bounded rate limiting | P1-09 | 413 on oversize, proxy trust config, LRU/TTL limiter |
| 10 | Hermetic tests + single check entrypoint | P1-10, P1-11 | 56/56 on clean DB, random order, check.sh |
| 11 | OpenAPI artifact + docs correction | P1-13 | openapi.json matches app, stale docs fixed |
| 12 | Non-root container + Compose validation | P1-14 | Non-root UID, healthcheck, internal network |
| 13 | Backup/restore drill | P1-01 | SQLite backup + restore verification |
| 14 | License/third-party notices | P1-16 | LICENSE file, THIRD_PARTY_NOTICES.md |
| 15 | Disk/build preflight | P1-15 | Headroom threshold, successful build |
| 16 | Optional model benchmark | P1-17 | Benchmark report for Phase 4 gate |

---

## 5. Reconciled Out-of-Scope Items (Per PHASE_01_IMPLEMENTATION_PLAN.md §1.2)

| Excluded | Reason | Target Phase |
|----------|--------|--------------|
| Authentication, sessions, ownership | Requires DB schema changes, user model | Phase 3 |
| PostgreSQL deployment + migration | ADR-003/004/005 not yet approved | Phase 2 |
| Farm/crop domain APIs | New domain models beyond Phase 1 scope | Phase 5 |
| AI gateway refactor, prompt eval, streaming | Architecture change beyond foundation | Phase 4 |
| Research pipeline, SearXNG client, citations | New feature area | Phase 6 |
| Weather provider replacement | Legal/commercial decision required | Phase 5 |
| Voice feature work, model pre-baking | ADR-014 defers voice | Deferred |
| Public TLS, production hardening, backup automation | Requires Phase 1 foundation first | Phase 8 |
| Deleting models/images/volumes/databases | Destructive; separate approval | As needed |
| Pulling new models, GPU packages | Resource impact; separate approval | As needed |

---

## 6. Scope Conflicts & Resolutions

| Conflict | Source A | Source B | Resolution |
|----------|----------|----------|------------|
| **Chat endpoint mismatch** | TRD §9.1 proposes `POST /api/v1/ai/answer` | Current impl has `POST /api/v1/chat` | **Keep `/api/v1/chat`** for Phase 1; document as current contract; rename in Phase 4 if needed |
| **Error envelope** | ADR-009 mandates flat envelope | Current handlers return nested | **Implement flat envelope** (P1-07) — breaking change coordinated with clients |
| **Health endpoints** | ADR-009: `/health/live` + `/health/ready` | Current: `/health` + `/api/v1/health` | **Add live/ready, retain legacy** (P1-08) |
| **Android base URL** | TRD §10.2: absolute URL required | Current: relative `fetch(endpoint)` broken | **Fix in P1-18** — critical for Android integration |
| **Voice service** | ADR-014: defer from MVP | Currently running on 0.0.0.0:8001 | **Contain in P1-03** — stop publishing, exclude from default Compose |
| **Weather licensing** | INTEGRATION_AUDIT: Open-Meteo non-commercial | Currently used without cache/attribution | **Keep for prototype only** (P1-08 docs); commercial decision Phase 5 |

---

## 7. Acceptance Criteria (Per PHASE_01_IMPLEMENTATION_PLAN.md §5)

### Environment & Reproducibility
- [ ] Clean checkout + Python 3.12 + `uv sync --frozen` succeeds
- [ ] `scripts/check.sh` passes: format, lint, type check, tests, OpenAPI diff, Compose config, secret scan

### Tests
- [ ] Test suite 56/56 on clean DB; dev DB untouched; random order passes

### Health & API
- [ ] `/health/live` and `/health/ready` behave correctly with deps up/down; legacy `/health` retained
- [ ] Error envelope consistent; web and Android parse it; request IDs correlate

### Security & Hardening
- [ ] Body limits, trusted-proxy handling, bounded rate limiting tested
- [ ] Container non-root, healthcheck, no backend/DB/search/voice port published

### Documentation & Compliance
- [ ] Secret scan clean; no DB tracked; backup/restore drill evidence exists
- [ ] OpenAPI artifact matches app; stale docs corrected; version single-source
- [ ] License decision/third-party notices recorded

### Governance
- [ ] No non-loopback exposure, no production deploy, no data migration, no destructive cleanup without separate approval
- [ ] Phase 0 decisions that remain open recorded with owners and dates

---

## 7. Known Limitations (Explicitly Disclosed)

1. **No authentication** — All endpoints remain public; backend binds to `127.0.0.1` only
2. **No ownership model** — Conversation IDs act as bearer tokens; no user/farm scoping
3. **SQLite only** — PostgreSQL migration deferred to Phase 2 (requires G1 + ADR-003/004/005)
4. **No research/citations** — SearXNG not integrated; research endpoints don't exist
5. **Voice contained** — No voice feature available in Phase 1
6. **Android base URL fix required** — P1-18 must complete before Android integration testing
7. **Weather non-commercial** — Open-Meteo used without commercial license; prototype only
7. **No CI platform yet** — Prereq 9 must be resolved for P1-12

---

## 8. Scope Approval

| Field | Value |
|-------|-------|
| **Scope Approved** | ☐ Yes / ☐ No / ☐ With Modifications |
| **Modifications** | |
| **Approver** | |
| **Date** | |
| **Signature** | |

---

## 9. Next Steps After Approval

1. Update `DECISION_REGISTER.md` Gate G4 → APPROVED
2. Record any modifications to in-scope/out-of-scope lists
3. Proceed to gate resolution for G1, G2, G3, G5, G6
4. Begin Phase 1 Wave 0 investigation tasks (parallel)