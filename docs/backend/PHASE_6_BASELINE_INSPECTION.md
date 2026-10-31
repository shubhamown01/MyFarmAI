# Phase 6 — Baseline Inspection Report (PART A §1)

**Date:** 2026-10-31 · **Type:** Read-only inspection, performed before Phase 6 final testing modifications · **Baseline commit:** `6658c62` (clean tree, no tracked modifications)

## 1. Repository state (verified)

- Branch: main (single-branch repo); HEAD `6658c62`; working tree clean of tracked modifications (untracked: `.orchestrator/`, `opencode.json.backup-*` — owner's pre-existing files, preserved untouched per standing rule).
- Commit chain this phase: `57fed50` (6A) → `3b1ad60` (6B/6J) → `bf7c99a` (6I/6N) → `700dc2d` (owner eval review) → `f98a8be` (6C/6E audits + G1) → `64ebab3` (live research evidence) → `f2f812c` (6C fixes) → `297785f` (addendum) → `0cda4b5` (6F/6G) → `caa65b2` (6D/6L pre-work) → `31b1799` (Report 2) → `6658c62` (M1 + 6D activation).

## 2. Phase 0–5 prerequisites

- Phase 5 Report 1 re-issued: verdict PARTIAL narrowing to 5I only (notifications, deferred to Phase 6+ by plan); gate 188→194 passed over subsequent work; live eval 11/11.
- Owner items still open from Phase 5: human review of 3 eval items (eval-p5b + eval-p5c done by owner; 2 Phase-4 groundedness items remain), ADR-015 retention (PROPOSED), ADR-016 voice (PROPOSED), Android device QA.

## 3. Deployment architecture (as-found)

- **Docker Compose:** postgres:17 (healthy, password via Docker secrets file, internal network `myfarmai-internal`, named volume) + backend (non-root host-UID, binds `./backend/data`, reaches host Ollama via socat bridge at 172.22.0.1:11434 — bridge IP fragility documented in compose). `docker compose config` validates clean.
- **Host Ollama:** 127.0.0.1:11434; registry-enabled models qwen3:0.6b (chat) + qwen3-vl:2b (vision); serial constraint enforced host-side (`OLLAMA_MAX_LOADED_MODELS=1`, `NUM_PARALLEL=1`).
- **Web:** Next.js, `output: standalone` (6F), build + boot verified; API URL baked at build time.
- **Android:** Expo managed workflow; no signing config; no keystore material in git (6G).
- **No published ports from compose** (reached via dev rewrites / local runs); no reverse proxy deployed yet; no TLS yet.
- **Storage verified HDD-wired:** `daemon.json` data-root=/data/docker; containerd root=/data/containerd (kernel mount table confirms live snapshots there).
- **Stray containers observed (NOT MyFarmAI's):** `wizardly_kirch`, `confident_keller` (unhealthy), `thirsty_thompson`, `mcp-redis` — pre-existing host state; untouched.

## 4. Environment separation

- `backend/app/core/config_profiles.py`: production validator now enforces explicit CORS, absolute DB path, non-localhost Ollama, **explicit allowed_hosts** (M2 fixed). Dead secret_key check removed (L1).
- `.env` gitignored (verified); `.env.example` 52 lines, zero secrets, `ENVIRONMENT="development"` default.
- Web `.env`: localhost API URL + commented production placeholder; `NEXT_PUBLIC_API_BASE_URL` baked at build time (6F).
- No staging environment exists yet (blocked on hosting config — now decided: this machine).

## 5. Database & migrations

- Alembic present (`backend/alembic.ini`, 2 version files; initial schema). Canonical historical SQLite DBs in `backend/data/` remain untouched on the bind mount (never migrated without owner approval).
- **Backups ACTIVE (6D):** nightly cron 02:00 (`# MYFARMAI-NIGHTLY-BACKUP` marker, owner-approved 2026-10-31), `scripts/backup.sh` integrity-checked (pg_restore --list), retention 14 nightly + first-of-month; two verified manual runs; restore drill PASSED (14/14 tables in isolated container, FCL-066).
- Live DB: postgres `myfarmai` (8.5 MB, 0 users, 14 public tables) — pre-launch.

## 6. AI inference (as-found)

- Registry-gated model selection everywhere **after G1 fix** (vision now passes `require_enabled`).
- Live evidence: chat eval 11/11 (qwen3:0.6b); vision 200 live (qwen3-vl:2b, template-compliant); research 200 live via SearXNG loopback container.
- Known host concerns (6E): swap 100% full (G7); cold VL load > 120 s default timeout (deployment must warm or raise timeout); per-process concurrency (single-worker requirement).

## 7. CI/CD, monitoring, incident, legal

- CI: `.github/workflows/ci.yml` — backend/web/android/compose gates; **no deploy jobs** (verified by grep at creation). Note: repo has no GitHub remote configured locally — workflow is ready but unexercised by a real runner (flagged honestly since 6J creation).
- Monitoring: none deployed (6H pending deployment track).
- Incident runbooks: 10 documented (6I). Legal/privacy inventory: complete (6N), 5 pre-launch documents required.

## 8. Owner decisions recorded 2026-10-31 (executed where approved)

1. Hosting: **this machine now, free cloud later** (portability-first).
2. Domain: **free/opensource TLS route** (plan: DuckDNS + Caddy DNS-01 or Cloudflare Tunnel; registration = owner action).
3. Nightly backups: **APPROVED → cron active** (6D complete).
4. M1: **require auth** → implemented + tested (all weather/resources endpoints, 401 tests).

## 9. Identified gaps going into final testing

- No production deployment/TLS/domain yet (owner must register the free subdomain before 6K executes).
- No staging environment (to be created on this host per decision 1).
- Monitoring (6H), production acceptance (6M) blocked on the above.
- Dependency vulnerability scan and secret scan: tooling (pip-audit/bandit/gitleaks) not installed — will run where installable without violating storage policy, else flagged NOT RUN.
- Host swap 100% full — ops pre-check before production AI serving.

**Baseline verdict: consistent with prior reports; no unexpected state found; ready to proceed with Phase 6 final testing.**
