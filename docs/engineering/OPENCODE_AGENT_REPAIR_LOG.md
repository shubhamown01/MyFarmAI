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
`BLOCKED` — graph built at commit `067aed0`, HEAD `3839cff`; `graphify-out/` is also dirty from hooks (expected). Update is deferred until after the P1-18 patch lands: `graphify update .` runs once at the end (AST-only, no API cost).
Secondary finding: teammate sessions cannot invoke `graphify query` in their tool sandbox (scout-backend report), so the graph-first rule degraded to filesystem exploration for delegated work. `PROPOSED` fix: expose the graphify CLI command to teammate tool permissions.

### R9 — P1-18 / GAP-009 Android base-URL defect
Owner pre-approval recorded 2026-10-23 ("all permissions allowed and pre-approved").
In-flight: teammate `fix-android-baseurl` (android-engineer, real tree because `android/` is untracked). Diff + verification evidence goes to VALIDATION. Governance reconciliation: plan `PHASE_01_IMPLEMENTATION_PLAN.md` still says "No Phase 1 task has started" at line 5 and P1-18 depends on client owner + P1-07; this blanket approval is recorded here per source-of-truth precedence rule #1, and the plan should be updated when the full Phase 1 checklist is signed.

## Not repaired (deliberate)

- SearXNG service not being declared/started (needs owner approval — new service).
- No dependency upgrades beyond the ensemble pin (no blind upgrades policy).
- No commits made; all work left in working tree / untracked paths for owner review.
