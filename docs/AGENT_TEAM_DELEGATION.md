# MyFarmAI Agent Team — Delegation & Handoff Protocol

## Overview

This document defines how the MyFarmAI Orchestrator delegates work to specialist agents, how handoffs are structured, and how parallelization and verification work.

## Agent Roster

| Agent | Mode | Purpose | Invocation |
|-------|------|---------|------------|
| `myfarmai-orchestrator` | Primary | Coordination, roadmap tracking, delegation | Default agent (Tab to switch) |
| `backend-engineer` | Subagent | FastAPI, SQLAlchemy, PostgreSQL, auth, migrations, tests | `@backend-engineer` |
| `frontend-engineer` | Subagent | Next.js, React, Tailwind, accessibility, API integration | `@frontend-engineer` |
| `android-engineer` | Subagent | Expo/React Native, API base URL, microphone/audio, builds | `@android-engineer` |
| `ai-ml-engineer` | Subagent | Ollama gateway, Qwen models, PersonaPlex feasibility, benchmarks | `@ai-ml-engineer` |
| `research-engineer` | Subagent | SearXNG, web search, extraction, citations, SSRF protection | `@research-engineer` |
| `security-engineer` | Subagent (read-only) | Auth audits, secrets, API/upload security, threat modeling | `@security-engineer` |
| `qa-reviewer` | Subagent (test execution) | Unit/integration tests, API contracts, regression, build checks | `@qa-reviewer` |
| `release-coordinator` | Subagent (read-only) | Diff review, quality-gate execution, documentation-impact check, ship-readiness report | `@release-coordinator` |
| `explore` | Built-in subagent | Read-only codebase exploration | `@explore` |

## Delegation Workflow

### 1. Orchestrator Reads Roadmap
- Reads `docs/roadmaps/MyFarmAI_Backend_Roadmap.md` and `docs/roadmaps/MyFarmAI_Frontend_Dashboard_Roadmap.md`
- Identifies current phase and eligible tasks (respecting hard gates)
- Checks Phase 0 audit findings for context

### 2. Task Decomposition
For each eligible task, the orchestrator creates a **Task Card**:

```markdown
## Task MF-<phase>-<seq>: <Title>

**Objective**: <One-sentence goal>

**Agent**: @<agent-name>

**Files/Components**:
- Primary: <file patterns>
- Related: <file patterns>

**Dependencies**:
- Task MF-<phase>-<seq> (must complete first)
- External: <service, API, approval>

**Constraints** (from Phase 0):
- <Hardware, licensing, security findings>

**Acceptance Criteria**:
- [ ] Specific, verifiable outcome 1
- [ ] Specific, verifiable outcome 2

**Verification Commands**:
```bash
<commands the agent must run and pass>
```

**Expected Output**:
- Files changed
- Test results
- Documentation updates
```

### 3. Delegation
Orchestrator invokes the specialist agent with the Task Card:
```
@backend-engineer Implement Task MF-01-03: Add JWT authentication middleware per AUTH_ASSESSMENT.md
```

### 4. Specialist Execution
- Specialist reads relevant files first (exploration)
- Implements changes within their file scope
- Runs verification commands
- Reports results with evidence

### 5. Security Gate (if applicable)
For security-sensitive changes (auth, uploads, secrets, crypto, PII):
```
@security-engineer Review Task MF-01-03 implementation
```
Security engineer reports findings. Implementation agent fixes. Security re-reviews.

### 6. Quality Gate
```
@qa-reviewer Verify Task MF-01-03
```
QA runs full verification suite. Reports pass/fail with evidence.

### 7. Integration
Orchestrator:
- Resolves any conflicts
- Updates documentation (`CHANGELOG.md`, relevant docs)
- Advances to next eligible task
- Records completion in roadmap tracking

## Handoff Protocol

Every handoff (orchestrator → specialist, specialist → security/QA, specialist → orchestrator) includes:

| Field | Description |
|-------|-------------|
| **Task ID** | `MF-<phase>-<seq>` |
| **Objective** | One-sentence goal |
| **Files/Components** | Specific files, directories, or components |
| **Dependencies** | Other tasks, external services, approvals |
| **Constraints** | Hardware, licensing, Phase 0 findings, API stability |
| **Expected Output** | Files changed, tests added, docs updated |
| **Verification Criteria** | Specific commands + expected results |
| **Findings** | What was discovered during execution |
| **Unresolved Blockers** | Items needing human decision or external input |

## Parallelization Rules

**DO parallelize:**
- Independent backend + frontend tasks (different file trees)
- Research + AI/ML tasks (different domains)
- Exploration tasks (read-only)

**DO NOT parallelize:**
- Tasks writing to same files
- Tasks modifying same database schema
- Tasks with declared dependency
- Security review + implementation of same feature (sequential)

## File Ownership

During a task, the assigned agent **owns** their declared files. No other agent should modify those files until the task completes or ownership is explicitly transferred.

| Agent | Primary Ownership |
|-------|-------------------|
| backend-engineer | `backend/app/**`, `backend/tests/**`, `backend/alembic/**` |
| frontend-engineer | `web/src/**`, `web/styles/**`, `web/*.config.js` |
| android-engineer | `android/src/**`, `android/*.json`, `android/*.config.js` |
| ai-ml-engineer | `backend/app/services/ollama.py`, `backend/app/services/chat.py` |
| research-engineer | `backend/app/services/research*.py`, `infra/searxng/**` |
| security-engineer | Review only — no ownership |
| qa-reviewer | Test files only — `**/*.test.*`, `**/*.spec.*`, Playwright config |

## Phase Gates (from Roadmaps)

### Backend (MyFarmAI_Backend_Roadmap.md)
- Phase 0: Audit complete, approval recorded → **Phase 1 start**
- Phase 1: FastAPI foundation, health, errors, tests, CI baseline
- Phase 2: PostgreSQL, Alembic, migration tested on disposable copy
- Phase 3: Auth, sessions, authorization, privacy controls
- Phase 4: Ollama gateway, bounded inference, evaluations
- Phase 5: Agriculture integrations, licensed data adapters
- Phase 6: Research engine, search, citations, prompt-injection defense
- Phase 7: Background jobs, vector search (only if measured need)
- Phase 8: Deployment hardening, TLS, backups, runbooks
- Phase 9: CI, release gates, recovery validation

### Frontend (MyFarmAI_Frontend_Dashboard_Roadmap.md)
- Phase 0: Repository audit, baseline checks
- Phase 1: TypeScript baseline repair
- Phase 2: Design system finalized
- Phase 3: Responsive application shell
- Phase 4: Home dashboard components
- Phase 5: Weather experience
- Phase 6: AI assistant integration
- Phase 7: Navigation and quick tools
- Phase 8: Accessibility/responsiveness
- Phase 9: Browser QA
- Phase 10: Security/performance review
- Phase 11: Final build/documentation

## Verification Before Phase Completion

Before declaring any phase complete:

1. **Run all relevant tests** (backend, frontend, android as applicable)
2. **Inspect Git diff** — no accidental changes
3. **Confirm no secrets/model weights in Git**
4. **Update documentation** — CHANGELOG, architecture, API docs, roadmaps
5. **Record evidence** — command output, screenshots, test results
6. **Report unresolved issues honestly**

## Escalation

If a specialist encounters:
- **Scope creep** → Return to orchestrator for re-scoping
- **Blocking dependency** → Orchestrator resolves or reorders
- **Security concern** → Immediate `@security-engineer` review
- **Test failure not caused by change** → `@qa-reviewer` investigates
- **Architecture decision needed** → Orchestrator documents ADR

## Example Delegation Sequence

```
1. @myfarmai-orchestrator: "Start Phase 1 backend foundation"
2. @myfarmai-orchestrator creates Task MF-01-01: "Reproducible FastAPI app with settings, health, errors"
3. @backend-engineer implements, runs pytest/ruff/mypy
4. @security-engineer reviews error handling, logging (no secrets)
5. @qa-reviewer verifies full backend suite passes
6. @myfarmai-orchestrator updates docs, creates Task MF-01-02
7. Repeat...
```