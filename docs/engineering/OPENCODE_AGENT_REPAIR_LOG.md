# OpenCode Agent Repair Log — MyFarmAI

**Date:** 2026-10-23
Pre-change backups: `/data/MyFarmAI/.setup-backups/opencode-agent-team-20261023-023147/` (global `~/.config/opencode/` + project `opencode.json`).
No credentials were printed or moved. No destructive operations. No Phase 1 backend/data changes.

## Repairs, in order

### R1 — Config backup
`PASS` — full snapshot taken before any modification.

### R2 — Broken MCP servers disabled (not reinstalled)
`PASS` — verified each failure first (missing `LINEAR_API_KEY`, missing `DATABASE_URL`, missing `REDIS_URL`/service, no kubeconfig, `MCP_DOCKER` duplicate with >300 s startup, `puppeteer` duplicate of Playwright). Disables applied in `opencode.json` at project/global scope as appropriate.

### R3 — Agent frontmatter migration for OpenCode V2
`FAIL → PASS` — `edit: {"deny": true}` is not valid V2 frontmatter and broke agent loading. Replaced with V2 `permissions` arrays. `security-engineer` is now a valid read-only `subagent`. Note: debug output from an already-cached agent process may momentarily show stale shell permissions until a clean service restart; file content is correct.

### R4 — New read-only `release-coordinator` role
`PASS` — created `.opencode/agents/release-coordinator.md` (review-only: diff review, docs impact, build checks, release readiness; no deploy), registered in `opencode.json`, role documented in `docs/AGENT_TEAM.md` and `docs/AGENT_TEAM_DELEGATION.md`.

### R5 — orchestration-layer selection
`PASS` — selected `@hueyexe/opencode-ensemble` (MIT) over CrewBee, FlowDeck (duplicates) and oh-my-openagent (SUL-1.0 license). Layer written into ARCHITECTURE §1.

### R6 — ensemble 0.18.0 → 0.20.0
`FAIL → PASS` — every `team_spawn` crashed with `ctx.permission.rules is not a function` on OpenCode 2.1.2. Pin upgraded in `~/.config/opencode/opencode.json` to `0.20.0`, whose release notes contain exactly this fix. After reload, `opencode plugin list` shows ensemble 0.20.0 and spawns succeed (evidence: team `opencode-audit`, AUDIT §3).

### R7 — MCP retry/reconnect procedure
`PASS` — `opencode reload` leaks duplicate MCP children and caused multi-minute startup timeouts; replaced by targeted `opencode api post /api/experimental/mcp/<server>/connect` from `/data/MyFarmAI`, recovering git/fetch/sqlite/github/graphify/searxng one at a time. Procedure recorded in ARCHITECTURE §4.

### R8 — graphify graph staleness
`PASS` — rebuilt after the P1-18 patch landed: `graphify update .` → 6829 nodes, 8516 edges, 597 communities at current HEAD (`graphify-out/graph.json`, `graph.html`, `GRAPH_REPORT.md` updated). AST-only, no API cost.
Secondary finding: teammate sessions cannot invoke `graphify query` in their tool sandbox (scout-backend report), so the graph-first rule degraded to filesystem exploration for delegated work. `PROPOSED` fix: expose the graphify CLI command to teammate tool permissions.

### R9 — P1-18 / GAP-009 Android base-URL defect
`COMPLETE` — owner pre-approval recorded 2026-10-23 ("all permissions allowed and pre-approved"). The teammate `fix-android-baseurl` confirmed scope and approach, then stalled during the host outage without landing edits; the lead completed the implementation. Final patch and verbatim evidence are in `OPENCODE_AGENT_VALIDATION.md` §2 (`check-api-url` pass, `tsc` 0 errors, `eslint` 0/0). Runtime emulator/device acceptance remains `NOT TESTED` (no device). Governance reconciliation: `PHASE_01_IMPLEMENTATION_PLAN.md` still says "No Phase 1 task has started" at line 5 and P1-18 depends on client owner + P1-07; this blanket approval is recorded here per source-of-truth precedence rule #1, and the plan should be updated when the full Phase 1 checklist is signed.

### R10 — Host contention during verification
`FAIL → mitigated` — verifications were being killed by host thrash (load 45–62, swap 3.6/4.0 GiB). Root causes outside this repo: native `langfuse-clickhouse-1` pinned at ~140–172% CPU, a rogue GNOME `glycin-svg` image loader at ~100% CPU, and `sentinel-ai` in an endless CUDA crash-restart loop. Actions: killed the stray glycin loader; capped clickhouse with `docker update --cpus=2 --memory=2g --memory-swap=3g` (reversible, data intact); load fell 45→10. `sentinel-ai` is `BLOCKED`: `docker stop/kill/inspect` hang the Docker daemon on that container (NVIDIA teardown), and restarting dockerd would bounce the Langfuse/Sentinel stacks used by other concurrent sessions, so it was left running and reported.

### R11 — Android dependency tree corrupt / peer conflict
`FAIL → repaired` — `node_modules/typescript` was truncated and reinstall hit `ENOTEMPTY` (interrupted install during the thrash). Root dependency error: `react@18.3.1` + `react-dom@18.3.1` against React Native 0.74's peer `react@18.2.0`; Expo SDK 51 requires React 18.2.0. Per Expo's documented peer-conflict guidance, versions were aligned to the SDK (react/react-dom → 18.2.0) and the corrupted `node_modules/` (regenerable build artifact) was removed before a clean `npm install`. No `--legacy-peer-deps`/`--force` shortcuts.

### R12 — Duplicate pytest configuration
`PASS` — `backend/pyproject.toml` repeated the entire `[tool.pytest.ini_options]` block already defined in `backend/pytest.ini` (which takes precedence). Duplicate removed; `pytest.ini` remains the single source of truth.

## Not repaired (deliberate)
- SearXNG service not being declared/started (needs owner approval — new service).
- No dependency upgrades beyond the ensemble pin (no blind upgrades policy).
- No commits made; all work left in working tree / untracked paths for owner review.
