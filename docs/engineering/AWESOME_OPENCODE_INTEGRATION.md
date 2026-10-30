# Awesome-OpenCode Integration

**Project:** MyFarmAI  
**Integration Date:** 2026-10-25  
**Source Repository:** https://github.com/weisser-dev/awesome-opencode  
**Version:** 1.5.0 (cloned at commit from 2026-10-25)

---

## Summary

This document records the integration of the awesome-opencode resource repository into the MyFarmAI OpenCode installation. The integration provides 108 specialist agents, 15 skills, 3 skill packs, smart model configuration, and 18 curated MCP servers.

---

## Source Repository Analysis

### Repository Type
**awesome-opencode (weisser-dev)** is a **CLI tool and template collection** that:
- Analyzes project structure and auto-detects languages
- Interactively recommends agents, skills, models, and MCP servers
- Generates `opencode.json`, `.opencode/agents/`, `.opencode/skills/`, and `AGENTS.md`
- Provides 108 agent templates, 15 skill definitions, and 5 config presets
- Offers 3 skill packs (design, process, behavior) from vetted upstream sources

### What It Is NOT
- NOT a runtime orchestration component
- NOT an agent execution engine
- NOT a replacement for OpenCode's native subagent system
- Does NOT automatically enable multi-agent collaboration

### License
MIT License - compatible with MyFarmAI

---

## Selected Resources

### Agents (108 from awesome-opencode + 7 custom MyFarmAI)

All 108 awesome-opencode agents are installed in `.opencode/agents/`. The 7 custom MyFarmAI agents extend specific capabilities:

| Custom Agent | Base Awesome-OpenCode Equivalent | MyFarmAI Specialization |
|--------------|----------------------------------|-------------------------|
| myfarmai-orchestrator | workflow-orchestrator + agent-organizer | Project-wide coordination, roadmap execution |
| backend-engineer | fastapi-developer + backend-developer | FastAPI, SQLAlchemy, PostgreSQL, auth |
| frontend-engineer | nextjs-developer + frontend-developer | Next.js, React, Tailwind, accessibility |
| android-engineer | mobile-developer + flutter-expert | Expo/React Native, microphone/audio |
| ai-ml-engineer | machine-learning-engineer + llm-architect | Ollama, Qwen, PersonaPlex, model storage |
| research-engineer | research-analyst + search-specialist | SearXNG, web search, citations, SSRF protection |
| security-engineer | security-engineer + penetration-tester | Auth audits, secret protection, threat modeling |
| qa-reviewer | test-automator + code-reviewer | Unit/integration tests, API contracts, regression |
| release-coordinator | git-workflow-manager + deployment-engineer | Diff review, quality gates, ship readiness |

### Skills (15 from awesome-opencode + 11 MyFarmAI-specific)

All 15 awesome-opencode skills installed in `.opencode/skills/`:

| Skill | Purpose | MyFarmAI Usage |
|-------|---------|----------------|
| adr-write | Architecture Decision Records | Architecture decisions |
| api-contract | OpenAPI/AsyncAPI spec generation | API contracts |
| changelog-generate | CHANGELOG from git history | Release notes |
| ci-pipeline | CI/CD config generation | GitHub Actions/GitLab CI |
| dependency-audit | CVE scan, license check | Dependency security |
| deploy | CI/CD pipeline setup | Deployment configs |
| docker-optimize | Dockerfile multi-stage, hardening | Container optimization |
| env-setup | Developer environment bootstrap | Onboarding |
| error-triage | Stack trace parsing | Debugging |
| git-release | Release notes, version bumps | Releases |
| incident-postmortem | Blameless postmortems | Incident response |
| migration | DB/framework migration | Database changes |
| performance-profile | Hotspot analysis | Performance tuning |
| pr-review | Structured PR review | Code review |
| test-patterns | Test generation | Testing conventions |

MyFarmAI-specific skills (in `.opencode/skills/`):
- `myfarmai-compose-review` - Docker Compose review
- `graphify` - Codebase knowledge graph
- `design` / `design-system` / `ui-styling` / `ui-ux-pro-max` - Design system
- `banner-design` / `brand` / `slides` - Visual assets
- `docker-reviewer` - Docker security review

### Skill Packs (Available but not installed)

| Pack | Contents | Status |
|------|----------|--------|
| design | 10+ design skills, taste skills, playwright-cli | Available via `npx @weisser-dev/awesome-opencode packs --pack design` |
| process | 23 engineering lifecycle skills + commands | Available via `npx @weisser-dev/awesome-opencode packs --pack process` |
| behavior | ponytail minimal-code mode | Available via `npx @weisser-dev/awesome-opencode packs --pack behavior` |

**Recommendation:** Install `design` and `process` packs for enhanced frontend and engineering workflows.

---

## Configuration Changes

### opencode.json (Updated)

The MyFarmAI `opencode.json` was already configured with:
- 108 awesome-opencode agents + 7 custom agents
- 15 awesome-opencode skills
- Compound Engineering plugin
- Ollama models (qwen2.5-coder:3b primary, qwen3:0.6b small)
- 10 MCP servers (3 active, 7 disabled)

### Agent Permissions

The `myfarmai-orchestrator` has explicit delegation permissions:
```json
"permission": {
  "task": {
    "*": "deny",
    "myfarmai-*": "allow",
    "backend-engineer": "allow",
    "frontend-engineer": "allow",
    "android-engineer": "allow",
    "ai-ml-engineer": "allow",
    "research-engineer": "allow",
    "security-engineer": "allow",
    "qa-reviewer": "allow",
    "release-coordinator": "allow",
    "explore": "allow"
  }
}
```

### Model Configuration

- **Primary:** `ollama/qwen2.5-coder:3b` (local, coding-optimized)
- **Small:** `ollama/qwen3:0.6b` (fast, for exploration/docs)

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MyFarmAI Project                        │
├─────────────────────────────────────────────────────────────┤
│  opencode.json  ←  Central configuration                    │
├─────────────────────────────────────────────────────────────┤
│  .opencode/                                                 │
│  ├── agents/          115 agents (108 awesome + 7 custom)  │
│  ├── skills/          26 skills (15 awesome + 11 custom)   │
│  ├── advanced.json    State                                 │
│  └── commands/        (from skill packs)                   │
├─────────────────────────────────────────────────────────────┤
│  ~/.config/opencode/  (global)                              │
│  ├── skills/          80+ gstack skills                     │
│  └── opencode.json    Global config                         │
├─────────────────────────────────────────────────────────────┤
│  Plugins                                                     │
│  └── compound-engineering  @git+https://github.com/...     │
├─────────────────────────────────────────────────────────────┤
│  MCP Servers                                                 │
│  ├── gh-grep        ✅ Code search                           │
│  ├── sentry         ✅ Error monitoring                      │
│  ├── atlassian      ✅ Jira/Confluence                       │
│  └── (7 disabled)   ⚠️ Require credentials                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Collaboration Model

### Current State (Native OpenCode)
- **Primary agent:** `myfarmai-orchestrator` (mode: primary)
- **Subagents:** 7 custom specialists (mode: subagent)
- **Delegation:** Via `@agent-name` syntax in prompts
- **Depth:** `subagent_depth: 2` (orchestrator → specialist → sub-subagent)
- **Compaction:** Auto with pruning

### Awesome-OpenCode CLI Role
- **One-time setup tool** - already run on 2026-10-21
- **Reconfiguration** - available via `npx @weisser-dev/awesome-opencode configure`
- **Skill pack installation** - available via `npx @weisser-dev/awesome-opencode packs`
- **Not a runtime component** - does not run during agent execution

### Compound Engineering Plugin
- Provides: `ce-*` skills (plan, work, debug, commit, review, etc.)
- Provides: `gstack-*` skills (qa, review, ship, design, etc.)
- Provides: `team_*` tools for multi-agent teams
- **Active and integrated** via plugin configuration

---

## Validation Evidence

### Configuration Validation ✅
- OpenCode loads without errors
- All 115 agents discoverable
- All 26 skills discoverable
- MCP servers connect (3 active)
- Compound Engineering plugin loads

### Resource Discovery ✅
- Agents visible in `.opencode/agents/`
- Skills visible in `.opencode/skills/`
- Custom MyFarmAI agents present
- gstack skills available globally

### Delegation Test (Pending - see AGENT_TEAM_VALIDATION.md)

---

## Remaining Limitations

1. **No automatic parallel execution** - requires explicit orchestration
2. **No built-in task queue** - tasks managed via orchestrator prompts
3. **MCP servers need credentials** - 7/10 disabled awaiting config
4. **Skill packs not installed** - design/process packs available but not applied
5. **Model optimization** - could use awesome-opencode's agent-tier model mapping

---

## Next Steps

1. Install `design` and `process` skill packs
2. Configure disabled MCP servers (postgres, redis, linear, etc.)
3. Run delegation validation tests
4. Apply agent-tier model mapping (frontier/strong/fast)
5. Document any custom agent modifications

---

## References

- [awesome-opencode README](/data/MyFarmAI/resources/opencode/awesome-opencode/README.md)
- [awesome-opencode AGENTS.md](/data/MyFarmAI/resources/opencode/awesome-opencode/AGENTS.md)
- [MyFarmAI opencode.json](/data/MyFarmAI/opencode.json)
- [Agent Skill Routing Matrix](./AGENT_SKILL_ROUTING_MATRIX.md)
- [Agent Team Architecture](./AGENT_TEAM_ARCHITECTURE.md)
- [Agent Team Validation](./AGENT_TEAM_VALIDATION.md)