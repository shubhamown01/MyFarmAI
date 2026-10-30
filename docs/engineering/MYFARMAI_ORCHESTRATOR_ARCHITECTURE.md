# MyFarmAI Orchestrator Architecture

**Document Version:** 1.0  
**Status:** Implemented  
**Date:** 2026-10-25  
**Component:** MyFarmAI-Orchestrator  

---

## 1. Overview

The MyFarmAI Orchestrator is an advanced, project-aware orchestration system that coordinates the existing OpenCode environment, specialist agents, subagents, skills, plugins, MCP servers, CLI tools, development software, testing infrastructure, and documentation.

It manages the complete engineering lifecycle: **Discover → Plan → Build Team → Assign → Execute → Integrate → Test → Secure → Document → Report**

---

## 2. Architecture Principles

| Principle | Implementation |
|-----------|----------------|
| **OpenCode-Native** | No new runtime; works within existing OpenCode session model |
| **Reuse First** | Leverages 57 existing agents, 26 skills, compound-engineering plugin |
| **Graphify-Aware** | Uses knowledge graph for project context |
| **Document-First** | Every code change updates documentation |
| **HDD-First Storage** | Core logic in `/data/MyFarmAI` (HDD-backed) |
| **Permission Gates** | 4-tier approval system for software changes |
| **Evidence-Based** | Verification requires actual command output |
| **Resumable** | Checkpoint-based execution with retry/backoff |

---

## 3. Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MyFarmAI Orchestrator                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐     │
│  │  Capability      │    │  Dynamic Team    │    │  Skill/Tool      │     │
│  │  Registry        │◄───│  Builder         │◄───│  Router          │     │
│  │  (registry.py)   │    │  (team_builder)  │    │  (router.py)     │     │
│  └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘     │
│           │                       │                       │               │
│           ▼                       ▼                       ▼               │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │                    Orchestrator Core (core.py)                    │    │
│  │  Task Graph │ Delegation │ Progress │ Resources │ File Ownership │    │
│  └────────────────────────────┬─────────────────────────────────────┘    │
│                               │                                          │
│           ┌───────────────────┼───────────────────┐                     │
│           ▼                   ▼                   ▼                     │
│  ┌──────────────────┐ ┌───────────────┐ ┌──────────────────┐           │
│  │ Execution Manager│ │ Integration   │ │ Verification     │           │
│  │ (execution.py)   │ │ Review Manager│ │ Security Gate    │           │
│  └────────┬─────────┘ └───────┬───────┘ └────────┬─────────┘           │
│           │                   │                   │                     │
│           ▼                   ▼                   ▼                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                  Project Memory (memory.py)                       │  │
│  │  Decisions │ History │ Capability Snapshots │ Learnings │ Audit  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    OpenCode Runtime Environment                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐   │
│  │  Agents  │ │ Skills   │ │ Plugins  │ │ MCPs     │ │ CLI Tools  │   │
│  │  (57)    │ │ (26)     │ │ (1)      │ │ (8)      │ │ (50+)      │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Core Components

### 4.1 CapabilityRegistry (`registry.py`)

**Purpose:** Discovers, catalogs, and validates all available capabilities.

**Discovery Sources:**
- `.opencode/agents/*.md` → 57 agent definitions
- `.opencode/skills/*/SKILL.md` → 26 skill manifests
- `opencode.json` → plugins, MCP servers, model config
- `backend/pyproject.toml` / `requirements.txt` → Python dependencies
- `web/package.json` → npm dependencies (web)
- `android/package.json` → npm dependencies (android)
- System PATH → CLI tools (docker, git, uv, node, etc.)
- `ollama list` → Available models
- Test framework configs → pytest, vitest, playwright, etc.

**Key Features:**
- Status lifecycle: INSTALLED → CONFIGURED → AUTHENTICATED → AVAILABLE → VERIFIED_WORKING
- Validation commands per capability type
- Conflict detection (duplicates, version mismatches, permission overlaps)
- Tier 2 allowlist for auto-installation
- Export for documentation/reporting

### 4.2 OrchestratorCore (`core.py`)

**Purpose:** Main orchestration engine managing task lifecycle.

**Key Features:**
- Task graph with dependency management (DAG)
- Resource budgeting (agents, models, docker builds, test slots)
- File ownership tracking to prevent conflicts
- Parallel group detection for independent tasks
- Session persistence with run IDs
- Status tracking: PLANNED → READY → RUNNING → BLOCKED → REVIEW → PASSED/FAILED/CANCELLED

**Resource Budgets (from Phase 0 hardware):**
- Max parallel agents: 4 (CPU cores)
- Max concurrent models: 1 (2 GiB VRAM constraint)
- Max concurrent docker builds: 1 (disk I/O constraint)
- Max concurrent test runs: 2 (RAM constraint)

### 4.3 DynamicTeamBuilder (`team_builder.py`)

**Purpose:** Selects smallest effective team for each task.

**Algorithm:**
1. Infer required capabilities from task (objective, constraints, files)
2. Query registry for matching agents
3. Score candidates: capability_match(0.4) + availability(0.3) + load(0.2) + specialization(0.1)
4. Assign single accountable owner per task
5. Build parallel groups via topological sort
6. Apply concurrency limits

**Prevents:**
- Recursive delegation loops (max depth 3)
- Overloaded agents (max 3 concurrent tasks)
- Unauthorized new agent creation (Tier 3 gate)

### 4.4 SkillToolRouter (`router.py`)

**Purpose:** Routes tasks to appropriate capabilities using priority rules.

**Routing Priority:**
1. Existing Skill (exact task type match)
2. Existing Agent + Skill (agent with relevant skill loaded)
3. Existing Agent Only (built-in capability)
4. MCP Tool (direct MCP server call)
5. CLI Tool (installed command-line tool)
6. New Skill Creation (only if Tier 3 approved)

**Routing Rules (12 defined):**
| Rule | Patterns | Primary Agent | Primary Skill | Tier |
|------|----------|---------------|---------------|------|
| backend_api | api, endpoint, fastapi | backend-engineer | api-contract | 1 |
| backend_database | database, sql, migration | database-administrator | migration | 1 |
| frontend_component | component, ui, react, tailwind | frontend-engineer | shadcn | 1 |
| android_feature | android, mobile, expo | android-engineer | vercel-react-native-skills | 1 |
| ai_ml_integration | model, ollama, qwen | ai-ml-engineer | google-agents-cli-adk-code | 1 |
| research_engine | research, search, searxng | research-engineer | searxng | 1 |
| security_audit | security, auth, vulnerability | security-engineer | gstack-cso | 3 |
| qa_testing | test, qa, lint, typecheck | qa-reviewer | test-patterns | 1 |
| deployment | deploy, docker, ci, cd | deployment-engineer | deploy-to-vercel | 3 |
| documentation | doc, readme, documentation | docs-writer | document-generate | 1 |
| architecture | architecture, design, adr | architect-reviewer | adr-write | 1 |
| debugging | debug, error, fix, bug | debugger | ce-debug | 1 |
| performance | performance, optimize, latency | performance-engineer | performance-profile | 1 |

### 4.5 ExecutionManager (`execution.py`)

**Purpose:** Manages task execution with checkpoints, retries, and isolation.

**Execution Phases:**
1. **PREPARING** - Verify dependencies, check resources, create worktree
2. **DELEGATING** - Build handoff, create agent assignment, track agent
3. **EXECUTING** - Run delegation, capture outputs
4. **VERIFYING** - Run verification gate
5. **INTEGRATING** - Merge worktree, resolve conflicts
6. **COMPLETING** - Finalize, release resources, record history

**Features:**
- Git worktree isolation for file modifications
- Checkpoint/resume via JSON files (`.orchestrator/checkpoints/`)
- Exponential backoff retry (max 3, base 2s, max 60s)
- Resource slot acquisition/release
- Phase-based error handling

### 4.6 IntegrationReviewManager (`integration.py`)

**Purpose:** Detects and resolves integration conflicts.

**Conflict Types Detected:**
- FILE_OVERLAP - Multiple tasks modifying same file
- API_CONTRACT - Breaking API changes
- DATABASE_SCHEMA - Conflicting migrations
- CONFIGURATION - Conflicting config changes
- RESOURCE_CONTENTION - Competing for exclusive resources

**Severity Levels:** INFO, WARNING, ERROR, BLOCKING

**Auto-Resolution:** Attempted for resolvable conflicts (different file sections, different config keys)

**Review Queue:** Security-sensitive, API, and database changes require independent review

### 4.7 VerificationSecurityGate (`verification.py`)

**Purpose:** Enforces quality and security standards with evidence.

**22 Standard Checks:**

| Category | Checks |
|----------|--------|
| Quality (10) | backend_tests, backend_typecheck, backend_lint, backend_format, frontend_typecheck, frontend_tests, frontend_lint, frontend_build, android_typecheck, android_lint |
| Security (4) | secret_scan, dependency_audit_python, dependency_audit_web, dependency_audit_android |
| Contract (1) | openapi_diff |
| Build (2) | docker_compose_config, dockerfile_syntax |
| Dependency (1) | uv_lock_check |

**Security Review Trigger Patterns:**
- auth, secret, password, token, credential
- security, vulnerability, encryption, tls, ssl
- permission, authorization, rbac, oauth

### 4.8 ProjectMemoryManager (`memory.py`)

**Purpose:** Durable project memory with audit trail.

**Storage (`.orchestrator/memory/`):**
- `decisions.json` - ADR-style decision records
- `history.jsonl` - Task execution history (append-only)
- `capabilities.json` - Capability snapshots
- `learnings.json` - Captured learnings (ce-compound compatible)
- `metadata.json` - Summary statistics

**Features:**
- Decision lifecycle: PROPOSED → APPROVED/REJECTED/SUPERSEDED
- Failure pattern analysis (recurring errors)
- Agent performance metrics
- Audit report generation
- Retention policy (90 days default)

---

## 5. Data Flow

```
User Request
     │
     ▼
┌─────────────────────────────────────┐
│  Objective Analysis                 │
│  (myfarmai-task-decompose skill)    │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Task Decomposition                 │
│  → Task[] with dependencies         │
│  → Required capabilities            │
│  → Resource estimates               │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Team Building                      │
│  (DynamicTeamBuilder)               │
│  → AgentAssignment[]                │
│  → Parallel groups                  │
│  → Execution order                  │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Execution Loop                     │
│  (ExecutionManager)                 │
│  For each parallel group:           │
│    For each task:                   │
│      → Prepare (deps, resources)    │
│      → Delegate (handoff)           │
│      → Execute (agent)              │
│      → Verify (gate)                │
│      → Integrate (merge)            │
│      → Complete/Block/Retry         │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Completion                         │
│  → Update project memory            │
│  → Generate audit report            │
│  → Clean checkpoints                │
│  → Report results                   │
└─────────────────────────────────────┘
```

---

## 6. Permission Model

### Tier 1 - Existing Trusted Tools (Auto-use)
- All 57 configured agents
- All 26 installed skills
- Compound-engineering plugin
- Configured MCP servers (gh-grep, sentry, atlassian)
- Installed CLI tools (docker, git, uv, node, etc.)

### Tier 2 - Reversible, Low-Risk (Allowlisted Auto-install)
- Linting: ruff, mypy, eslint, prettier
- Testing: pytest, vitest, playwright
- Security: gitleaks, trivy, osv-scanner, pip-audit, npm audit
- Build: hadolint, shellcheck
- **Allowlist configurable** via registry

### Tier 3 - New Capabilities (Explicit Approval)
- New agent definitions
- New skill creation
- New MCP server connections
- New plugin installations
- **Requires:** Explicit user approval with rationale

### Tier 4 - Destructive/High-Impact (Explicit Authorization + Safeguards)
- Database migrations
- Secret rotation
- Production deployment
- Volume deletion
- Destructive Docker commands
- **Requires:** Explicit authorization, impact explanation, rollback plan

---

## 7. Integration Points

### Compound Engineering Plugin
Uses existing CE skills:
- `ce-plan` - Structured plan creation
- `ce-work` - Plan execution
- `ce-debug` - Failure diagnosis
- `ce-commit-push-pr` - Shipping changes
- `ce-code-review` - Diff review
- `ce-doc-review` - Documentation review
- `ce-handoff` - Session continuity
- `ce-compound` - Learning capture

### Graphify Knowledge Graph
- Project context queries via `graphify query`
- Architecture decision lookup
- Code relationship analysis
- Auto-update on file changes

### OpenCode Session Model
- One orchestration run = one OpenCode session
- Subagents via `subagent` tool (background for parallel)
- Team tools for complex multi-agent work
- `ce-handoff` for session persistence

---

## 8. File Structure

```
/data/MyFarmAI/
├── backend/app/orchestrator/
│   ├── __init__.py
│   ├── models.py           # Pydantic models
│   ├── registry.py         # CapabilityRegistry
│   ├── core.py             # OrchestratorCore
│   ├── team_builder.py     # DynamicTeamBuilder
│   ├── router.py           # SkillToolRouter
│   ├── execution.py        # ExecutionManager
│   ├── integration.py      # IntegrationReviewManager
│   ├── verification.py     # VerificationSecurityGate
│   └── memory.py           # ProjectMemoryManager
│
├── .opencode/skills/
│   ├── myfarmai-orchestrate/SKILL.md
│   ├── myfarmai-task-decompose/SKILL.md
│   ├── myfarmai-capability-scan/SKILL.md
│   └── myfarmai-verify/SKILL.md
│
├── .orchestrator/
│   ├── checkpoints/        # Execution checkpoints
│   ├── worktrees/          # Git worktrees for isolation
│   ├── memory/             # Project memory (JSON/JSONL)
│   ├── verification/       # Verification evidence
│   ├── cache/              # Capability/verification cache
│   └── logs/               # Execution logs
│
└── docs/engineering/
    ├── MYFARMAI_ORCHESTRATOR_ARCHITECTURE.md
    ├── MYFARMAI_AGENT_TEAM_CATALOG.md
    ├── MYFARMAI_CAPABILITY_REGISTRY.md
    ├── MYFARMAI_SKILL_TOOL_ROUTING.md
    ├── MYFARMAI_EXECUTION_AND_PERMISSION_POLICY.md
    ├── MYFARMAI_ORCHESTRATOR_TEST_REPORT.md
    └── MYFARMAI_ORCHESTRATOR_OPERATIONS.md
```

---

## 9. Non-Functional Requirements

| Requirement | Target | Implementation |
|-------------|--------|----------------|
| Task decomposition accuracy | ≥ 90% | Capability-based inference + validation |
| Agent selection correctness | ≥ 95% | Multi-factor scoring + fallback chains |
| Parallel execution efficiency | ≥ 70% | Dependency DAG + resource budgeting |
| Verification gate pass rate | 100% critical | Evidence-based, no simulation |
| Documentation currency | 100% | Doc-update required in handoff |
| Mean time to recovery | < 5 min | Checkpoint/resume + exponential backoff |
| Capability registry freshness | < 1 hr | Auto-refresh + manual trigger |

---

## 10. Limitations & Known Issues

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| OpenCode API stability | Medium | Abstract delegation layer, version pin |
| No true parallel agent execution | Medium | Sequential with background subagents |
| Graphify stale data risk | Low | Auto-update hooks, manual refresh |
| Worktree merge conflicts | Medium | Pre-flight conflict detection |
| Resource estimation accuracy | Medium | Conservative defaults, monitoring |
| Security review manual | High | Documented process, audit trail |

---

## 11. Future Extensions

1. **True Parallel Agents** - When OpenCode supports native parallel subagents
2. **ML-Based Task Decomposition** - Train on historical task patterns
3. **Advanced Conflict Resolution** - Semantic merge for code conflicts
4. **Predictive Resource Scheduling** - ML-based duration estimation
5. **Multi-Project Orchestration** - Cross-repository dependency management
6. **Visual Dashboard** - Real-time execution monitoring