# MyFarmAI — Individual ADR Review Records

**Document ID:** MYFARMAI-ADR-REV-001  
**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Proposed — Owner/Engineering Review Required  
**Gate:** G3 (Blocks Phase 1 start, P1-07, P1-10, P1-18)  
**Source:** `docs/roadmaps/phase-00/ARCHITECTURE_DECISIONS.md`

---

## 1. Purpose

This document records individual review decisions for the six ADRs that **must be approved before Phase 1 starts** per `ARCHITECTURE_DECISIONS.md` §2 Approval Rule:

> Phase 1 may start only after ADR-001, ADR-002, ADR-009, ADR-010, ADR-013, ADR-014, and the Phase 1 scope are approved.

Each ADR review includes: problem context, alternatives considered, recommendation, security/data implications, dependencies, and approval decision.

---

## 2. ADR-001 — Modular Monolith on FastAPI

### Source
`ARCHITECTURE_DECISIONS.md` lines 34-49

### Problem & Context
- Current backend is a single FastAPI process with routers, services, raw SQL
- Host constraints: 7 GiB RAM, 2 GiB VRAM, limited disk
- Roadmap prefers modular monolith, forbids unmeasured service splits

### Decision
Keep one deployable FastAPI backend. Organize into domain modules with one-way dependencies (`api → modules → integrations/db`). Split only when measured isolation/scaling/security requirement cannot be met inside monolith, via new ADR.

### Alternatives Considered
| Alternative | Assessment |
|-------------|------------|
| Microservices | Rejected: operational + RAM cost too high for 7 GiB host |
| Serverless | Rejected: local AI, long requests, persistent DB, self-hosting requirement |
| Separate AI service | Deferred until isolation is measured |

### Consequences
- **Positive:** One runtime, one deployment, simple local dev, low memory, shared transactions, easy refactoring
- **Negative:** Single failure domain; module boundaries must be enforced by review/import rules
- **Neutral:** Can run multiple workers later, but shared state (rate limits, sessions) must move out first

### Security & Data Implications
- Single process = single attack surface (easier to harden)
- Shared transactions = atomicity for multi-table operations
- No network serialization between modules = lower latency, fewer failure modes

### Verification Criteria
- No cross-module imports of ORM models
- Routers contain no SQL
- One Compose service for backend
- Module ownership documented

### Recommendation
**APPROVE** — Matches current architecture, addresses host constraints, provides clear evolution path.

### Review Record
| Field | Value |
|-------|-------|
| **Reviewer** | |
| **Date** | |
| **Decision** | ☐ Approve / ☐ Approve with Changes / ☐ Reject |
| **Comments** | |
| **Conflicts Resolved** | |

---

## 3. ADR-002 — Python 3.12 + `uv` Lockfile

### Source
`ARCHITECTURE_DECISIONS.md` lines 53-69

### Problem & Context
- Local virtualenv: Python 3.14.4
- Container/mypy target: Python 3.12
- Dependencies unpinned; `requirements.txt` has duplicates + test tooling in production
- Reproducibility + supply-chain risk (DEP-01, DEP-02, DEP-03)

### Decision
Target **Python 3.12** for dev, CI, runtime. Use `pyproject.toml` with runtime/dev dependency groups and committed `uv.lock`. Use `uv sync --frozen` in CI and `uv sync --frozen --no-dev` in runtime image. Keep `requirements.txt` only as temporary shim.

### Alternatives Considered
| Alternative | Assessment |
|-------------|------------|
| Keep unpinned pip | Rejected: non-reproducible, supply-chain risk |
| Pin 3.14 | Rejected: container/mypy mismatch, broader ecosystem risk |
| Poetry | Viable but `uv` faster and aligned with roadmap |

### Consequences
- **Positive:** One interpreter version; reproducible installs; smaller runtime image; faster installs
- **Negative:** Existing 3.14 venv must be recreated; contributors need `uv`; lockfile updates become reviewable
- **Risk:** 3.12-only pin may lag newer library features (acceptable for stability)

### Security & Data Implications
- Lockfile enables dependency scanning (pip-audit, OSV-Scanner) in CI
- Reproducible builds prevent supply-chain attacks
- Dev/runtime separation reduces attack surface in production images

### Verification Criteria
- `uv lock --check` passes
- `uv sync --frozen` works on clean checkout with Python 3.12
- `python --version` = 3.12.x in CI and image
- No duplicate dependencies

### Recommendation
**APPROVE** — Critical for reproducibility, supply-chain security, and Phase 1 P1-04. Already partially implemented (uv.lock exists).

### Review Record
| Field | Value |
|-------|-------|
| **Reviewer** | |
| **Date** | |
| **Decision** | ☐ Approve / ☐ Approve with Changes / ☐ Reject |
| **Comments** | |
| **Conflicts Resolved** | |

---

## 4. ADR-009 — Flat Error Envelope & Request Correlation

### Source
`ARCHITECTURE_DECISIONS.md` lines 210-249

### Problem & Context
- Current handlers raise `HTTPException(detail={...})` producing nested `{"detail":{"detail":...,"error_code":...}}`
- Schemas/docs describe flat object
- Web handles both; Android displays `[object Object]`
- Request IDs generated for logs but not standardized in responses

### Decision
Return one flat JSON envelope for all application errors:
```json
{
  "detail": "Conversation not found.",
  "error_code": "CONVERSATION_NOT_FOUND",
  "request_id": "3f0c...",
  "errors": [{"field": "message", "message": "Must not be blank."}]
}
```
`errors` optional for validation. HTTP status conveys class; `error_code` stable. Map 422 into same envelope. Return `X-Request-ID` on every response; accept inbound ID if 8-128 safe chars, else generate. Never return stack traces, upstream bodies, SQL, or secrets.

### Status Code Mapping
| Status | Use |
|--------|-----|
| 400 | Malformed request (not schema validation) |
| 401 | Missing/invalid authentication |
| 403 | Authenticated but not allowed |
| 404 | Missing object or unauthorized access |
| 409 | Conflict (duplicate, state transition) |
| 422 | Request schema validation |
| 429 | Rate limit/concurrency limit; include `Retry-After` |
| 503 | Dependency unavailable/overloaded |
| 504 | Upstream timeout |

### Consequences
- **Positive:** One client parser; stable codes; easier support; request correlation
- **Negative:** Breaking change for consumers expecting nested shape; web/Android must update together
- **Neutral:** FastAPI default validation handler must be overridden

### Security & Data Implications
- Prevents stack trace leakage (S-10)
- Request correlation enables audit trails without exposing secrets
- Standardized error codes enable client-side retry logic

### Verification Criteria
- Contract tests for every code/status
- Web and Android parse same shape
- Request ID present and unique
- No stack traces in responses

### Recommendation
**APPROVE WITH CHANGES** — Coordinate with web/Android owners (Prereq 11). Required for P1-07.

**Required Coordination:**
- Web client: Update error parsing in `web/src/lib/api/client.ts` (already handles both)
- Android client: Fix error parsing in `android/src/lib/api/client.ts` (currently broken)
- Both must deploy simultaneously with backend

### Review Record
| Field | Value |
|-------|-------|
| **Reviewer** | |
| **Date** | |
| **Decision** | ☐ Approve / ☐ Approve with Changes / ☐ Reject |
| **Comments** | |
| **Conflicts Resolved** | |

---

## 5. ADR-010 — Single-Host Compose + Caddy + Internal Networks

### Source
`ARCHITECTURE_DECISIONS.md` lines 252-276

### Problem & Context
- Current Compose: `network_mode: host`, voice on `0.0.0.0:8001`, root containers, no healthchecks/limits, floating images
- Backend not running; host `/` has 5.3 GB free; Docker data on `/`

### Decision
Deploy first production-capable version as single-host Compose stack:

| Component | Configuration |
|-----------|---------------|
| **Caddy** | Only public service (80/443); TLS termination; body/header/timeouts; coarse rate limits |
| **Backend** | Non-root; internal network; no published port; reaches Postgres, Ollama, SearXNG, voice via private addresses |
| **PostgreSQL** | No published port; data/backups on `/data` |
| **Ollama** | Host process on loopback; controlled host gateway; no 11434 exposure |
| **SearXNG** | Internal only; not published |
| **Voice** | Internal only; not published (or removed per ADR-014) |

Hardening: Pin image digests; health checks; `restart: unless-stopped`; `cap_drop: [ALL]`; `no-new-privileges`; read-only root fs where practical; resource limits after measurement.

### Alternatives Considered
| Alternative | Assessment |
|-------------|------------|
| Host networking | Rejected: exposure; no isolation |
| Kubernetes | Too heavy for single-host |
| Cloud load balancer | Unnecessary/paid |
| Nginx | Viable; Caddy has simpler TLS automation |

### Consequences
- **Positive:** Isolation, TLS, reproducible deployment, no accidental LAN exposure
- **Negative:** More config than host networking; Ollama host-gateway needs care; Caddy critical service
- **Risk:** Building images may fail until `/` space freed or Docker root moves to `/data` (HW-02)

### Security & Data Implications
- **Addresses S-03:** Voice not published on 0.0.0.0
- **Addresses S-09:** CORS/TrustedHost/TLS enforced at Caddy
- **Addresses S-12:** Non-root, read-only fs, capabilities dropped, resource limits
- **Data:** PostgreSQL on `/data` with backups; no DB exposure

### Verification Criteria
- `docker compose config` validates
- Only 80/443 published
- Backend/DB/search/voice not reachable from LAN
- Containers non-root; health checks pass
- TLS cert valid; secrets absent from images/Git

### Recommendation
**APPROVE** — Addresses multiple High/Medium security findings, enables production-ready deployment. Required for P1-14.

### Review Record
| Field | Value |
|-------|-------|
| **Reviewer** | |
| **Date** | |
| **Decision** | ☐ Approve / ☐ Approve with Changes / ☐ Reject |
| **Comments** | |
| **Conflicts Resolved** | |

---

## 6. ADR-013 — Hermetic Tests, Disposable PostgreSQL, CI Gates

### Source
`ARCHITECTURE_DECISIONS.md` lines 330-354

### Problem & Context
- Test suite: 49 pass / 7 fail on clean DB (chat tests use global settings, no schema init)
- No CI, no OpenAPI artifact, test tooling ships in runtime image

### Decision
- Introduce app factory (`create_app(settings)`) + dependency injection; no import-time global settings in tests
- Unit tests: per-test temp SQLite DB, same logical schema via Alembic (or metadata path with migration-parity test); enable `PRAGMA foreign_keys=ON`
- Integration tests: disposable PostgreSQL (Compose in CI), run `alembic upgrade head`
- Contract tests: error envelope, OpenAPI snapshot, auth matrix, health semantics
- Security regression tests: cross-user access, rate limits, body limits, SSRF/prompt injection (later)
- `scripts/check.sh` = single local/CI entrypoint: format, lint, type check, tests, OpenAPI diff, Compose validation, secret scan, dependency audit
- CI platform chosen when remote configured; script works locally first

### Consequences
- **Positive:** Trustworthy test signal; no dev-data writes; reproducible CI; reviewable API changes
- **Negative:** Slower integration tests; Docker/Postgres required for full suite
- **Risk:** SQLite/PostgreSQL schema drift; mitigated by migration-parity test

### Security & Data Implications
- Fixes test isolation (GAP-008): tests never touch `backend/data/app.db` or `data/app.db`
- Security regression tests prevent auth/authorization regressions
- Secret scanning in CI prevents credential leakage
- Dependency auditing catches supply-chain vulnerabilities

### Verification Criteria
- Clean checkout + `scripts/check.sh` passes
- Tests never touch dev DBs
- CI runs same script
- OpenAPI diff fails on unintended changes

### Recommendation
**APPROVE** — Critical for fixing 49/56 test failure, enabling CI, establishing quality gates. Required for P1-10, P1-11, P1-12.

### Review Record
| Field | Value |
|-------|-------|
| **Reviewer** | |
| **Date** | |
| **Decision** | ☐ Approve / ☐ Approve with Changes / ☐ Reject |
| **Comments** | |
| **Conflicts Resolved** | |

---

## 7. ADR-014 — Defer Voice Service from MVP

### Source
`ARCHITECTURE_DECISIONS.md` lines 357-379

### Problem & Context
- Voice container: root, `0.0.0.0:8001`, unauthenticated, no size/type/duration/rate limits
- No consumers in backend/clients; forces Hindi; downloads model at runtime; 0.6-1.2 GB RAM
- Security finding S-03 (High): unauthenticated high-cost endpoint

### Decision
Remove voice from default MVP profile. Do not publish port 8001. Keep code for later phase or delete if not needed. If reintroduced:
- Expose only via authenticated backend endpoint
- Enforce max upload size, MIME types, duration, per-user rate limits
- Non-root, read-only root fs, internal network, bounded temp storage
- Pre-bake/pin model + persistent cache
- Queue/concurrency cap + timeout
- Explicit language handling (auto-detect vs selected)

### Alternatives Considered
| Alternative | Assessment |
|-------------|------------|
| Secure it now | More Phase 1 work, no current consumer |
| Leave exposed | Rejected: S-03 High risk |

### Consequences
- **Positive:** Removes unauthenticated high-cost endpoint; lowers RAM; reduces attack surface
- **Negative:** No voice feature until reintroduced
- **Neutral:** Code/model remain available for later product decision

### Security & Data Implications
- **Directly addresses S-03 (High/Critical):** Unauthenticated voice endpoint contained
- Reduces RAM pressure (0.6-1.2 GB saved)
- Removes unauthenticated audio upload + transcription surface
- Audio data (potential PII) no longer processed without auth

### Verification Criteria
- Port 8001 not published
- Default Compose has no voice service
- Any future voice endpoint requires auth and limits

### Recommendation
**APPROVE** — Removes High-severity security finding with no current user impact. Required for P1-03.

### Review Record
| Field | Value |
|-------|-------|
| **Reviewer** | |
| **Date** | |
| **Decision** | ☐ Approve / ☐ Approve with Changes / ☐ Reject |
| **Comments** | |
| **Conflicts Resolved** | |

---

## 8. Review Summary & Gate G3 Status

| ADR | Title | Recommendation | Status |
|-----|-------|----------------|--------|
| ADR-001 | Modular Monolith | **APPROVE** | PENDING |
| ADR-002 | Python 3.12 + uv | **APPROVE** | PENDING |
| ADR-009 | Flat Error Envelope | **APPROVE WITH CHANGES** (coordinate clients) | PENDING |
| ADR-010 | Compose + Caddy | **APPROVE** | PENDING |
| ADR-013 | Hermetic Tests + CI | **APPROVE** | PENDING |
| ADR-014 | Defer Voice | **APPROVE** | PENDING |

### Gate G3 Decision

| Field | Value |
|-------|-------|
| **All 6 ADRs Approved** | ☐ Yes / ☐ No |
| **Gate G3 Status** | ☐ APPROVED / ☐ BLOCKED |
| **Owner Sign-off** | |
| **Date** | |

### Next Steps After G3 Approval
1. Update `ARCHITECTURE_DECISIONS.md` status from "Proposed" → "Approved" for each
2. Update `DECISION_REGISTER.md` Gate G3 → APPROVED
3. Unblock Phase 1 start, P1-07, P1-10, P1-18
4. Begin Phase 1 implementation per combined execution plan