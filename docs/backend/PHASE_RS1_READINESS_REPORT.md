# Phase RS-1 — Production-Readiness Report (Sprint 1)

**Date:** 2026-11-01 · **Directive:** owner 2026-11-01 — "fix all bugs, check everything, proper readiness for production and deployment" (7C feature work deferred).
**Baseline:** Phase 6 Production Readiness Report 1 (owner-accepted, `04ebdb5`). This report covers the **15 commits** since (`04ebdb5..0fae8b9`): all of Phase 7A (dashboard), Phase 7B (crop planning), the critical gitignore repair, the mypy threshold gate, and the argon2 auth fix.
**Audit method:** release-coordinator read-only audit + orchestrator re-execution of all mechanical gates. Evidence source noted per row.

## Executive summary — verdict: READY WITH CONDITIONS

Every mechanical quality gate passes on the current tree. No code-level deploy blocker remains open. The conditions are **owner-side actions** (domain registration, device/browser QA, two ADRs, one pending secret-rotation authorization) plus recorded non-blocking gaps. Nothing in the codebase prevents deployment once the owner conditions are met.

## Evidence table

| # | Check | Result | Source |
|---|-------|--------|--------|
| 1 | Backend gate `bash scripts/check.sh` | ruff format+lint clean; **mypy 71 errors ≤ baseline 85** (threshold gate active — errors may only decrease); **209 passed**; **EXIT=0** | Orchestrator re-run, this session |
| 2 | Web `typecheck && test && lint && build` | all exit 0; **35/35 tests** (6 suites) | Orchestrator re-run |
| 3 | Android `typecheck && lint` | both exit 0 (static only — no jest/device infra) | Orchestrator re-run |
| 4 | Git state | zero uncommitted tracked changes; owner untracked files untouched | Orchestrator re-run |
| 5 | Secret scan of the 15-commit range | no real secrets (matches were a React `useState` password field and event-name constants) | release-coordinator |
| 6 | Dependency manifests | **zero changes** across the range — zero-cost policy holds | release-coordinator |
| 7 | Auth/X-Forwarded-For | trusted-proxy fix confirmed (AUTHENTICATION_FLOW, P3-11 closed) | release-coordinator (docs) |
| 8 | Backups | nightly pg_dump cron ACTIVE (02:00, marker `MYFARMAI-NIGHTLY-BACKUP`); DR tested in Phase 6 (restore 7 s → login 200) | release-coordinator (docs) |
| 9 | Migrations | 2 present (`6cd2bffd9881` → `a7c1e409f2b3`), both cycle-verified on isolated postgres | release-coordinator + 7B QA re-run |
| 10 | Docs/FCL/CHANGELOG | complete through FCL-088; API.md + APP_FLOW cover 7A + 7B; DEPENDENCY_POLICY conformance | release-coordinator |

## Deploy blockers — OWNER ACTIONS (ordered)

1. **DuckDNS subdomain registration (6K)** — blocks free TLS (Caddy DNS-01) and public exposure. Registration is an owner action; config ready.
2. **6H monitoring** — needs the production deployment to exist first (follows 6K).
3. **Android device QA** — dashboard + planning screens statically checked only; no emulator/device run has ever been performed.
4. **Playwright/axe browser flows** — e2e release-gate gap; jest+axe covers component surface only.
5. **Codebase LICENSE choice** — Phase 0 gate still open (SearXNG is AGPL-3.0; posture documented, license decision pending).
6. **ADR-015 (retention) + ADR-016 (voice)** — PROPOSED; require owner review/approval.
7. **SearXNG secret rotation** — plan documented, execution awaits separate owner authorization (per IMPLEMENTATION_PLAN/TRD).
8. **6N pre-launch documents** + **2 Phase-4 groundedness eval items** needing human review.

## Known gaps (non-blocking, recorded)

- **mypy 71 errors** repo-wide (was 99, silently suppressed; now gated at ≤85 and can only go down).
- **Android:** no jest infra; refresh-token rotation deferred (401 → sign-in); client envelope normalization code-reviewed, not device-tested.
- **Chat async-branch** test coverage gap (live-verified evidence recorded in Phase 6).

## What changed since Report 1

Phase 7A + 7B shipped (dashboard, crop planning — web/Android parity, farmer-task protection, append-only plan history); the **critical gitignore repair** (the entire ORM package had been untracked since inception — fresh clones could not build); the **mypy threshold gate** (no more silent error suppression); **argon2 malformed-hash 401 fix**. All QA verdicts: CONFIRMED WITH EXCEPTIONS (exceptions are the owner actions + gaps above).
