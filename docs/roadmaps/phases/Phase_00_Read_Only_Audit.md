# Phase 0 — Read-Only Audit and Architecture Approval

**Reported status:** Complete according to the Phase 0 handoff.  
**Implementation status:** Phase 1 has not started; explicit approval is still required.  
**Purpose:** Establish repository facts and a safe, evidence-based implementation plan.

## Scope

- Verify repository, branch, commit, working tree, roadmap, backend, clients, infrastructure and docs.
- Inventory API endpoints, dependencies, integrations, databases, tests and deployment configuration.
- Audit paid-service exposure, licence constraints, security/privacy risks, resource constraints and documentation drift.
- Propose target architecture, ADRs, gap analysis and Phase 1 tasks.
- Preserve all pre-existing uncommitted and untracked work.

## Reported repository baseline

- Repository: `/data/MyFarmAI`
- Branch/commit: `main` / `3cd1a6e60e0ad7d54888d632d4ea30820a37b60f`
- No remote configured.
- Substantial pre-existing uncommitted/untracked work; preserve unchanged.
- Thirteen Phase 0 documents reportedly created in `docs/roadmaps/phase-00/`.

These are facts from the supplied Phase 0 handoff and should be re-verified before any future operation. This roadmap file does not independently inspect the repository.

## Critical reported findings

1. Clean-database test run: 49 passed, 7 failed in `test_chat.py`; prior 56/56 depended on a pre-existing development database.
2. Two divergent SQLite databases: `backend/data/app.db` reportedly has 122 conversations / 315 messages; `data/app.db` reportedly has 35 / 74. Both pass SQLite integrity checks; canonical source is undecided.
3. `backend/data/app.db` is reportedly untracked and not ignored, creating accidental-commit risk.
4. Authentication, authorization and ownership checks are reportedly absent; conversation IDs act as bearer secrets.
5. Voice service is reportedly unauthenticated, has unbounded upload, runs as root, and is published on `0.0.0.0:8001`.
6. A hardcoded SearXNG secret reportedly exists in `infra/searxng/config/settings.yml`.
7. No verified database backup/restore procedure exists.
8. Android API calls reportedly use relative URLs and do not use `getApiBaseUrl()`.
9. Rate limiting is reportedly bypassable through spoofed `X-Forwarded-For` and uses an unbounded in-memory map.
10. Dependency/image pinning, lockfile, CI and scanning are reportedly incomplete.
11. Host is reportedly constrained: 7 GiB RAM, about 1.9–2.3 GiB available, 2 GiB VRAM, and about 5 GB free on `/`; Docker data resides on `/`.
12. Open-Meteo's free offering is reportedly non-commercial; commercial usage requires a terms/licensing decision.
13. SearXNG is AGPL-3.0; project distribution/modification posture needs legal review.

Treat these as reported findings until the underlying audit documents are checked.

## Required outputs

The repository handoff says these exist under `docs/roadmaps/phase-00/`:
- README and current-state audit.
- Dependency and integration/cost inventories.
- API contract inventory.
- Database assessment.
- Security/privacy audit.
- Hardware/deployment assessment.
- Target architecture and 15 proposed ADRs.
- Gap analysis and Phase 1 plan.
- Verification report.

## Approval decisions

Resolve before implementation:
- Preservation/branching strategy for existing work.
- Canonical SQLite database and data-preservation requirements.
- Deployment target and network exposure.
- Commercially suitable weather/public data source.
- Python/runtime and lockfile policy.
- PostgreSQL production and SQLite test strategy.
- Voice deferral or containment strategy.
- Local model selection based on benchmark.
- Project licence and AGPL-3.0 implications.
- Whether optional Valkey, workers, Qdrant and observability are justified.

## Exit gate

- [ ] Repository evidence and audit documents reviewed.
- [ ] Existing uncommitted work and databases preserved.
- [ ] Seven clean-DB test failures acknowledged and assigned.
- [ ] Immediate security risks have approved containment/remediation plans.
- [ ] Approval decisions are recorded.
- [ ] Phase 1 scope is explicitly approved.

**Do not implement Phase 1 automatically.**
