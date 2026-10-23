# OpenCode Agent Team Audit — MyFarmAI

**Date:** 2026-10-23
**Auditor:** Lead of OpenCode team `opencode-audit` (this record was written by the orchestrating agent)
**Scope:** OpenCode v2.1.2 installation used for MyFarmAI — agents, skills, plugins, MCP servers, team/delegation layer.
**Status labels:** `PASS`, `FAIL`, `BLOCKED`, `NOT TESTED`, `PROPOSED`

---

## 1. Environment inventory (observed)

| Item | Value | Evidence |
|---|---|---|
| OpenCode version | v2.1.2 | `opencode` CLI output |
| Agents available | 124 registered | `opencode agent list` / project + global `agents/` dirs |
| Skills installed | 92 unique | skill list after de-duplication of project/global dirs |
| Plugins loaded | 7 | see table below |
| MCP servers | 22 entries | `opencode mcp list` (run from `/data/MyFarmAI`; output differs per directory) |

### Plugins

| Plugin | Version | License | Verdict |
|---|---|---|---|
| `@hueyexe/opencode-ensemble` | 0.20.0 | MIT | **Kept** — primary team layer |
| `superpowers` | git (bb92a77) | MIT | Kept |
| `compound-engineering` | git (8673dfb) | MIT | Kept |
| `gstack` | 1.91.164.0 | MIT | Kept |
| `ponytail` | 5.3.2 | MIT | Kept |
| `@upstash/context7-opencode` | 0.2.1 | MIT | Kept |
| `oh-my-openagent` | 5.1.40 | SUL-1.0 (non-OSI) | Kept installed, demoted — not used as team layer; license restricts commercial use |

**Rejected as duplicates:** CrewBee, FlowDeck (overlapping orchestration roles vs ensemble). No code removed; they are simply not routed to.

### MCP servers — disables and reasons

Disabled rather than reinstalled, each verified non-functional first (no secrets printed):

| Server | Reason | Status |
|---|---|---|
| `linear` | no `LINEAR_API_KEY` present | `FAIL — missing credential` |
| `postgres` | no `DATABASE_URL` | `FAIL — missing credential` |
| `redis` | no `REDIS_URL`, no running redis service | `FAIL — no service` |
| `kubernetes` | no kubeconfig | `FAIL — no cluster` |
| `MCP_DOCKER` | duplicate of existing docker tooling; startup timed out (>300 s) | `FAIL — hung startup` |
| `puppeteer` | duplicate of Playwright; no usable sandbox | `FAIL — duplicate` |

### MCP servers verified working (read-only test call)

`PASS` — graphify, filesystem, git, memory, sqlite, github, context7, atlassian, sentry, shadcn, figma, vercel, playwright, 21st, fetch, gh-grep.
`FAIL` — searxng: MCP process connects but backend `http://127.0.0.1:8890` is down (`available: false`); `infra/searxng/` has config/data but **no compose service defined**. Not started (needs owner approval for new services).

---

## 2. Config repair log (summary — details in REPAIR_LOG)

- Backed up global + project config to `.setup-backups/opencode-agent-team-20261023-023147/` before any change.
- Fixed invalid agent frontmatter (`edit: {"deny": true}` → V2 `permissions` arrays) — `security-engineer` is now a valid `subagent` with edit deny and destructive-command denies.
- Added read-only `release-coordinator` agent (`.opencode/agents/release-coordinator.md`) and registered it in `opencode.json`.
- Upgraded ensemble pin `0.18.0 → 0.20.0` in global config. Rationale: release notes for 0.20.0 explicitly fix `ctx.permission.rules is not a function` on OpenCode ≥ 2.0.19.

## 3. Delegation test (the real evidence)

Team: `opencode-audit` (lead + 3 members). Layer: **ensemble 0.20.0** `team_*` tools.

| Test | Result | Evidence |
|---|---|---|
| Team + shared task board creation | `PASS` | 2 tasks on board |
| First spawn on ensemble 0.18.0 | `FAIL` | error `ctx.permission.rules is not a function` |
| Spawn after upgrade to 0.20.0 | `PASS` | `team_spawn` returned teammate session |
| Read-only scout task (backend audit) | `PASS` | scout-backend report: 6 test files / 56 tests, exact run command `uv run pytest -q` from `backend/`, config duplication noted. Matches independent 56-passed baseline run by lead. |
| Read-only scout task (API URL audit) | `PASS (delayed delivery)` | scout-api's final report arrived late (server-restart outage window held it unread): web client DOES apply `NEXT_PUBLIC_API_BASE_URL` (client.ts L3/L21/L40), android `client.ts` L29 `fetch(endpoint)` never prefixes the exported `API_BASE_URL` (dead code), no android tests assert the behavior, defect already flagged as INT-F07 in `docs/roadmaps/phase-00/INTEGRATION_AND_COST_AUDIT.md:82`. Findings independently corroborated by the lead's direct file inspection. |
| Implementation delegation | See VALIDATION | teammate `fix-android-baseurl` (android-engineer), worktree disabled intentionally — `android/` is untracked, so a fresh worktree would not contain it |
| Known fragility | documented | OpenCode server restarted repeatedly during the session; teammates went idle and unread message queues were lost. Task board survived. |

**Limitation accepted:** `graphify query` was not invocable through the explore teammate's tool set (scout-backend report, verbatim note). The graphify-first rule therefore degraded gracefully to filesystem exploration. Not fixed in this audit; recorded for follow-up.
