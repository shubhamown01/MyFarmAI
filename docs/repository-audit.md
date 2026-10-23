# MyFarmAI — Repository Audit (2026-10-23)

**Scope:** Full project organization and GitHub readiness.
**Branch:** `phase-01-foundation` · 64 tracked files · working tree heavily untracked · no remote configured.
**Supersedes/extends:** root `REPOSITORY_AUDIT.md` (2026-10-21), which should be considered historical.

---

## 1. Current State (verified)

### 1.1 Git status

- Branch `phase-01-foundation`, 9 commits: `3cd1a6e` (init) → Phase 1 tasks P1-01 through P1-09 (DB safety, secret remediation, voice containment, Python 3.12 + uv, quality gates) → Phase 2 SQLAlchemy 2 models + Alembic initial migration.
- **No remote** (`git remote -v` is empty). Nothing has ever been pushed — safe from history-leak risk, but GitHub publishing is blocked on decisions below.
- **Untracked (uncommitted) work** includes: entire `web/`, `android/`, `docs/` documentation suite, `MyFarmAI_Brand_Assets/` (6.5 MB), root README/CHANGELOG/CONTRIBUTING/SECURITY, `.env.example`, scripts, AGENTS.md, graphify tooling config.
- Tracked files = `backend/**` (app, tests, alembic, pyproject, uv.lock, Dockerfile, ruff/mypy/pytest configs) + `ai/voice/**` + `.gitignore`.

### 1.2 Component inventory

| Component | Path | Tech | Status | Entry point / run command |
|-----------|------|------|--------|--------------------------|
| Backend API | `backend/` | FastAPI, SQLAlchemy 2, Alembic, SQLite (aiosqlite), Python 3.12 + uv | **Implemented**, Phase 1–2 work committed | `uv run uvicorn app.main:app` (loopback only) |
| Web frontend | `web/` | Next.js 15, React 18, TS, Tailwind 3.4, TanStack Query v5, Zustand, Jest | Implemented (untracked) | `npm run dev` (scripts: build/start/lint/typecheck/test) |
| Android app | `android/` | Expo 51, RN 0.74, Expo Router, React Native Paper | Implemented (untracked) | `npm start`, `npm run android` |
| Voice service | `ai/voice/` | FastAPI, faster-whisper (small, CPU) | **Contained** — removed from Compose, port 8001 unpublished (P1-03) | Not in `docker-compose.yml` |
| Database | `backend/data/app.db` (canonical per G1 decision, pending owner approval) + legacy `data/app.db` | SQLite x2 | Both files exist (~150 KB each) | — |
| SearXNG | `infra/searxng/` | Dockerized, secret externalized (`${SEARXNG_SECRET}`, P1-02 ✓) | Partial | Manual Docker run |
| Docs | `docs/` | 60+ markdown: product/ (8), engineering/ (16), roadmaps (backend + frontend + phase-00/ 13 files), backend/, frontend/, integration/, ui/, branding/ | Extensive, current as of Phase 2 | — |
| Brand assets | `MyFarmAI_Brand_Assets/` | logos, app icon, favicon, social, guidelines + manifest | Present, 6.5 MB total | — |
| AI gateway | External Ollama | Qwen3 4B Q4_K_M (planned) | External to repo | `ollama pull qwen3:4b` |

### 1.3 Governance status (Phase 1 gates — verified from `docs/engineering/DECISION_REGISTER.md`)

| Gate | Status |
|------|--------|
| G1 Canonical DB (`backend/data/app.db`) | Decision recorded, **pending owner approval** |
| G2 License | **BLOCKED** — evaluation done (Apache-2.0 recommended), no decision, no LICENSE file |
| G3 Six ADRs (001/002/009/010/013/014) | **BLOCKED** — reviews documented, none approved |
| G4 Phase 1 revised scope | **BLOCKED** |
| G5 Backup drill | Drill passed, **pending owner acceptance** |
| G6 Voice containment | Implemented (commit 84 bef58), formal sign-off recommended |

**Consequence:** implementation proceeded past several "blocked" gates (commits exist), but the register still shows G2/G3/G4 as blockers. GitHub publication and any bulk restructure require G1–G6 owners sign-off recorded in that register.

### 1.4 Known issues found in this audit (2026-10-23)

| # | Issue | Severity | Location |
|---|-------|----------|----------|
| A1 | Whole `web/`, `android/`, `docs/`, root docs **uncommitted** — any disk loss loses ~all recent work | HIGH | repo root |
| A2 | No remote and no Git bundle located in repo (README does not cite a bundle path) | HIGH | git config |
| A3 | README Quick Start says "docker compose up -d" runs "backend + voice" — voice was removed from Compose; Python listed as 3.11 but environment is 3.12 | MEDIUM | `README.md` |
| A4 | Stray scratch files `web/test.ts`, `web/test.tsx`, `web/test-component.tsx` (tiny placeholder scratch, appear unused) | LOW | `web/` |
| A5 | `opencode.json.bak` and `opencode.json.backup-20261021-180336` still present although CHANGELOG claims they were removed | LOW | repo root |
| A6 | `du` on `web/node_modules` and `backend/.venv` exceeds 5 min (no symlink loop found, ~10k files in web/node_modules) — cosmetic/perf anomaly, no action | LOW | — |
| A7 | Roadmaps and backend docs reference `backend/` paths, Docker context `./backend`, `uv` tooling — a full restructure would churn every one | HIGH (restructure risk) | docs/, compose, Dockerfile |
| A8 | `.gitignore` excludes `.vscode/` — blocks committing recommended VS Code config | LOW | `.gitignore` |
| A9 | Test baseline known imperfect: historical note of clean-DB failures in `test_chat.py` (Phase 0 context); backend tests should be re-run to confirm current state | MEDIUM | `backend/tests/` |
| A10 | License absent (no `LICENSE` file) — GitHub readiness requires G2 decision | HIGH | repo root |

**Verified OK:** SearXNG secret is externalized; `data/` and `backend/data/` both ignored in Git with `.gitkeep` retained; brand assets modest size and no model weights present; no secrets found in source during basic scan.

---

## 2. Proposed Target Structure — Mapping and Recommendation

The requested target (`apps/web`, `apps/mobile`, `services/api`, `services/voice`, `shared/`, `infrastructure/`, `assets/brand/`, …) is a legitimate end-state layout. However, executing it **now** conflicts with three realities:

1. **In-flight roadmap work:** Phase 2 (backend persistence) is mid-implementation on `backend/` with Alembic migrations, `uv` lockfile, Dockerfile context `./backend`, and `pyproject.toml` entry points all keyed to current paths.
2. **Documentation coupling:** ~60 docs plus roadmaps reference current paths.
3. **Unresolved governance gates (§1.3)** — the register explicitly requires owner sign-off before architecture-affecting changes.

### 2.1 Recommended path (Option A — staged, order-safest)

Do not move source directories yet. Complete GitHub readiness in current layout, then restructure once Phase 2 baseline is committed and a remote exists:

1. **Now (safe, small):** clean stray files (A4, A5), fix README drift (A3), add Makefile + VS Code config (with `.gitignore` exception, A8), refresh root documentation set, commit all untracked work on `phase-01-foundation`, create a Git bundle, prepare (not execute) GitHub push commands.
2. **After owner signs G1–G6 and Phase 2 lands:** execute the full mapping in one reviewed change (Option B below) with branch `repo-restructure`, updating compose/CMake…/imports/docs in a single pass.

Mapping table (for the future restructure; identical-name files kept when content is current):

| Current | Future |
|---------|--------|
| `web/` | `apps/web/` |
| `android/` | `apps/mobile/` |
| `backend/` | `services/api/` |
| `ai/voice/` | `services/voice/` |
| `infra/` | `infrastructure/` (searxng, docker, monitoring) |
| `MyFarmAI_Brand_Assets/` | `assets/brand/` |
| `scripts/`, `docs/`, `tests → per-component tests/` | unchanged locations |
| `data/` (legacy DB) | removed/merged only with P1-01 backup verified |

### 2.2 Alternative (Option B — restructure immediately)

Execute §2.1 mapping now, then fix references (compose, Dockerfiles, tsconfigs, docs links). Cost assessment: forces re-touching 60+ docs, alembic paths, Docker context, possibly CI scripts, *days* before a pending owner review — highest churn, no functional benefit today. **Not recommended while Phase 2 is mid-flight, but will execute on request.**

---

## 3. Risks

| Risk | Mitigation |
|------|-----------|
| Uncommitted work loss (A1) | Commit + verified bundle before any structural change |
| Breaking in-progress Phase 2 (A7) | No source-directory moves until Phase 2 baseline is committed (recommended Option A ordering) |
| Data loss / canonical-DB ambiguity | Never delete/move either SQLite DB without G1 approval + backup (drill already exists) |
| License risk publishing without G2 | Do not publish until G2 decision recorded and `LICENSE` added |
| Secret/data leakage on push | Secret scan + confirm `git ls-files` has no `.env`/`*.db` before any push |
| Docker/voice state | Voice stays contained; no Compose service additions without governance update |

---

## 4. Validation Plan (after any change batch)

1. Backend: `cd backend && ./scripts/check.sh` (ruff format/lint, mypy, pytest).
2. Web: `npm run typecheck && npm run lint && npm test && npm run build` in `web/`.
3. Android: `npm run typecheck && npm run lint` in `android/`.
4. Compose: `docker compose config -q`.
5. git: `git status` diff review (before/after), `git ls-files | grep -Ei '\.(db|sqlite|env$)'` empty, secret scan (gitleaks or grep-based fallback).
6. `git bundle verify` of the created bundle.
7. Docs: link check across `docs/`. An existing script, `scripts/check.sh`, runs the backend gate.

---

## 5. Immediate Safe Batch (proposed, awaiting approval)

| Action | Files | Risk |
|--------|-------|------|
| Delete 3 scratch `web/test.*` files (verified unused) | `web/test.ts(x)`, `web/test-component.tsx` | None — placeholder/`"hello"` scratch |
| Delete 2 `opencode.json` backup files | root | None — dated backups, config is superseded |
| Move 2 root maintenance reports into `docs/engineering/` | `maintenance-report-*.md` | None — no references elsewhere |
| Update README Quick Start + Python version facts | `README.md` | None — doc fix only |
| Write `docs/project-overview.md`, `docs/architecture.md`, `docs/setup-guide.md`, `docs/api-documentation.md`, `docs/database-design.md`, `docs/demo-guide.md` | new docs | None — verify facts against code |
| Add root `Makefile` + `.vscode/{settings,tasks,launch,extensions}.json` + `.gitignore` exception | new files | None |
| Backend test baseline re-run | `backend/` | None — read-only test execution |

**Explicitly NOT in this batch** (blocked/awaiting approval): any directory move (A7), database file deletion/merge, SECRET rotation, LICENSE creation (G2 gate), voice service changes, `git push` or remote creation.

*See DECISION_REGISTER.md for gate sign-off requirements before proceeding past the batch.*
