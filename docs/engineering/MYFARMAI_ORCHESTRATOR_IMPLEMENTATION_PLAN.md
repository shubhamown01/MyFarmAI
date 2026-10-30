# MyFarmAI-Orchestrator Implementation Plan

**Document Version:** 1.0  
**Status:** Draft — For Implementation  
**Date:** 2026-10-25  
**Author:** MyFarmAI Orchestrator  

---

## 1. Overview

This plan describes the implementation of **MyFarmAI-Orchestrator**, an advanced project-aware orchestration system that coordinates the existing OpenCode environment, specialist agents, subagents, skills, plugins, MCP servers, CLI tools, development software, testing infrastructure, and documentation.

The orchestrator manages the complete engineering lifecycle: **Discover → Plan → Build Team → Assign → Execute → Integrate → Test → Secure → Document → Report**

---

## 2. Architecture Decision: Implementation Approach

### Chosen Approach: OpenCode-Native Agent/Skill Extension

After auditing the existing environment, the orchestrator will be implemented as:

1. **Core Orchestration Logic**: Python modules in `/data/MyFarmAI/backend/app/orchestrator/` - reusable by any agent
2. **OpenCode Agent Definitions**: Enhanced agent definitions in `.opencode/agents/` with orchestration capabilities
3. **OpenCode Skills**: New skills in `.opencode/skills/` for orchestration workflows
4. **Integration with Compound Engineering Plugin**: Leverage the already-installed `compound-engineering@git+https://github.com/EveryInc/compound-engineering-plugin.git`
5. **Graphify Integration**: Use the existing knowledge graph at `graphify-out/` for project awareness

### Rationale

- **No new runtime required** - works within existing OpenCode session model
- **Reuses existing 57 agents and 26 skills** - no duplication
- **Leverages compound-engineering plugin** - provides ce-plan, ce-work, ce-debug, ce-commit-push-pr, etc.
- **Graphify-aware** - uses knowledge graph for project context
- **Minimal SSD writes** - core logic in backend (HDD-backed `/data/MyFarmAI`)
- **Document-first** - all changes update docs before/after implementation

---

## 3. Component Architecture

```
MyFarmAI-Orchestrator/
├── backend/app/orchestrator/           # Core Python modules
│   ├── __init__.py
│   ├── core.py                         # OrchestratorCore - task graph, delegation
│   ├── registry.py                     # CapabilityRegistry - agents, skills, tools
│   ├── team_builder.py                 # DynamicTeamBuilder - task→team mapping
│   ├── router.py                       # SkillToolRouter - task→capability matching
│   ├── execution.py                    # ExecutionManager - state tracking
│   ├── integration.py                  # IntegrationReviewManager - conflict detection
│   ├── verification.py                 # VerificationSecurityGate - quality gates
│   ├── memory.py                       # ProjectMemory - audit trail, decisions
│   └── models.py                       # Pydantic models for all components
│
├── .opencode/skills/
│   ├── myfarmai-orchestrate/           # Main orchestration skill
│   ├── myfarmai-task-decompose/        # Task decomposition skill
│   ├── myfarmai-capability-scan/       # Capability discovery skill
│   └── myfarmai-verify/                # Verification gate skill
│
├── .opencode/agents/
│   ├── myfarmai-orchestrator.md        # Enhanced primary agent (existing)
│   ├── myfarmai-architect.md           # Architecture agent
│   ├── myfarmai-integration.md         # Integration reviewer agent
│   └── myfarmai-auditor.md             # Audit/verification agent
│
└── docs/engineering/                   # Required documentation artifacts
    ├── MYFARMAI_ORCHESTRATOR_ARCHITECTURE.md
    ├── MYFARMAI_AGENT_TEAM_CATALOG.md
    ├── MYFARMAI_CAPABILITY_REGISTRY.md
    ├── MYFARMAI_SKILL_TOOL_ROUTING.md
    ├── MYFARMAI_EXECUTION_AND_PERMISSION_POLICY.md
    ├── MYFARMAI_ORCHESTRATOR_TEST_REPORT.md
    └── MYFARMAI_ORCHESTRATOR_OPERATIONS.md
```

---

## 4. Implementation Phases

### Phase A: Foundation (Week 1)
| Task | Description | Deliverable |
|------|-------------|-------------|
| A1 | Create Pydantic models for all orchestration entities | `backend/app/orchestrator/models.py` |
| A2 | Implement CapabilityRegistry with discovery | `backend/app/orchestrator/registry.py` |
| A3 | Implement OrchestratorCore with task graph | `backend/app/orchestrator/core.py` |
| A4 | Write MYFARMAI_CAPABILITY_REGISTRY.md | Documentation artifact |
| A5 | Write MYFARMAI_ORCHESTRATOR_ARCHITECTURE.md | Documentation artifact |

### Phase B: Team Building & Routing (Week 1-2)
| Task | Description | Deliverable |
|------|-------------|-------------|
| B1 | Implement DynamicTeamBuilder | `backend/app/orchestrator/team_builder.py` |
| B2 | Implement SkillToolRouter | `backend/app/orchestrator/router.py` |
| B3 | Create myfarmai-orchestrate skill | `.opencode/skills/myfarmai-orchestrate/` |
| B4 | Create myfarmai-task-decompose skill | `.opencode/skills/myfarmai-task-decompose/` |
| B5 | Write MYFARMAI_AGENT_TEAM_CATALOG.md | Documentation artifact |
| B6 | Write MYFARMAI_SKILL_TOOL_ROUTING.md | Documentation artifact |

### Phase C: Execution & Integration (Week 2)
| Task | Description | Deliverable |
|------|-------------|-------------|
| C1 | Implement ExecutionManager | `backend/app/orchestrator/execution.py` |
| C2 | Implement IntegrationReviewManager | `backend/app/orchestrator/integration.py` |
| C3 | Create myfarmai-capability-scan skill | `.opencode/skills/myfarmai-capability-scan/` |
| C4 | Write MYFARMAI_EXECUTION_AND_PERMISSION_POLICY.md | Documentation artifact |

### Phase D: Verification & Memory (Week 2-3)
| Task | Description | Deliverable |
|------|-------------|-------------|
| D1 | Implement VerificationSecurityGate | `backend/app/orchestrator/verification.py` |
| D2 | Implement ProjectMemory | `backend/app/orchestrator/memory.py` |
| D3 | Create myfarmai-verify skill | `.opencode/skills/myfarmai-verify/` |
| D4 | Write MYFARMAI_ORCHESTRATOR_OPERATIONS.md | Documentation artifact |

### Phase E: Testing & Validation (Week 3)
| Task | Description | Deliverable |
|------|-------------|-------------|
| E1 | Run 12 mandatory validation checks | Test evidence |
| E2 | Write MYFARMAI_ORCHESTRATOR_TEST_REPORT.md | Documentation artifact |
| E3 | Integration test with real MyFarmAI task | Verified completion |

---

## 5. Data Models (Pydantic)

### Core Entities

```python
# models.py - Key models

class TaskStatus(str, Enum):
    PLANNED = "planned"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    REVIEW = "review"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class CapabilityStatus(str, Enum):
    INSTALLED = "installed"
    CONFIGURED = "configured"
    AUTHENTICATED = "authenticated"
    AVAILABLE = "available"
    VERIFIED_WORKING = "verified_working"
    BROKEN = "broken"
    OBSOLETE = "obsolete"

class PermissionTier(str, Enum):
    TIER1_EXISTING = "tier1_existing"          # Auto-use
    TIER2_REVERSIBLE = "tier2_reversible"      # Auto-install if allowlisted
    TIER3_NEW = "tier3_new"                     # Explicit approval
    TIER4_DESTRUCTIVE = "tier4_destructive"     # Explicit authorization

class Task(BaseModel):
    id: str                                    # MF-<phase>-<seq>
    objective: str
    files_involved: List[str]
    dependencies: List[str]                    # Other task IDs
    constraints: List[str]                     # Hardware, licensing, Phase 0 findings
    expected_output: str
    verification_criteria: Dict[str, Any]      # Commands, expected results
    owner: str                                 # Agent name
    status: TaskStatus = TaskStatus.PLANNED
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    findings: List[str] = []
    blockers: List[str] = []
    evidence: Dict[str, Any] = {}

class Capability(BaseModel):
    name: str
    type: Literal["agent", "skill", "plugin", "mcp", "cli", "model", "test_framework"]
    version: Optional[str] = None
    location: str
    capabilities: List[str]
    permissions: List[str]
    dependencies: List[str]
    status: CapabilityStatus
    validation_command: Optional[str] = None
    validation_result: Optional[Dict[str, Any]] = None
    last_verified: Optional[datetime] = None

class AgentAssignment(BaseModel):
    task_id: str
    agent_name: str
    agent_type: Literal["existing", "new"]
    scope: List[str]                           # Files/components this agent owns
    parallel_group: Optional[int] = None       # For parallel execution
    handoff: Dict[str, Any]                    # Full handoff protocol data

class VerificationResult(BaseModel):
    task_id: str
    check_name: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    passed: bool
    evidence: Dict[str, Any]
    timestamp: datetime
```

---

## 6. Capability Registry Design

### Discovery Sources

| Source | Discovery Method | Example Capabilities |
|--------|------------------|---------------------|
| `.opencode/agents/*.md` | Parse agent definitions | 57 specialist agents |
| `.opencode/skills/*/SKILL.md` | Parse skill manifests | 26 skills |
| `opencode.json` | Parse plugin config | compound-engineering plugin |
| `opencode.json mcp.servers` | Parse MCP config | gh-grep, sentry, atlassian, etc. |
| `backend/requirements.txt` / `pyproject.toml` | Parse Python deps | pytest, ruff, mypy, fastapi |
| `web/package.json` | Parse npm deps | next.js, react, playwright |
| `android/package.json` | Parse npm deps | expo, react-native |
| Graphify knowledge graph | Query graphify-out/ | Code relationships, architecture |

### Registry Operations

1. **Full Scan** - On startup or explicit refresh
2. **Incremental Update** - On file change events
3. **Validation** - Run `validation_command` for each capability
4. **Conflict Detection** - Duplicate names, version conflicts, permission overlaps
5. **Health Report** - Summary of available/broken/obsolete capabilities

---

## 7. Dynamic Team Builder Algorithm

```
Input: Task graph (tasks with dependencies, constraints, file scopes)
Output: AgentAssignment[] with parallel groups

Algorithm:
1. For each task:
   a. Identify required capabilities from constraints + file types
   b. Query CapabilityRegistry for matching agents/skills
   c. Score candidates: (capability_match * 0.4) + (availability * 0.3) + (load * 0.2) + (specialization * 0.1)
   d. Select highest-scoring available agent
   e. If no existing agent covers all capabilities, check if skill+agent combo works
   f. Only create new agent definition if TIER3 approval granted

2. Build parallel groups:
   a. Topological sort by dependencies
   b. Group independent tasks (no shared files, no shared resources)
   c. Apply concurrency limits: CPU cores, RAM, GPU, model slots

3. Assign ownership:
   a. Each file/component → single owner agent
   b. Track in registry to prevent conflicts
   c. Flag any overlaps for manual resolution
```

---

## 8. Skill/Tool Routing Rules

### Routing Priority

1. **Existing Skill** - If skill exists for exact task type
2. **Existing Agent + Skill** - Agent with relevant skill loaded
3. **Existing Agent Only** - Agent with built-in capability
4. **MCP Tool** - Direct MCP server call
5. **CLI Tool** - Installed command-line tool
6. **New Skill Creation** - Only if TIER3 approved and gap is real

### Routing Table (Initial)

| Task Type | Primary Capability | Fallback |
|-----------|-------------------|----------|
| Backend API development | `@backend-engineer` + `api-contract` skill | `@fastapi-developer` |
| Frontend component | `@frontend-engineer` + `shadcn`/`ui-styling` | `@react-specialist` |
| Android feature | `@android-engineer` + `vercel-react-native-skills` | `@mobile-developer` |
| AI/ML model integration | `@ai-ml-engineer` + `google-agents-cli-adk-code` | `@llm-architect` |
| Web research | `@research-engineer` + `searxng` MCP | `@search-specialist` |
| Security audit | `@security-engineer` + `gstack-cso` | `@penetration-tester` |
| QA/Testing | `@qa-reviewer` + `test-patterns` | `@test-automator` |
| Architecture decision | `@architect-reviewer` + `adr-write` | `@ce-pov` |
| Documentation | `@docs-writer` + `document-generate` | `@technical-writer` |
| Deployment | `@deployment-engineer` + `deploy-to-vercel` | `@devops-engineer` |
| Database migration | `@database-administrator` + `migration` | `@postgres-pro` |
| Performance optimization | `@performance-engineer` + `performance-profile` | `@vercel-optimize` |

---

## 9. Execution Manager State Machine

```
Task State Transitions:

PLANNED → READY          : All dependencies PASSED, resources available
READY → RUNNING          : Agent assigned, worktree/branch created
RUNNING → BLOCKED        : Blocker reported (missing dep, permission, resource)
BLOCKED → READY          : Blocker resolved, re-verified
RUNNING → REVIEW         : Agent reports completion, outputs collected
REVIEW → PASSED          : Verification gate PASSED, integration clean
REVIEW → FAILED          : Verification gate FAILED or integration conflict
REVIEW → BLOCKED         : Security gate requires review, awaiting security-engineer
PASSED → (terminal)      : Task complete, memory updated
FAILED → READY           : Retry (if retries < limit, backoff applied)
FAILED → CANCELLED       : Max retries exceeded or manual cancellation
ANY → CANCELLED          : Manual cancellation, cleanup performed
```

### Concurrency Control

- **Max parallel agents**: `min(CPU_cores, 4)` = 4 (based on host)
- **Max concurrent model inferences**: 1 (2 GiB VRAM constraint)
- **Max concurrent Docker builds**: 1 (disk I/O constraint)
- **Max concurrent test runs**: 2 (RAM constraint)

---

## 10. Verification & Security Gates

### Quality Gate Checks (All Must Pass)

| Check | Command | Required |
|-------|---------|----------|
| Backend tests | `cd backend && uv run pytest -q` | Yes |
| Backend type check | `cd backend && uv run mypy .` | Yes |
| Backend lint | `cd backend && uv run ruff check .` | Yes |
| Frontend type check | `cd web && npm run typecheck` | Yes |
| Frontend tests | `cd web && npm test` | Yes |
| Frontend lint | `cd web && npm run lint` | Yes |
| Frontend build | `cd web && npm run build` | Yes |
| Android type check | `cd android && npm run typecheck` | Yes |
| Android lint | `cd android && npm run lint` | Yes |
| Secret scan | `gitleaks detect --source .` | Yes |
| Dependency audit | `pip-audit` / `npm audit` | Yes |
| OpenAPI diff | `diff openapi.json docs/api/openapi.json` | Yes |

### Security Gate (Security-Engineer Review Required)

- Authentication/authorization changes
- Secret/credential handling
- API endpoint exposure changes
- Database schema changes affecting permissions
- File upload/processing changes
- Dependency additions with known CVEs

---

## 11. Project Memory Schema

### Decision Records

```python
class DecisionRecord(BaseModel):
    id: str                                    # DR-<YYYYMMDD>-<seq>
    title: str
    context: str
    decision: str
    alternatives_considered: List[str]
    consequences: List[str]
    status: Literal["proposed", "approved", "rejected", "superseded"]
    approver: Optional[str] = None
    approved_at: Optional[datetime] = None
    related_tasks: List[str] = []
    related_files: List[str] = []
```

### Task History

```python
class TaskHistoryEntry(BaseModel):
    task_id: str
    event: Literal["created", "assigned", "started", "blocked", "unblocked", "completed", "failed", "retried", "cancelled"]
    timestamp: datetime
    agent: Optional[str] = None
    details: Dict[str, Any] = {}
    evidence_refs: List[str] = []              # Paths to logs, test outputs, diffs
```

---

## 12. Permission Policy Implementation

### Tier Enforcement

```python
class PermissionGate:
    def check(self, action: Action, context: Context) -> PermissionResult:
        tier = self.classify_action(action)
        
        if tier == PermissionTier.TIER1_EXISTING:
            return PermissionResult(allowed=True, reason="Existing trusted tool")
        
        if tier == PermissionTier.TIER2_REVERSIBLE:
            if self.is_allowlisted(action) and self.within_resource_limits(context):
                return PermissionResult(allowed=True, reason="Allowlisted reversible action")
            return PermissionResult(allowed=False, reason="Not allowlisted or exceeds limits")
        
        if tier == PermissionTier.TIER3_NEW:
            if self.has_explicit_approval(action):
                return PermissionResult(allowed=True, reason="Explicitly approved")
            return PermissionResult(allowed=False, reason="Requires explicit approval", requires_approval=True)
        
        if tier == PermissionTier.TIER4_DESTRCTIVE:
            if self.has_explicit_authorization(action) and self.has_safeguards(context):
                return PermissionResult(allowed=True, reason="Authorized with safeguards")
            return PermissionResult(allowed=False, reason="Requires explicit authorization + safeguards", requires_authorization=True)
```

---

## 13. Integration with Existing Systems

### Compound Engineering Plugin

The orchestrator will use these CE skills (already installed via plugin):
- `ce-plan` - Create structured plans
- `ce-work` - Execute plans end-to-end
- `ce-debug` - Debug failures
- `ce-commit-push-pr` - Ship changes
- `ce-code-review` - Review diffs
- `ce-doc-review` - Review docs
- `ce-handoff` - Session continuity
- `ce-compound` - Capture learnings

### Graphify Integration

```python
# Use graphify for project awareness
async def get_project_context(query: str) -> ProjectContext:
    # Query graphify for relevant code, docs, decisions
    result = await graphify_query(query)
    return ProjectContext(
        relevant_files=result.files,
        architecture_decisions=result.adrs,
        related_tasks=result.tasks,
        capability_gaps=result.gaps
    )
```

### OpenCode Session Model

- Each orchestration run = one OpenCode session
- Subagents spawned via `subagent` tool (background for parallel)
- Team tools (`team_create`, `team_spawn`, `team_tasks_add`) for complex multi-agent work
- `ce-handoff` for session persistence

---

## 14. Validation Checklist (12 Mandatory Checks)

| # | Check | Method | Success Criteria |
|---|-------|--------|------------------|
| 1 | Config loads | `opencode --version` | No new errors |
| 2 | Agents discoverable | `opencode agent list` | All 57 agents listed |
| 3 | Capability discovery | Run registry scan | Identifies installed + unavailable |
| 4 | Duplicate detection | Registry scan | Reports duplicates if any |
| 5 | Router selection | Test 3 task types | Correct agent/skill selected |
| 6 | Delegation (read-only) | Spawn 2 explore agents | Both return results |
| 7 | Result reconciliation | Collect explore results | Merged without conflicts |
| 8 | Non-destructive task | Complete real task | Task passes verification |
| 9 | Independent review | Security-engineer review | Review completes |
| 10 | Tests execute | Run quality gates | Real results captured |
| 11 | Permission gate | Attempt unauthorized action | Blocked with reason |
| 12 | Resumability | Interrupt + resume | State recovered |

---

## 15. Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| OpenCode API changes | Medium | High | Pin OpenCode version, abstract delegation layer |
| Compound plugin updates | Low | Medium | Test after plugin updates, version pin |
| Graphify stale | Medium | Medium | Auto-update on file changes, manual refresh command |
| Agent conflicts | Medium | High | File ownership tracking, pre-flight conflict check |
| Resource exhaustion | High | High | Concurrency limits, resource monitoring |
| Permission bypass | Low | Critical | Explicit tier enforcement, audit logging |
| Documentation drift | High | Medium | Doc-update required in every task handoff |

---

## 16. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Task decomposition accuracy | ≥ 90% tasks correctly scoped | Post-task review |
| Agent selection correctness | ≥ 95% tasks get optimal agent | Expert review |
| Parallel execution efficiency | ≥ 70% tasks parallelized | Execution logs |
| Verification gate pass rate | 100% for critical paths | CI/CD results |
| Documentation currency | 100% docs updated per change | Doc audit |
| Mean time to recovery | < 5 min for failed tasks | Incident logs |
| Capability registry freshness | < 1 hr stale | Registry timestamps |

---

## 17. Next Steps

1. **Immediate**: Begin Phase A - create Pydantic models and CapabilityRegistry
2. **Review**: Present this plan for approval before implementation
3. **Execute**: Follow phases A-E with verification at each step
4. **Document**: Update all 7 required documentation artifacts
5. **Validate**: Run all 12 mandatory validation checks
6. **Report**: Final test report and operations guide

---

## 18. Approval Required

This implementation plan requires approval before proceeding. The plan:
- Uses only existing OpenCode runtime (no new services/daemons)
- Respects all Phase 0 gates (no DB changes, no secret rotation, no voice changes)
- Follows HDD-first storage policy
- Follows document-first engineering policy
- Requires no Tier 3 or Tier 4 permissions for core implementation
- Tier 3 approval needed only if new agent definitions are created

**Approval Request**: Approve / Approve with Changes / Reject