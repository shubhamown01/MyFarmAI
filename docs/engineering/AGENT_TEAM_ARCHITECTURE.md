# Agent Team Architecture

**Project:** MyFarmAI  
**Date:** 2026-10-25  
**Orchestrator:** myfarmai-orchestrator (primary)

---

## Team Structure

```
┌────────────────────────────────────────────────────────────────┐
│                    MYFARMAI ORCHESTRATOR                       │
│  (myfarmai-orchestrator - primary agent)                       │
│  - Reads roadmaps & governance                                 │
│  - Decomposes tasks                                            │
│  - Delegates to specialists                                    │
│  - Integrates results                                          │
│  - Enforces gates (security, quality, docs)                    │
└────────────────────────┬───────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│  BACKEND      │ │  FRONTEND     │ │  ANDROID      │
│  ENGINEER     │ │  ENGINEER     │ │  ENGINEER     │
│               │ │               │ │               │
│ FastAPI       │ │ Next.js 14+   │ │ Expo/React    │
│ SQLAlchemy    │ │ React 18+     │ │ Native        │
│ PostgreSQL    │ │ Tailwind CSS  │ │ Microphone    │
│ Auth/JWT      │ │ Accessibility │ │ Audio         │
│ Migrations    │ │ API Integration│ │ Builds        │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
┌────────────────────────────────────────────────────────────────┐
│                    AI/ML & RESEARCH LAYER                      │
├────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐         ┌──────────────────────┐    │
│  │   AI-ML ENGINEER     │         │  RESEARCH ENGINEER   │    │
│  │                      │         │                      │    │
│  │ Ollama Gateway       │         │ SearXNG Integration  │    │
│  │ Qwen Models          │         │ Web Search           │    │
│  │ PersonaPlex          │         │ Source Extraction    │    │
│  │ Model Storage        │         │ Citations            │    │
│  │ Inference Tuning     │         │ SSRF Protection      │    │
│  └──────────────────────┘         └──────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│                    QUALITY & SECURITY GATES                    │
├────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐         ┌──────────────────────┐    │
│  │   SECURITY ENGINEER  │         │    QA REVIEWER       │    │
│  │                      │         │                      │    │
│  │ Auth Audits          │         │ Unit/Integration     │    │
│  │ Secret Protection    │         │ API Contract Checks  │    │
│  │ API/Upload Security  │         │ Regression Testing   │    │
│  │ Threat Modeling      │         │ Build Verification   │    │
│  │ Dependency Scanning  │         │ Browser QA           │    │
│  └──────────────────────┘         └──────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│                    RELEASE COORDINATOR                         │
│  - Read-only diff review                                       │
│  - Quality gate execution                                      │
│  - Documentation impact check                                  │
│  - Ship-readiness report                                       │
└────────────────────────────────────────────────────────────────┘
```

---

## Agent Definitions

### Primary Orchestrator

| Property | Value |
|----------|-------|
| Agent ID | `myfarmai-orchestrator` |
| Mode | `primary` |
| Steps | 20 |
| Model | `ollama/qwen2.5-coder:3b` |
| Temperature | 0.2 |
| Permissions | Full edit/bash, task delegation to 7 specialists + explore |

**Responsibilities:**
- Roadmap execution (backend + frontend roadmaps)
- Task decomposition with MF-<phase>-<seq> IDs
- Specialist delegation with handoff protocol
- Conflict prevention (file ownership tracking)
- Security gate enforcement
- Quality gate enforcement
- Documentation compliance

### Specialist Agents (Subagents)

#### Backend Engineer
| Property | Value |
|----------|-------|
| Agent ID | `backend-engineer` |
| Mode | `subagent` |
| Steps | 15 |
| Base Template | `fastapi-developer` + `backend-developer` |
| Key Skills | `api-contract`, `test-patterns`, `migration`, `docker-optimize` |
| MCP Tools | filesystem, git, gh-grep |

**Domain:** FastAPI, SQLAlchemy, PostgreSQL, authentication, migrations, tests

#### Frontend Engineer
| Property | Value |
|----------|-------|
| Agent ID | `frontend-engineer` |
| Mode | `subagent` |
| Steps | 15 |
| Base Template | `nextjs-developer` + `frontend-developer` |
| Key Skills | `test-patterns`, `ui-styling`, `ui-ux-pro-max`, `design-system` |
| MCP Tools | filesystem, git, playwright, gh-grep |

**Domain:** Next.js, React, Tailwind, accessibility, API integration, responsive design

#### Android Engineer
| Property | Value |
|----------|-------|
| Agent ID | `android-engineer` |
| Mode | `subagent` |
| Steps | 15 |
| Base Template | `mobile-developer` + `flutter-expert` |
| Key Skills | `test-patterns`, `env-setup`, `docker-optimize` |
| MCP Tools | filesystem, git, gh-grep |

**Domain:** Expo/React Native, API base URL, microphone/audio, auth, builds

#### AI/ML Engineer
| Property | Value |
|----------|-------|
| Agent ID | `ai-ml-engineer` |
| Mode | `subagent` |
| Steps | 15 |
| Base Template | `machine-learning-engineer` + `llm-architect` |
| Key Skills | `docker-optimize`, `env-setup`, `performance-profile`, `dependency-audit` |
| MCP Tools | filesystem, git, gh-grep |

**Domain:** Ollama gateway, Qwen models, PersonaPlex feasibility, model storage

#### Research Engineer
| Property | Value |
|----------|-------|
| Agent ID | `research-engineer` |
| Mode | `subagent` |
| Steps | 15 |
| Base Template | `research-analyst` + `search-specialist` |
| Key Skills | `adr-write`, `error-triage`, `api-contract` |
| MCP Tools | filesystem, git, gh-grep, searxng |

**Domain:** SearXNG, web search, extraction, citations, SSRF protection, agricultural knowledge

#### Security Engineer
| Property | Value |
|----------|-------|
| Agent ID | `security-engineer` |
| Mode | `subagent` |
| Steps | 15 |
| Base Template | `security-engineer` + `penetration-tester` |
| Key Skills | `pr-review`, `dependency-audit`, `incident-postmortem` |
| MCP Tools | filesystem, git, gh-grep |

**Domain:** Auth audits, secret protection, API/upload security, threat modeling

#### QA Reviewer
| Property | Value |
|----------|-------|
| Agent ID | `qa-reviewer` |
| Mode | `subagent` |
| Steps | 15 |
| Base Template | `test-automator` + `code-reviewer` |
| Key Skills | `test-patterns`, `test-automator`, `changelog-generate`, `performance-profile` |
| MCP Tools | filesystem, git, playwright, gh-grep |

**Domain:** Unit/integration tests, API contracts, regression, build checks

#### Release Coordinator
| Property | Value |
|----------|-------|
| Agent ID | `release-coordinator` |
| Mode | `subagent` |
| Steps | 10 |
| Base Template | `git-workflow-manager` + `deployment-engineer` |
| Key Skills | `git-release`, `changelog-generate`, `pr-review`, `ci-pipeline`, `deploy` |
| MCP Tools | filesystem, git, github, gh-grep |

**Domain:** Read-only diff review, quality gates, documentation impact, ship readiness

---

## Supporting Agents (Available for Specific Tasks)

| Agent | Template | Use Case |
|-------|----------|----------|
| architect-reviewer | architect-reviewer | ADR creation, architecture decisions |
| performance-engineer | performance-engineer | Performance bottlenecks |
| dependency-manager | dependency-manager | Dependency audits |
| code-reviewer | code-reviewer | Code quality reviews |
| devops-engineer | devops-engineer | CI/CD pipelines |
| test-automator | test-automator | Test framework design |
| penetration-tester | penetration-tester | Security testing |
| debugger | debugger | Root cause analysis |
| docker-expert | docker-expert | Container optimization |
| api-designer | api-designer | API schema design |

---

## Collaboration Flow

### 1. Task Reception
```
User Request → myfarmai-orchestrator
```

### 2. Task Analysis
```
Orchestrator reads:
- Relevant roadmap (backend/frontend)
- Phase 0 audit findings
- Current Git status
- Affected documentation
```

### 3. Task Decomposition
```
Creates task checklist with:
- Task ID (MF-<phase>-<seq>)
- Objective
- Files/components
- Dependencies
- Constraints
- Verification criteria
```

### 4. Specialist Assignment
```
For each independent task:
- Select appropriate specialist
- Verify no file ownership conflicts
- Delegate with full handoff context
```

### 5. Parallel Execution (Read-Only)
```
Independent investigations → Run in parallel via @agent invocations
```

### 6. Sequential Execution (Write)
```
Dependent/write tasks → Run sequentially with verification between
```

### 7. Result Collection
```
Specialist returns:
- Findings
- Implementation summary
- Test evidence
- Blockers
```

### 8. Integration & Review
```
Orchestrator:
- Reviews conflicts
- Runs security gate (if needed)
- Runs quality gate (mandatory)
- Updates documentation
```

### 9. Verification
```
- Run relevant test suites
- Inspect Git diff
- Check for secrets
- Update CHANGELOG.md
```

### 10. Completion Report
```
Reports:
- Task status (PASS/FAIL/BLOCKED)
- Evidence
- Unresolved issues
- Next authorized steps
```

---

## Communication Protocols

### Orchestrator → Specialist
- Uses `@agent-name` syntax
- Provides complete handoff protocol (Task ID, objective, files, deps, constraints, verification)
- Sets clear expectations for output format

### Specialist → Orchestrator
- Returns structured findings
- Includes test commands and results
- Lists any blockers or deviations
- Does NOT delegate to other specialists

### Cross-Specialist
- NOT permitted directly
- Must go through orchestrator
- Orchestrator manages dependencies and ordering

---

## Gate Enforcement

### Security Gate (Mandatory)
- Triggered by: auth changes, secret handling, API exposure, upload handling, dependency changes
- Reviewer: `security-engineer` (read-only)
- Criteria: No critical vulnerabilities, secrets rotated, threat model updated

### Quality Gate (Mandatory)
- Triggered by: ALL implementations
- Reviewer: `qa-reviewer` (read-only + test execution)
- Criteria: Tests pass, coverage maintained, no regressions, builds pass

### Documentation Gate (Mandatory)
- Triggered by: ANY material change
- Reviewer: `release-coordinator` (read-only)
- Criteria: Docs match implementation, CHANGELOG updated, no drift

### Release Gate (At Ship Time)
- Triggered by: `release-coordinator` before merge
- Reviewer: `release-coordinator` (read-only diff review)
- Criteria: All gates PASS, diff clean, version bumped, ship report generated

---

## Resource Constraints

| Resource | Limit | Notes |
|----------|-------|-------|
| Host RAM | 7 GiB | Shared across all processes |
| VRAM | 2 GiB | For Ollama models |
| Disk (/) | ~5 GB free | SSD - prefer /data for large files |
| Subagent Depth | 2 | Orchestrator → Specialist → (optional) |
| Concurrency | 2-3 specialists | Avoid OOM on host |

---

## Escalation Path

```
Specialist blocked
       │
       ▼
Orchestrator reviews
       │
       ├──► Re-assign to different specialist
       ├──► Break into smaller tasks
       ├──► Escalate to supporting agent (architect-reviewer, debugger, etc.)
       └──► Request human decision (governance gate)
```

---

## Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| opencode.json | `/data/MyFarmAI/opencode.json` | Main config: agents, MCP, models, plugins |
| myfarmai-orchestrator.md | `.opencode/agents/` | Orchestrator prompt & permissions |
| backend-engineer.md | `.opencode/agents/` | Backend specialist config |
| frontend-engineer.md | `.opencode/agents/` | Frontend specialist config |
| android-engineer.md | `.opencode/agents/` | Android specialist config |
| ai-ml-engineer.md | `.opencode/agents/` | AI/ML specialist config |
| research-engineer.md | `.opencode/agents/` | Research specialist config |
| security-engineer.md | `.opencode/agents/` | Security specialist config |
| qa-reviewer.md | `.opencode/agents/` | QA specialist config |
| release-coordinator.md | `.opencode/agents/` | Release specialist config |

---

## Skill Availability

### Project Skills (`.opencode/skills/`)
- All 15 awesome-opencode skills ✅
- 11 MyFarmAI-specific skills ✅

### Global Skills (`~/.config/opencode/skills/`)
- 80+ gstack skills ✅
- project-maintenance, task-checklist-execution ✅

### Skill Packs (Available via CLI)
- `design` pack - 10+ design skills
- `process` pack - 23 engineering skills + commands
- `behavior` pack - ponytail mode (opt-in)

---

## Model Strategy

| Tier | Model | Use Case |
|------|-------|----------|
| Primary (Frontier) | `ollama/qwen2.5-coder:3b` | Code writing, complex reasoning |
| Small (Fast) | `ollama/qwen3:0.6b` | Exploration, docs, context mgmt |

**Future:** Apply awesome-opencode agent-tier mapping:
- Frontier: code-writing agents, language specialists
- Strong: code review, architecture, security
- Fast: exploration, docs, context management

---

## Maintenance

### Regular Tasks
- Weekly: Run `gstack-retro` for engineering retrospective
- Per Release: Run `release-coordinator` quality gates
- Per Sprint: Review agent performance, update prompts
- Quarterly: Re-run awesome-opencode CLI for updates

### Upgrade Path
1. Pull latest awesome-opencode
2. Run `npx @weisser-dev/awesome-opencode configure` 
3. Review diff in generated files
4. Preserve MyFarmAI customizations
5. Test delegation flow
6. Update documentation

---

## References

- [Awesome-OpenCode Integration](./AWESOME_OPENCODE_INTEGRATION.md)
- [Agent Skill Routing Matrix](./AGENT_SKILL_ROUTING_MATRIX.md)
- [Agent Team Validation](./AGENT_TEAM_VALIDATION.md)
- [MyFarmAI Orchestrator Prompt](../.opencode/agents/myfarmai-orchestrator.md)
- [Phase 0 Audit Findings](../REPOSITORY_AUDIT.md)