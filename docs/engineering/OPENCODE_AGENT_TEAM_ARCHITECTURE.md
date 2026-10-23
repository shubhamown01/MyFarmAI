# OpenCode Agent Team Architecture — MyFarmAI

**Date:** 2026-10-23

## 1. Layering decision

One orchestration layer, not several.

| Concern | Owner | Rejected alternatives |
|---|---|---|
| Parallel teammates, worktrees, shared task board, messaging | **ensemble 0.20.0** (`team_*` tools) | CrewBee, FlowDeck, oh-my-openagent |
| Process discipline (plans, TDD, verification) | superpowers skills + compound-engineering | — |
| Repo/infra helper skills | gstack, ponytail | — |
| Documentation lookup | context7 MCP | — |
| Project knowledge graph | graphify (local plugin) | — |

`oh-my-openagent` stays installed but is not the team layer because its license is **SUL-1.0** (non-OSI, restricts commercial use). Ensemble is MIT and its ≥0.20.0 line supports OpenCode 2.x permission hooks.

## 2. Role map (required logical roles → implementation)

| Required role | Implemented as | Worktree | Notes |
|---|---|---|---|
| Lead orchestrator | session lead (you/this agent) + ensemble `team_*` | — | owns board, merges, gates |
| Frontend/UI | `.opencode/agents/frontend-engineer` + web best-practice skills | yes | web lives in tracked tree |
| Backend/DB | `.opencode/agents/backend-engineer` / `postgres-pro` | yes | tracked backend tree |
| Agricultural AI/ML | `.opencode/agents/ai-ml-engineer` | yes | local model work is RAM-gated (7 GiB host / 2 GiB VRAM — no concurrent local model runs) |
| Research/docs | `research-analyst`, `docs-writer`, `technical-writer` (no repo writes) | no | read-only |
| QA/security/performance | `qa-reviewer` (write in own tree), `security-engineer` (subagent, **edit-denied**, destructive-command-denied), `performance-engineer` | mixed | security-engineer is a subagent intentionally |
| Integration/release | `release-coordinator` — **added by this audit**, read-only reviewer of diffs/docs/release readiness | no worktree | review-only; does not deploy |

## 3. Sandbox rules (encoded in agent frontmatter / spawn flags)

- **Read-only agents** (`explore`-family, `release-coordinator`): `worktree: false` + explicit "no writes" prompt; they get the real tree because they never modify it.
- **Writing agents**: worktree `true` **when the target tree is tracked**. Example exception on record: `android/` is currently **untracked**, so a worktree checkout contains no `android/` — the P1-18 teammate therefore ran with `worktree: false` in the real tree. Once `android/` is committed, future writers must use worktrees again.
- **Security-engineer**: edit denied at config level (V2 `permissions`), i.e. advisory access even if a prompt asks it to write.

## 4. MCP topology

22 configured entries from project + global `opencode.json`; 16 verified reachable, 6 disabled with reasons (AUDIT §1). Rules:

- Always operate `opencode mcp` commands from `/data/MyFarmAI` — server sets are per-directory.
- `opencode reload` leaks duplicate MCP child processes; prefer targeted `opencode api post /api/experimental/mcp/<server>/connect` reconnects over repeated reloads.

## 5. Data flow for a delegated task

```
Lead ── team_tasks_add ──► shared board
      │                       ▲
      └─ team_spawn(agent,    │ claim
         worktree?, prompt) ──┘
             │ (async work, own session)
             └─ team_message/task completion ──► lead
Lead ── team_results ──► verify evidence ──► team_merge (writers, tracked trees only)
                                          ──► team_shutdown ──► team_cleanup
```

Safety properties: lead reviews every diff before merge; board state survives lead restarts; teammate message queues currently do **not** (OpenCode restart loses unread messages — mitigated by having the lead claim/complete critical evidence itself, see VALIDATION).
