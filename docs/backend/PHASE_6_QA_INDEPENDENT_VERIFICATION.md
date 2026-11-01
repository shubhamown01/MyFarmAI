# Phase 6 — Independent QA Verification

**Date:** 2026-10-31 · **Verifier:** Independent QA subagent (read-only except test execution)
**Scope:** Re-verify Phase 6 claims against reality with real commands; no trust in implementation-agent reports.
**Commits verified:** `6658c62`, then `3d1217e` (branch `phase-01-foundation`)

## Verdict: Phase 6 evidence — **CONFIRMED**

All mechanically testable claims were reproduced with real commands. One material gap was caught by this independent review (two unauthenticated `/resources` sub-endpoints) and was **fixed and re-verified by QA at `3d1217e`**. Remaining notes are minor and documented below (check.sh banner reliability, G2 attestation-only evidence, mypy debt).

## Verification table

| # | Claim (source doc) | Verification command | Actual result | Status |
|---|---|---|---|---|
| V-1 | Backend gate: 195 passed, exit 0 (FCL-068/069); ruff clean | `bash scripts/check.sh` (from `backend/`); `uv run ruff check app tests --exclude app/orchestrator` | `195 passed, 24 warnings in 80.47s`, CHECKSH_EXIT=0; ruff `All checks passed!` exit=0 | **VERIFIED** |
| V-1a | Ruff clean (unexcluded scope) | `uv run ruff check app tests` | 25 errors, **all in `app/orchestrator/`**, which the canonical gate and ci.yml deliberately exclude. Pre-existing scaffold code, not a Phase 6 regression | **VERIFIED** (with note) |
| V-2 | M1: ALL weather/resources endpoints require auth (6C addendum, FCL-068) | Read `weather.py` + `resources.py` at `3d1217e`; `pytest -v` on the three 401 tests | weather 2/2 auth'd; resources **3/3** auth'd (resources.py:18, 40, 52 — `GET /resources`, `/resources/categories`, `/resources/{category}`); 3/3 401 tests PASS incl. `test_resources_categories_and_category_require_auth` | **VERIFIED** (fixed at `3d1217e` after QA caught 2/5 endpoints open at `6658c62`) |
| V-3 | M2: production validator rejects default `allowed_hosts` (FCL-064) | `pytest tests/test_config_profiles.py` | 3/3 pass (`test_production_default_allowed_hosts_rejected`, `test_production_explicit_allowed_hosts_passes`, `test_non_production_skips_checks`) | **VERIFIED** |
| V-4 | G1: vision registry gate present + regression test (FCL-062) | Read `vision.py`; `pytest tests/test_p5e_vision.py` | `registry.require_enabled(settings.vision_model, registry.VISION)` at vision.py:92 → 503 `VISION_MODEL_UNAVAILABLE`; 9/9 vision tests pass incl. chat-only-model regression | **VERIFIED** |
| V-5 | 6D: cron active with `MYFARMAI-NIGHTLY-BACKUP` marker (FCL-068) | `crontab -l` | `0 2 * * * /bin/bash /data/MyFarmAI/scripts/backup.sh >> /data/MyFarmAI-backups/postgres/backup.log 2>&1` with marker comment | **VERIFIED** |
| V-6 | 6D: recent integrity-checked dumps exist (FCL-066/068) | `ls -la /data/MyFarmAI-backups/postgres/`; `docker exec -i myfarmai-postgres pg_restore --list < newest.dump \| grep -c " TABLE "` | 4 dumps, all 44,104 B, 2026-10-31 11:16–11:43; newest lists **28 TABLE entries** (matches doc) | **VERIFIED** |
| V-7 | backup.sh has no `--file=-` (FCL-066 gotcha avoided) | `grep -n "file=" scripts/backup.sh` | No matches; script uses `pg_dump -Fc > "$FILE"` + `pg_restore --list` integrity check | **VERIFIED** |
| V-7a | Timed recovery exercise: backup 1 s, isolated restore 7 s, app boots on restored DB (health 200), login on restored data 200 | Not re-executed — would require manipulating containers/DB state. Attestation reviewed: argon2 malformed-hash → 500 (not 401) honestly recorded as a Low robustness finding | Internally consistent, mechanism (dump/restore/health/login) separately corroborated by V-6 and V-1 | **UNVERIFIED** (attestation-only; not disproven) |
| V-8 | 6J: ci.yml has backend/web/android/compose gates, **no deploy jobs** (Report 2 §1, FCL-060) | Read `.github/workflows/ci.yml`; `grep -rin deploy .github/workflows/` | 4 jobs present (backend, web, android, compose-validate); grep matches **comments only** — zero deploy/push steps | **VERIFIED** |
| V-9 | Web: typecheck/jest/lint/build pass; standalone entry exists (FCL-065) | `npm run typecheck && npm test -- --runInBand --ci && npm run lint && npm run build` | typecheck exit 0; **19/19 jest**; "No ESLint warnings or errors"; build succeeded; `.next/standalone/web/server.js` exists (6.5 KB; standalone **dir = 63 MB**, matching FCL-065) | **VERIFIED** |
| V-10 | Android: typecheck + lint pass (FCL-065, Report 2) | `cd android && npm run typecheck && npm run lint` | Both exit 0, no errors | **VERIFIED** |
| V-11 | Compose valid | `docker compose -f docker-compose.yml config --quiet` | Exit 0 | **VERIFIED** |
| V-12 | G2 closed with live vision evidence (6E addendum, FCL-062) | Not reproducible here — re-running requires loading `qwen3-vl:2b`, prohibited (serial-Ollama host). Indirect corroboration: `GET /api/tags` confirms live model inventory | Recorded live evidence (200, warm 24 s, cold-start 504 finding) is internally consistent but **not independently re-executed** | **UNVERIFIED** (attestation-only; not disproven) |
| V-13 | Report 2 §3 "192 passed" / 6C addendum "192" | Consistency check vs git history | Accurate at their commits (`caa65b2` baseline, pre-M1); superseded by 194 → 195 as tests were added — all correct in context | **VERIFIED** |
| V-14 | Ledger FCL-059..068 accuracy | Cross-checked each entry against commands above | All reproduce; the original M1 scope overstatement ("all 4 endpoints… /resources (x2)") was caught by QA and corrected at `3d1217e` | **VERIFIED** after correction |
| V-15 | Git state | `git status --porcelain` | No uncommitted tracked changes at both verified commits. Untracked housekeeping files only: `.orchestrator/`, `opencode.json.backup*` (×3), root `package.json` + `package-lock.json`, `resources/`, `test-*.js` (×4) | **VERIFIED** |

## check.sh banner-reliability observation

**Do not trust the banner; trust the exit code and the pytest summary line.** FCL-068 records that `check.sh` printed "All checks passed!" **even with 2 failing tests** (observed twice by the implementation agent). QA could not reproduce the failure mode in this session (in both QA gate runs the banner matched reality), but the observation is consistent with a banner driven by the last command's output rather than aggregate exit status. QA policy adopted for this report: a check passes only when (a) the process exit code is 0 **and** (b) the pytest summary line reads `N passed` with no `failed`/`error`. Both were satisfied in every gate run recorded here. Recommendation: fix check.sh to `exit` on the pytest status explicitly and gate the banner on it.

## Known non-blocking items (re-confirmed)

- **mypy:** 72 pre-existing errors in 16 files inside the gate run — gate passes by design (documented in Report 2 §3 as "mypy 54 pre-existing errors"; the count has since grown to 72 and should be tracked separately from the gate).
- **app/orchestrator/** excluded from ruff by the canonical gate; 25 lint errors live there.
- In-memory rate limiter/lockout (SEC-P5-03 / 6C-I1) — accepted for single-host, revisit at scale-out.
- Untracked housekeeping files at repo root (V-15) — cleanup candidate, no Phase 6 impact.

## Release readiness

- [x] All verification criteria met with evidence
- [x] No concealed failures — the M1 gap was surfaced by independent check and fixed under QA verification
- [x] Known limitations documented (G2/V-7a attestation-only, check.sh banner, mypy debt, orchestrator lint)
- [x] Blocker list empty (M1 residual closed at `3d1217e`)

QA: @qa-reviewer (independent)
Date: 2026-10-31
