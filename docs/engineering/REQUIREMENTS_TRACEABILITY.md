# MyFarmAI — Requirements Traceability Matrix

**Document ID:** MYFARMAI-RTM-001  
**Version:** 1.0  
**Date:** 2026-10-21  
**Status:** Draft — Owner Review Required  
**Source:** PRD.md, TRD.md, APP_FLOW.md, UI_UX_DESIGN_BRIEF.md, UI_UX_DESIGN_SYSTEM.md, BACKEND_SCHEMA.md, IMPLEMENTATION_PLAN.md, flows/*, Phase 0 audit documents

---

## 1. Purpose

This matrix establishes bidirectional traceability from **requirements** → **user flows** → **design** → **API contracts** → **data model** → **implementation tasks** → **tests** → **evidence**. It is the single reference for verifying that every approved requirement is implemented, tested, and documented.

---

## 2. Traceability Table

| Req ID | Requirement (PRD/TRD) | User Flow (APP_FLOW/flows/*) | Design (UI_UX) | API Contract (TRD §9) | Data Model (BACKEND_SCHEMA) | Impl Task (PHASE_01_IMPLEMENTATION_PLAN) | Test Reference | Evidence Status |
|--------|------------------------|------------------------------|----------------|------------------------|-------------------------------|------------------------------------------|----------------|-----------------|
| **FR-01** | API Foundation (PRD §6.1) | APP_FLOW §6 | — | TRD §9: `/health/live`, `/health/ready`, `/api/v1/health` | — | P1-06, P1-07, P1-08, P1-13 | test_health.py, contract tests | NOT TESTED |
| **FR-02** | Auth & Authorization (PRD §6.2) | AUTHENTICATION_FLOW §2–5 | UI_UX_DESIGN_BRIEF §148–149 | TRD §11.1 | BACKEND_SCHEMA §5.1 (users), §5.8 (audit_events) | Phase 3 (blocked) | auth matrix tests | BLOCKED (gate) |
| **FR-03** | Agricultural QA (PRD §6.3) | AGRICULTURAL_QA_FLOW §2–4 | UI_UX_DESIGN_BRIEF §132–136 | TRD §9.1: `POST /api/v1/ai/answer` | BACKEND_SCHEMA §5.2–5.3 (conversations, messages) | Phase 4 (blocked) | test_chat.py, e2e tests | BLOCKED (gate) |
| **FR-04** | AI Provider Management (PRD §6.4) | AGRICULTURAL_QA_FLOW §3 step 6 | — | TRD §7: AIProvider interface | BACKEND_SCHEMA §5.7 (model_providers) | Phase 4 (P1-17 benchmarks) | AI gateway contract tests | NOT TESTED |
| **FR-05** | Research Engine (PRD §6.5) | RESEARCH_FLOW §2–3 | UI_UX_DESIGN_BRIEF §138–143 | TRD §8, §9.2: `POST /api/v1/research` | BACKEND_SCHEMA §5.4–5.6 (research_jobs, sources) | Phase 6 (blocked) | research contract/SSRF tests | BLOCKED (gate) |
| **FR-06** | Source Citations (PRD §6.6) | RESEARCH_FLOW §3.9, §4 | UI_UX_DESIGN_SYSTEM §4.5 | TRD §9.2 response.sources[] | BACKEND_SCHEMA §5.5–5.6 | Phase 6 (blocked) | citation validation tests | BLOCKED (gate) |
| **FR-07** | Persistent Storage (PRD §6.7) | — | — | TRD §6 | BACKEND_SCHEMA §3–13 | P1-01 (backup), Phase 2 (migrations) | DB integrity, migration tests | BLOCKED (gate) |
| **FR-08** | Web Client (PRD §6.8) | APP_FLOW §3, §10 | UI_UX_DESIGN_SYSTEM §4, §8, §12 | — | — | Phase 6/7 (blocked) | web e2e, accessibility | BLOCKED (gate) |
| **FR-09** | Android Client (PRD §6.9) | APP_FLOW §10 | UI_UX_DESIGN_SYSTEM §12 (Android) | — | — | P1-18 (Android base URL fix) | Android contract tests | BLOCKED (gate) |
| **FR-10** | Operational Monitoring (PRD §6.10) | ERROR_RECOVERY_FLOW §7 | — | TRD §12: `/health/live`, `/health/ready` | — | P1-08 | health dependency tests | NOT TESTED |
| **FR-11** | Configuration (PRD §6.11) | APP_FLOW §5 | — | TRD §5.4 | — | P1-05 | config validation tests | NOT TESTED |
| **FR-12** | Documentation (PRD §6.12) | — | — | — | — | P1-13 | doc review | IN PROGRESS |

| NFR ID | Non-Functional (PRD §7) | Flow/Design Ref | Test Reference | Evidence Status |
|--------|------------------------|-----------------|----------------|-----------------|
| **NFR-01** | Security | SECURITY_AND_PRIVACY_AUDIT.md, TRD §11 | security regression tests | BLOCKED (gate) |
| **NFR-02** | Performance | TRD §15 | benchmark (P1-17) | NOT TESTED |
| **NFR-03** | Reliability | ERROR_RECOVERY_FLOW §2–6, TRD §12.2 | failure injection tests | NOT TESTED |
| **NFR-04** | Scalability | TRD §3.1 | load tests | NOT TESTED |
| **NFR-05** | Maintainability | IMPLEMENTATION_PLAN §2, ARCHITECTURE_DECISIONS.md | lint/type/format CI | NOT TESTED |
| **NFR-06** | Accessibility | UI_UX_DESIGN_SYSTEM §7, §12 | aXe, manual keyboard/screen reader | NOT TESTED |
| **NFR-07** | Privacy | PRIVACY_ASSESSMENT (SECURITY_AND_PRIVACY_AUDIT §4) | data retention/deletion tests | NOT TESTED |
| **NFR-08** | Cost Efficiency | INTEGRATION_AND_COST_AUDIT.md | cost monitoring | NOT TESTED |

---

## 3. Phase 1 Scope Traceability (P1-01 to P1-18)

| Task | Gaps Closed | Requirements Covered | Verification Method |
|------|-------------|----------------------|---------------------|
| P1-01 | GAP-001, 002, 003, 004 | FR-07, FR-11 | git bundle verify, restore clone, check-ignore, sqlite integrity, row counts |
| P1-02 | GAP-005, 027 | NFR-01 (S-04, S-16), FR-11 | secret scan, stat 600, container health |
| P1-03 | GAP-006 | NFR-01 (S-03, S-12, S-15) | docker port, ss, compose config, smoke test |
| P1-04 | GAP-012 | NFR-05, FR-11 | uv lock --check, uv sync --frozen, python --version |
| P1-05 | GAP-011, 019 | NFR-01 (S-09), FR-11 | config unit tests, startup failure tests |
| P1-06 | GAP-008, 019 | NFR-05, FR-01 | app-factory tests, route smoke tests, import review |
| P1-07 | GAP-017 | NFR-01 (S-10), FR-01 | contract tests, client unit tests, manual error matrix |
| P1-08 | GAP-018 | NFR-03, FR-10 | dependency-down tests, log parsing, redaction test |
| P1-09 | GAP-013, 014 | NFR-01 (S-07, S-08, S-18) | spoof test, memory-bound test, body-limit test |
| P1-10 | GAP-008 | NFR-05, FR-01 | pytest -q random order, before/after DB hash |
| P1-11 | GAP-012, 019 | NFR-05 | check.sh passes, inject failure |
| P1-12 | GAP-012 | NFR-05 | CI passes, scans run, SBOM |
| P1-13 | GAP-019 | NFR-05, FR-01 | regenerate/diff, docs review, fresh-setup |
| P1-14 | GAP-020 | NFR-01 (S-12), FR-11 | docker build/inspect, compose config, port scan |
| P1-15 | GAP-015 | NFR-08 | df -h, docker system df, build success |
| P1-16 | GAP-023 | NFR-07, FR-11 | legal sign-off, dependency inventory |
| P1-17 | GAP-021 | NFR-02, FR-04 | benchmark log, nvidia-smi, ollama ps |
| P1-18 | GAP-009 | FR-09, FR-01 | emulator/device smoke test, typecheck/lint |

---

## 4. Verification Evidence Mapping

| Evidence Type | Location | Linked Tasks | Status |
|---------------|----------|--------------|--------|
| Git bundle/remote | repo root / remote | P1-01 | NOT TESTED |
| Canonical DB decision | docs/engineering/DECISION_REGISTER.md | P1-01 | NOT TESTED |
| Backup/restore drill | /data/MyFarmAI-backups/ (not yet created) | P1-01 | NOT TESTED |
| Secret scan clean | CI / local | P1-02 | NOT TESTED |
| Voice containment | docker-compose.yml | P1-03 | NOT TESTED |
| uv.lock / pyproject.toml | backend/ | P1-04 | NOT TESTED |
| Config profiles | backend/app/core/config_profiles.py | P1-05 | NOT TESTED |
| App factory | backend/app/factory.py | P1-06 | NOT TESTED |
| Error envelope | backend/app/core/errors.py (new) | P1-07 | NOT TESTED |
| Health endpoints | backend/app/api/v1/health.py, factory.py | P1-08 | NOT TESTED |
| Request hardening | backend/app/middleware/ | P1-09 | NOT TESTED |
| Hermetic test suite | backend/tests/conftest.py | P1-10 | NOT TESTED |
| check.sh | scripts/check.sh | P1-11 | NOT TESTED |
| CI config | .github/workflows/ or .gitlab-ci.yml | P1-12 | NOT TESTED |
| OpenAPI artifact | docs/api/openapi.json | P1-13 | NOT TESTED |
| Container baseline | backend/Dockerfile, docker-compose.yml | P1-14 | NOT TESTED |
| Disk preflight | docs/engineering/BACKUP_AUDIT.md | P1-15 | NOT TESTED |
| LICENSE / notices | LICENSE, THIRD_PARTY_NOTICES.md | P1-16 | NOT TESTED |
| Benchmark report | docs/engineering/BENCHMARK_REPORT.md | P1-17 | NOT TESTED |
| Android base URL fix | android/src/lib/api/client.ts | P1-18 | NOT TESTED |

---

## 5. Open Traceability Gaps

1. **No API contract exists for `/api/v1/ai/answer`** — TRD §9.1 proposes it; current backend has `/api/v1/chat` (different schema)
2. **No API contract exists for research endpoints** — TRD §9.2 proposes `POST /api/v1/research` and `GET /api/v1/research/{id}`; not implemented
3. **Android client uses relative URLs** — API-C-04, GAP-009; blocks all Android integration testing
4. **No auth/ownership model implemented** — FR-02, ADR-008; required before any non-loopback deployment
5. **PostgreSQL migration path defined but not approved** — ADR-003, ADR-004, ADR-005; blocked on canonical DB decision
6. **SearXNG secret hardcoded** — GAP-005, INT-F03; secret rotation required before Phase 1
7. **Open-Meteo non-commercial only** — INT-F01, GAP-010; commercial decision required before Phase 5

---

## 6. Maintenance

- Update this matrix when: requirements change, tasks are added/removed, tests pass/fail, gates are approved
- Review at each Phase gate
- Keep synchronized with PHASE_01_IMPLEMENTATION_PLAN.md, GAP_ANALYSIS.md, and DECISION_REGISTER.md