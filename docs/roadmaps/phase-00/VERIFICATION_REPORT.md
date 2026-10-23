# Phase 0 Verification Report

**Phase:** 0 — read-only audit  
**Date:** 2026-10-21  
**Repository:** `/data/MyFarmAI`  
**Branch / commit:** `main` / `3cd1a6e60e0ad7d54888d632d4ea30820a37b60f`  
**Status:** Phase 0 complete. Phase 1 has **not** started and requires explicit approval.  
**Related:** [`README.md`](README.md), [`CURRENT_STATE_AUDIT.md`](CURRENT_STATE_AUDIT.md), [`GAP_ANALYSIS.md`](GAP_ANALYSIS.md)

---

## 1. Purpose

This report records what was executed, what was observed, and what was **not** verified during Phase 0. It supports the audit’s evidence claims and confirms that no project state was changed.

## 2. Environment at verification

| Item | Observed | Notes |
|---|---|---|
| OS / kernel | Ubuntu 26.04.1 LTS / `7.0.0-38-generic` | Read-only host inspection |
| RAM | 7.0 GiB total; 5.0 GiB used; 1.9 GiB available | Snapshot; changed slightly during the audit |
| Swap | 4.0 GiB total; 3.6 GiB used | Heavy pre-existing swap use |
| GPU | NVIDIA MX250, 2048 MiB VRAM, 2 MiB used; driver 580.178.04 | `qwen3:4b` weights alone are 2.5 GB |
| Root disk | `/dev/nvme0n1p5`, 126 GB, 115 GB used, **5.0 GB free (96%)** | 5.3 GB at initial audit; 5.0 GB at final check; build risk |
| Data disk | `/dev/sda2`, 274 GB, 85 GB used, **176 GB free (33%)** | Models and repo live here |
| Docker | 29.9.1; root `/var/lib/docker` on `/` | 25 images / 16.39 GB; 9 volumes / 24.08 GB |
| Running containers | 17, including unrelated Langfuse/Sentinel stacks, `myfarmai-voice`, `myfarmai-searxng` | Backend not running |
| Local Python | 3.14.4 (`backend/.venv`) | Container targets 3.12 |
| Container Python | `python:3.12-slim` (floating tag) | Verified from Dockerfile |

## 3. Commands and results

| Command | Result | Interpretation |
|---|---|---|
| `git status --short --branch` | `## main`; 4 modified files; many untracked paths | Large pre-existing uncommitted work; no audit changes to tracked files |
| `git log -1 --oneline` | `3cd1a6e chore: initialize My Farm AI foundation` | Single commit |
| `git remote -v` | empty | No remote or off-host backup |
| `git diff --stat` | 4 files, +117/−6 | Pre-existing modifications to `.gitignore`, `backend/app/main.py`, `backend/requirements.txt`, `docker-compose.yml` |
| `git check-ignore -v backend/data/app.db` | no match (exit 1) | Conversation DB is **not** ignored |
| `git check-ignore -v data/app.db` | `.gitignore:29:data/*` | Compose DB is ignored |
| `DATABASE_PATH=/tmp/opencode/phase0-audit-verify.db .venv/bin/python -m pytest -q` | **7 failed, 49 passed, 1 warning in 0.39 s** | Clean-DB run contradicts the documented 56/56 |
| `.venv/bin/python -m ruff check app tests` | `All checks passed!` | Lint clean |
| `.venv/bin/python -m mypy app` | `Success: no issues found in 26 source files` plus `mypy.ini ... section '[tool.mypy:overrides]' already exists` | Type check passes, but config overrides are not applied as intended |
| `docker compose config --quiet` | exit 0 | Current Compose is syntactically valid |
| Read-only SQLite query (Python `sqlite3`, `mode=ro`) | `backend/data/app.db`: `ok`, 122 conversations / 315 messages; `data/app.db`: `ok`, 35 / 74 | Both files pass integrity; they are divergent |
| `stat` on DB files | `backend/data/app.db` mode 644, mtime 2026-10-21 10:33:31; `data/app.db` mode 644, mtime 2026-10-19 11:07:54 | Audit did not modify either file |
| `stat` on env files | `.env` mode 664; `infra/searxng/.env` mode 600 | Root env is group/world readable |
| Secret-pattern scan of Phase 0 docs (`grep` for 64-hex, `sk-…`, `password=…`) | no matches | No credential values reproduced; not a substitute for a real scanner |
| Markdown link check of Phase 0 docs | 0 missing after this report was added | All local links resolve |
| `free -h`, `df -h`, `nvidia-smi`, `docker system df`, `docker ps` | values in §2 | Snapshot only |

### 3.1 Test failure analysis

The run used an isolated database path, yet `backend/data/app.db` retained its pre-audit mtime and the isolated file remained 0 bytes. The seven chat tests receive `500` responses because the app’s lifespan — which calls `init_db()` — is not executed by the test transport. The tests instantiate a global app and global settings rather than creating an app with their fixture settings. This is a **test-isolation defect**, not proof that chat is broken in the existing dev environment.

The previously reported “56/56” result is therefore not reproducible from a clean database. A correct suite must initialize the schema per test and inject settings, as proposed in Phase 1 (P1-10).

## 4. Repository and deliverable verification

| Check | Result |
|---|---|
| Phase 0 directory exists | `docs/roadmaps/phase-00/` |
| Required documents present | 13 of 13: `README.md`, `CURRENT_STATE_AUDIT.md`, `DEPENDENCY_INVENTORY.md`, `INTEGRATION_AND_COST_AUDIT.md`, `API_CONTRACT_INVENTORY.md`, `DATABASE_ASSESSMENT.md`, `SECURITY_AND_PRIVACY_AUDIT.md`, `HARDWARE_AND_DEPLOYMENT_ASSESSMENT.md`, `TARGET_BACKEND_ARCHITECTURE.md`, `ARCHITECTURE_DECISIONS.md`, `GAP_ANALYSIS.md`, `PHASE_01_IMPLEMENTATION_PLAN.md`, `VERIFICATION_REPORT.md` |
| Finding IDs | `CS-*`, `DEP-*`, `INT-*`, `API-C-*`, `DB-S*`, `S-*`, `HW-*`, `GAP-*`, `ADR-*` used consistently |
| Cross-references | Local links resolve; finding-to-gap traceability included in `GAP_ANALYSIS.md` §7 |
| Secret values | None reproduced; scans found no hex/JWT-like values |
| Existing files overwritten | None |
| Phase 1 executed | No |

## 5. Evidence highlights

| Claim | Evidence |
|---|---|
| No authentication or ownership | All routes lack auth dependencies; conversation schema has no user/farm column; lookups by ID only |
| Voice is exposed and unbounded | `docker ps` shows `0.0.0.0:8001->8001/tcp`; `ai/voice/main.py` has no size/type/rate limit; container runs as root |
| SearXNG secret is hardcoded | `infra/searxng/config/settings.yml` contains a 64-hex `server.secret_key`; value not reproduced |
| Conversation DB is not ignored | `git check-ignore` returns no match; file contains 122 conversations / 315 messages |
| No backup/restore | Repository search found no backup script, cron, snapshot, or runbook |
| Rate limiting is bypassable and unbounded | `middleware/rate_limit.py` trusts the first `X-Forwarded-For`; `defaultdict(list)` has no eviction |
| Tests are not hermetic | Clean-DB run: 49 pass / 7 fail; isolated DB remained empty |
| Android cannot reach the backend | `android/src/lib/api/client.ts:29` calls `fetch(endpoint)` with relative URLs; `getApiBaseUrl()` is unused |
| Open-Meteo is non-commercial | Official pricing/terms pages, accessed 2026-10-21; free tier non-commercial, attribution required, commercial requires a paid plan |
| Host is constrained | 1.9 GiB available RAM, 5.0 GB free on `/`, 2 GiB VRAM, Docker root on `/` |
| Documentation is stale | Existing backend docs claim no DB/chat/weather, a 404 `/health`, 56/56 tests, and version 0.2.0 vs code 0.1.0 |

## 6. What was not verified

- No live backend, Ollama, Open-Meteo, SearXNG, or voice request was made. Route behaviour is inferred from code and tests, not observed end-to-end.
- No OpenAPI JSON was captured from a running app; schemas were read from Pydantic models.
- No dependency CVE scan, container image scan, SBOM generation, TLS scan, firewall test, or penetration test was performed.
- No exploit or fuzzing was attempted.
- No model benchmark was run; `qwen3:4b` latency/VRAM behaviour is unknown.
- No PostgreSQL instance was created or tested; the migration plan is unexecuted.
- Android runtime behaviour was not tested on a device; the relative-URL defect is verified from source.
- Host values are a snapshot; other projects’ containers can change available RAM/disk.
- Open-Meteo terms and third-party licences can change; re-check them at the commercial decision point.
- The secret-pattern scan is not a full secret scanner; a dedicated scanner (for example gitleaks) is recommended in CI.
- Git history was not exhaustively rewritten or scanned for all historical data; the repository has one commit and the SearXNG config is untracked, but a pre-publication history review is still required.

## 7. No-change confirmation

Phase 0 changed **no** project source, configuration, dependency, database, container, or deployment state.

- The only intentional writes were **new** Markdown files under `docs/roadmaps/phase-00/` and an isolated test database at `/tmp/opencode/phase0-audit-verify.db`. Test/lint runs may have refreshed ignored Python/tool caches (`__pycache__`, `.pytest_cache`, `.ruff_cache`, `.mypy_cache`); these are not source, configuration, or data.
- No existing source, configuration, or data file was overwritten, deleted, renamed, staged, committed, or reverted.
- The four modified tracked files shown by `git diff --stat` were already modified before the audit; their contents were not edited by Phase 0.
- No packages were installed or upgraded; no images were built; no containers were started or stopped.
- No database migration, schema change, backup, or restore was executed against project data. SQLite was opened read-only for integrity/count queries; DB mtimes are unchanged.
- No paid API, account, or external service was called. Open-Meteo and licence terms were read from public web pages only.
- No credential value was printed, copied, or committed.
- Existing uncommitted/untracked user work was preserved.

## 8. Final status

| Area | Status |
|---|---|
| Repository audit | Complete |
| Dependency/integration/API/database/security/hardware assessment | Complete |
| Target architecture and ADRs | Proposed, awaiting approval |
| Gap register | Complete; 37 gaps (15 P0, 12 P1, 7 P2, 3 P3) |
| Phase 1 plan | Proposed; **not executed** |
| Phase 0 exit gate | Met for audit/documentation; approval still required |
| Phase 1 start | **Blocked pending approval** |

**Conclusion:** MyFarmAI has a working prototype with a clean FastAPI/service separation and local-only AI, but it is not production-ready. The highest-risk items are the absence of authentication/ownership, the exposed voice service, the hardcoded SearXNG secret, the untracked conversation database, the lack of backups, the non-hermetic test suite, the Android API-base defect, and the non-commercial weather dependency.

**Next step:** review [`README.md`](README.md) §6 and [`PHASE_01_IMPLEMENTATION_PLAN.md`](PHASE_01_IMPLEMENTATION_PLAN.md), then return one decision: **approve**, **approve with changes**, or **reject**. No implementation will begin until that decision is recorded.
