# Report 1 — Phase 6 Final Testing Report (re-issue)

**Date:** 2026-11-01 · **Baseline:** `6658c62` · **Final commit:** `542c47b` · **Supersedes:** the PARTIAL issue of 2026-10-31

## Verdict: READY FOR OWNER RELEASE APPROVAL

All mechanically testable Phase 6 criteria pass with real, committed evidence. Independent QA verdict: **CONFIRMED** (`PHASE_6_QA_INDEPENDENT_VERIFICATION.md`). Zero unresolved Critical/High findings. Remaining items are named owner actions and deployment-track work — none is a code defect.

## 1. Preflight & baseline (§1)
- Read-only inspection at `6658c62`: clean tree, compose valid, postgres healthy, cron active, Alembic present, storage HDD-wired, env separation verified. Report: `PHASE_6_BASELINE_INSPECTION.md`.
- Phase 0–5 prerequisites verified; owner decisions of 2026-10-31 executed (M1 auth, 6D backups, hosting + domain decisions recorded).

## 2. Architecture, environment separation (§2–3)
- Compose: postgres (secret-file password, internal network, named volume) + backend (non-root, socat bridge to host Ollama); **no published DB/model ports**; `docker compose config` exit 0.
- Production profile validator enforces explicit CORS/allowed_hosts/absolute DB path (M2). `.env` gitignored; no secrets in tree (pattern scan clean).

## 3. Backend production results (§4)
| Check | Result |
|---|---|
| Full gate `bash scripts/check.sh` | **195 passed, exit=0** (verified via pytest line, not the banner — banner is unreliable, observed twice) |
| Dependency scan | pip-audit: **No known vulnerabilities** (uv cache on /data) |
| Secret scan | Pattern-based: clean (no literals/placeholders in tracked files) |
| Auth/authorization | All weather (2/2) + resources (3/3) endpoints require auth (QA-caught M1 gap fixed, `3d1217e`); 401 tests pass |
| Request-ID + logging | **Fixed this cycle** (`176f508`): IDs previously dropped from log lines by the default formatter; now rendered and live-verified (`request_id=mf6-log-check-7` in both log lines + header echo) |
| Graceful shutdown | SIGTERM → clean shutdown, DB connections closed, port released (live smoke) |
| Health endpoints | `/health` 200; no sensitive info exposed |

## 4. Database & DR (§5, §11)
- **Timed recovery exercise (this cycle, direct evidence):** backup **1 s** → isolated postgres:17 container restore **7 s** (14/14 tables) → app booted against the restored DB (health 200) → **login on restored data 200**. RTO ≈ **8 s** at pre-launch scale (8.5 MB, 0 users). Live DB untouched.
- Nightly pg_dump backups ACTIVE (cron 02:00, marker-commented, integrity-checked, retention 14 nightly + first-of-month); backups owner-controlled at `/data/MyFarmAI-backups` (policy rule 16).
- Finding (Low, queued): malformed stored argon2 hash yields 500 instead of clean 401.

## 5. AI infrastructure (§6)
- Live chat (qwen3:0.6b, real endpoint, real model): **3 turns 200 OK — 17.4 s / 6.9 s / 7.7 s**. (A pre-existing P5B regression — async-path `UnboundLocalError` on farm-less chat — was root-caused via the new 500-handler logging and fixed, `dea5320`.)
- Vision: live 200 on qwen3-vl:2b with registry gate (earlier evidence; attestation-only in QA table V-12 — host serial-Ollama prevents independent re-run).
- Research: live 200 via SearXNG loopback with official-domain ranking.
- Concurrency/queue caps verified in code + tests (503 AI_BUSY protects 2 GiB VRAM). Model licenses recorded in `docs/engineering/DEPENDENCY_POLICY.md` (re-verify model cards before public release).

## 6. Web & Android (§7–8)
- Web: typecheck + **19/19 jest** + lint + production build PASS; standalone entry `.next/standalone/web/server.js` verified by independent QA.
- Android: typecheck + lint PASS. Release build/device QA remain owner-side (no keystore in git — by design).

## 7. Security assessment (§12)
- Findings closed this phase: M1 (weather/resources auth — QA-caught full closure), M2 (production validator), L1/L2, G1 (vision registry gate). Classification + scans in `DEPENDENCY_POLICY.md` / `PHASE_6C_BACKEND_HARDENING_AUDIT.md`.
- **No unresolved Critical or High findings.** In-memory rate limiter accepted for single-host (SEC-P5-03/6C-I1).

## 8. CI/CD, rollback, monitoring (§9–10)
- ci.yml: 4 gate jobs (backend/web/android/compose), **zero deploy steps** (grep-verified) — production deployment cannot happen via ordinary commits; rollback = redeploy previous tag (documented in runbooks).
- **Monitoring: NOT DEPLOYED** (6H) — requires the production deployment to exist first. Blocked, not failed.

## 9. Counts (honest)
- **Passed:** backend 195 tests; web 19 tests + typecheck/lint/build; android typecheck/lint; compose validate; DR exercise; 3 live AI flows; 2 live smoke checks (request-ID, shutdown).
- **Failed:** 0 unresolved (2 real defects found AND fixed this cycle: chat async-path 500, silent 500s; 1 timing-test flake under load, passed on clean rerun).
- **Blocked:** monitoring (needs deployment), TLS/domain (owner DuckDNS registration), staging env (hosting decided, not yet provisioned), Android release build + device QA, live CI run (no GitHub remote configured locally).
- **Deliberately not exercised:** no production deployment (requires owner release approval).

## 10. Changed files this testing cycle
`backend/app/api/v1/resources.py`, `backend/app/api/v1/chat.py`, `backend/app/factory.py`, `backend/tests/test_resources.py`, `scripts/backup.sh`, docs (`PHASE_6_BASELINE_INSPECTION.md`, `DEPENDENCY_POLICY.md`, QA verification, FCL-068..072, CHANGELOG). Commits: `6658c62` → `3d1217e` → `dea5320` → `176f508` → `542c47b`. No secrets, no model weights, no DB data in git.

## 11. Owner approval status
- **Awaiting owner acceptance of this report.** Upon acceptance: register the free subdomain (DuckDNS account action) → 6K executes → staging deploy → monitoring (6H) → 6M final acceptance → release.
