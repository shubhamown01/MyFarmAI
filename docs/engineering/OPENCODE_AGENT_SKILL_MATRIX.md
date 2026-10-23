# OpenCode Agent Skill Matrix — MyFarmAI

**Date:** 2026-10-23
Scope: 124 agents / 92 unique skills / 7 plugins present in the OpenCode installation for MyFarmAI. This matrix maps the subset actually usable per role, with the routing rules from `AGENTS.md`.

## Legend

- ✅ primary (load for every task of that role)
- ⭕ optional (load when the task explicitly touches that area)
- ⛔ blocked (licensed or non-functional; do not route)

## Role × skill matrix

| Skill / capability | Lead | Frontend/UI | Backend/DB | AI/ML | Research/docs | QA/Sec/Perf |
|---|---|---|---|---|---|---|
| task-checklist-execution | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| verification-before-completion | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Graphify rules (graph-first query) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| brainstorming | ✅ (before feature work) | ⭕ | ⭕ | ⭕ | ⭕ | — |
| systematic-debugging | — | ⭕ | ✅ | ⭕ | — | ✅ |
| frontend-design, frontend-ui-engineering, web-design-guidelines, ui-ux-pro-max | — | ✅ | — | — | — | ⭕ |
| vercel-react-best-practices, vercel-composition-patterns | — | ✅ (web) | — | — | — | — |
| ai-sdk | — | ⭕ | ⭕ | ⭕ | — | — |
| sql-pro, database-optimizer, postgres-pro | — | — | ✅ | — | — | ⭕ |
| performance-optimization, performance-profile | — | ⭕ | ⭕ | ⭕ | — | ✅ |
| webapp-testing (Playwright) | — | ✅ | — | — | — | ✅ |
| test-patterns, test-writer, test-driven-development | — | ✅ | ✅ | ✅ | — | ✅ |
| error-triage, systematic-debugging (infra) | — | — | ⭕ | — | — | ⭕ |
| docker-build-strategies, docker-compose-patterns, docker destructive-guardrails | — | — | ✅ | — | — | ✅ |
| writing-plans, executing-plans, subagent-driven-development | ✅ | ⭕ | ⭕ | ⭕ | ⭕ | ⭕ |
| docs: docs-writer / technical-writer / ce-doc-review / ce-noslop | ⭕ | — | — | — | ✅ | ⭕ |
| research: research-analyst, searxng queries | — | — | — | ⭕ | ✅ | — |
| security-auditor / OWASP paths | — | — | — | — | — | ✅ |
| deployment (vercel, azure families, deploy) | — | — | — | — | — | ⛔ unless explicit release request |
| consulting second opinions (gstack-codex, gstack-claude-code, ce-pov) | ⭕ | — | — | — | — | ⭕ |
| ponytail | ✅ (levels full by default) | ⭕ | ⭕ | ⭕ | ❌ not for prose | ⭕ |

Production UI tasks additionally pull in the **MyFarmAI project skills**: `myfarmai-apple-inspired-design`, `myfarmai-color-system`, `myfarmai-interaction-engineering`, `myfarmai-compose-review` (Docker reviews), `project-maintenance`.

## Blocked / restricted entries

| Item | Reason | Rule |
|---|---|---|
| oh-my-openagent flow/routing | SUL-1.0 license (non-commercial restriction) | installed, not used as orchestration |
| deployment skills | owner-approved release only | require explicit human release request |
| CrewBee / FlowDeck | duplicate orchestration | not loaded |
| MCP: linear, postgres, redis, kubernetes, MCP_DOCKER, puppeteer | missing credentials / duplicates / hung startup | disabled (see AUDIT §1) |
| MCP: searxng | backend 127.0.0.1:8890 down | queries FAIL until SearXNG service is created and started |

## Agent selection cheat sheet

| Task | Spawn |
|---|---|
| read-only recon | `explore` agent, `worktree: false` |
| Android/web UI fix | terrain-specific agent (`android-engineer`, `frontend-engineer`), worktree only if target tree is tracked |
| release readiness review | `release-coordinator`, `worktree: false` |
| security review | `security-engineer` (read-only) + human applies fixes |
| docs | `docs-writer` / `technical-writer`, `worktree: false` recommended |
