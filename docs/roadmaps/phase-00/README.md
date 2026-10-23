# Phase 0 — Read-Only Audit and Architecture Approval

**Project:** MyFarmAI  
**Repository:** `/data/MyFarmAI`  
**Branch / commit:** `main` / `3cd1a6e60e0ad7d54888d632d4ea30820a37b60f`  
**Audit date:** 2026-10-21  
**Status:** Audit and documentation complete. **Phase 1 has not started and requires explicit approval.**
**Roadmap:** [`../MyFarmAI_Backend_Roadmap.md`](../MyFarmAI_Backend_Roadmap.md)

---

## 1. Purpose and scope

This directory records the Phase 0 read-only audit required by the backend roadmap. It establishes the actual state of the repository before any implementation, dependency, database, or deployment change.

**In scope:** repository inspection, backend/API/database/security review, dependency and integration inventory, hardware assessment, target architecture, ADRs, gap analysis, and a proposed Phase 1 plan.

**Out of scope (not performed):** production code, package installation or upgrades, database migrations, schema changes, configuration changes, service starts/stops, Docker builds, paid API calls, and Phase 1+ implementation.

## 2. Evidence conventions

Every significant finding is labelled:

| Label | Meaning |
|---|---|
| **Verified** | Directly established by inspected repository evidence or a read-only command. |
| **Inferred** | Strongly suggested by evidence but not conclusively proven. |
| **Unknown** | Evidence is missing, access was blocked, or a decision is still open. |
| **Risk** | A verified or plausible issue requiring attention. |

External claims include a source URL and access date. No credential values are reproduced in this directory.

## 3. Repository state at audit time

- The repository is a Git work tree with **one commit** (`3cd1a6e`), **no configured remote**, and a large amount of uncommitted/untracked work.
- `backend/app/main.py`, `backend/requirements.txt`, `docker-compose.yml`, and `.gitignore` had pre-existing modifications.
- The entire backend feature set beyond the initial skeleton (API, services, schemas, database code, tests) is currently untracked.
- Two SQLite databases exist with different row counts: `backend/data/app.db` (122 conversations / 315 messages) and `data/app.db` (35 / 74). Both pass SQLite `integrity_check`.
- The backend is a FastAPI application using SQLite/`aiosqlite`, local Ollama (`qwen3:4b`), and Open-Meteo. There is no authentication, no migration tool, no CI, and no backup procedure.
- The web client is Next.js 15. The Android client is Expo/React Native 51. The Android API client currently builds relative URLs and does not use its configured base URL, so it cannot reach the backend as written.
- A self-hosted SearXNG container is running on `127.0.0.1:8890`, but no backend code calls it. Its configuration contains a hardcoded server secret.
- Host resources are constrained: 7.0 GiB RAM (≈2.3 GiB available during the audit), 2 GiB MX250 VRAM, 5.3 GiB free on `/`, and 176 GiB free on `/data`. Docker data lives on `/`, not `/data`.

## 4. Top findings

| # | Finding | Severity / priority | Evidence |
|---|---|---|---|
| 1 | No authentication or authorization; conversations have no owner | High (Critical if public) | `SECURITY_AND_PRIVACY_AUDIT.md` S-01, S-02 |
| 2 | Voice transcription endpoint is unauthenticated, unbounded, runs as root, and is published on `0.0.0.0:8001` | High | S-03, `HARDWARE_AND_DEPLOYMENT_ASSESSMENT.md` |
| 3 | Hardcoded SearXNG secret in `infra/searxng/config/settings.yml` | High | S-04 |
| 4 | Conversation database is untracked and not ignored, creating a commit/privacy risk | High | S-05 |
| 5 | No backup or restore procedure; two divergent SQLite databases | High | S-06, `DATABASE_ASSESSMENT.md` |
| 6 | 7 chat tests fail against a clean database; the documented 56/56 result depends on a pre-existing dev DB | High (quality gate) | `VERIFICATION_REPORT.md` §3.1 |
| 7 | Open-Meteo free tier is non-commercial only; commercial use requires a paid licence | High (product/legal) | `INTEGRATION_AND_COST_AUDIT.md` INT-01 |
| 8 | Android API client uses relative URLs; configured base URL is unused | High (client blocker) | `API_CONTRACT_INVENTORY.md` API-C-04 |
| 9 | Dependencies are unpinned; Docker images are floating; no lockfile or CI | Medium | `DEPENDENCY_INVENTORY.md` |
| 10 | Rate limiting trusts `X-Forwarded-For` and grows an unbounded in-memory map | Medium | S-07 |

## 5. Document index

| Document | Contents |
|---|---|
| [`CURRENT_STATE_AUDIT.md`](CURRENT_STATE_AUDIT.md) | Verified current architecture, entry points, integrations, and documentation drift |
| [`DEPENDENCY_INVENTORY.md`](DEPENDENCY_INVENTORY.md) | Declared/installed versions, licences, maintenance and network characteristics |
| [`INTEGRATION_AND_COST_AUDIT.md`](INTEGRATION_AND_COST_AUDIT.md) | External services, credentials, data exposure, and paid-dependency risks |
| [`API_CONTRACT_INVENTORY.md`](API_CONTRACT_INVENTORY.md) | Every existing route, schema, consumer, error case, and contract risk |
| [`DATABASE_ASSESSMENT.md`](DATABASE_ASSESSMENT.md) | SQLite files, schema, counts, constraints, migration and backup risks |
| [`SECURITY_AND_PRIVACY_AUDIT.md`](SECURITY_AND_PRIVACY_AUDIT.md) | OWASP API Top 10 review, prioritised findings, remediation |
| [`HARDWARE_AND_DEPLOYMENT_ASSESSMENT.md`](HARDWARE_AND_DEPLOYMENT_ASSESSMENT.md) | Verified host limits, resource estimates, storage and deployment risks |
| [`TARGET_BACKEND_ARCHITECTURE.md`](TARGET_BACKEND_ARCHITECTURE.md) | Proposed modular-monolith architecture, flows, boundaries, alternatives |
| [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md) | Proposed ADRs, including the SQLite-to-PostgreSQL decision record |
| [`GAP_ANALYSIS.md`](GAP_ANALYSIS.md) | Prioritised gap register with verification methods |
| [`PHASE_01_IMPLEMENTATION_PLAN.md`](PHASE_01_IMPLEMENTATION_PLAN.md) | Proposed Phase 1 tasks and acceptance criteria — **not executed** |
| [`VERIFICATION_REPORT.md`](VERIFICATION_REPORT.md) | Commands run, files inspected, check results, limitations, final status |

## 6. Decisions required before Phase 1

1. **Repository safety:** approve committing the current work, adding ignore rules for databases/caches, and configuring a remote or backup.
2. **Canonical database:** decide whether `backend/data/app.db` or `data/app.db` is authoritative, and whether either contains data that must be preserved.
3. **Deployment target:** local-only, private LAN, single VPS, or public internet. This determines whether authentication is a Phase 1 prerequisite.
4. **Weather provider:** accept Open-Meteo for non-commercial prototyping only, or fund/replace it before commercial use.
5. **Python/runtime policy:** standardise on Python 3.12 with `uv` + lockfile (recommended) or keep the current unpinned `requirements.txt`.
6. **Database strategy:** PostgreSQL for production, SQLite for tests only (recommended), plus the migration approach in `ARCHITECTURE_DECISIONS.md` ADR-004.
7. **Voice service:** secure it (auth, size/type limits, non-root, internal-only) or remove it from the MVP until needed.
8. **AI model:** benchmark `qwen3:4b` against the 2 GiB VRAM / 7 GiB RAM budget; approve a smaller/alternative model if it cannot meet latency and memory targets.
9. **Licence:** choose the project licence and review AGPL-3.0 obligations for SearXNG before distribution.
10. **Optional services:** defer Valkey/Qdrant/extra observability until measured need (recommended).

## 7. What was not done

- No source code, configuration, dependency, lockfile, database, volume, or deployment state was changed.
- No packages were installed or upgraded; no images were built; no containers were started or stopped.
- No database migration, schema change, backup, or restore was executed.
- No paid API, account, or external service was called. Open-Meteo terms were read from its public website only; no API request was made.
- No dynamic security testing, exploitation, or third-party scanning was performed.

## 8. Approval gate

Phase 0 is an audit, not an implementation authorisation. Phase 1 may begin only after the decisions in §6 and the scope in `PHASE_01_IMPLEMENTATION_PLAN.md` are explicitly approved.

**Next action:** review this directory and return an approval decision (approve, approve with changes, or reject).
