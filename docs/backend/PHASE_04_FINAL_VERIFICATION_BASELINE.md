# Phase 4 Final Verification — Baseline Report (Part A §1)

**Date:** 2026-10-30 · **HEAD:** `3b2be0c` (Phase 3+4 project work committed with owner approval; 74 files) · **Branch:** `phase-01-foundation`

## Repository state

- **Committed:** backend Phases 2–4 tested state (auth/security + AI gateway/registry/prompts/evals), project docs, gate script. **Uncommitted (owner work, preserved):** 65 files — `android/*`, `backend/Dockerfile`, `backend/alembic/env.py`, `backend/app/orchestrator/`, `opencode.json*`, `.opencode/`, `.orchestrator/`, agent-infra docs, scratch scripts.
- **Canonical DB:** `backend/data/app.db` (untouched, git-ignored). Postgres container up (fresh, stamped `6cd2bffd9881`).
- **Ollama:** 0.33.2 active, loopback, 16 models on `/data/SentinelAI/ollama/models`, serial inference.

## Prior-phase verification (current evidence, not historical claims)

| Phase | Status | Current evidence |
|---|---|---|
| 0 | COMPLETE | Audit docs + security report in `docs/roadmaps/phase-00/`; findings tracked (voice containment not live, SearXNG secret pending rotation, Open-Meteo licensing owner-pending) |
| 1 | COMPLETE | Backend foundation; chat integration; `scripts/check.sh` gate green |
| 2 | COMPLETE | Postgres migration stamped; SQLite test-only per ADR-003/004; backup rehearsal recorded (`BACKUP_RUNBOOK.md`) |
| 3 | COMPLETE | Auth/CSRF/client-IP/lockout/audit; exit gate APPROVE-WITH-CONDITIONS → conditions closed (FCL-026/027); auth-matrix tests green |
| 4 | Execution COMPLETE (FCL-029..043) | Gateway/registry/prompts/evals; exit gate APPROVE-WITH-CONDITIONS (zero Critical/High, conditions closed); qa-reviewer + security-engineer independent evidence; §13 report written |

## Phase 4 verification status against Part A requirements

| Part A item | Status | Evidence gap to close in final verification |
|---|---|---|
| §2 Gateway tests (via API, not Ollama directly) | PARTIAL — unit/integration tests mock the Ollama client | **Live API test needed**: start backend, real Ollama chat through `/api/v1/chat` |
| §2 Model-specific tests | Only enabled model (`qwen3:0.6b`) testable — registry has exactly one enabled model; others disabled by evidence/scope (FCL-034/042/043) | Live chat quality/latency sample |
| §3 API integration (backend↔Ollama, web/Android↔backend) | Backend↔Ollama: live test pending. Web/Android↔backend: contract-verified (typecheck/lint/tests); no live E2E harness exists in repo | Live backend↔Ollama round-trip; contract review of client API layers |
| §4 Security testing | Extensive (Phase 3 suites + 4D pass + exit-gate review); image/SSF/retrieval N/A (no such features enabled) | Live unauthenticated-request probe against running backend |
| §5 Performance | Benchmarks + resource budget recorded (FCL-033/036, RESOURCE_BUDGET.md) | Record hardware snapshot + latency of the live run |
| §6 Regression | 130 backend + web 19/19 + builds clean (2026-10-30) | Re-run canonical commands as final evidence |
| §7 Documentation | Current through FCL-043 + execution report (amended) | Update after final verification |
| §8 Acceptance gate | All 12 §12 criteria evidence-backed | Final verification report → owner acceptance → Phase 5 |

## Rules for this verification

- Live backend runs against a **temp SQLite DB** (`/tmp/opencode/`), loopback-only, `environment=test`-compatible settings — the canonical DB and postgres are never touched.
- No model pulls; only installed models are used.
- Every test command and result is recorded; nothing is invented.
