"""
MyFarmAI Orchestrator - Core Data Models

Pydantic models for all orchestration entities including tasks, capabilities,
agents, verification results, and project memory.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

# =============================================================================
# Enums
# =============================================================================


class TaskStatus(str, Enum):
    """Task lifecycle states."""

    PLANNED = "planned"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    REVIEW = "review"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CapabilityType(str, Enum):
    """Types of capabilities in the registry."""

    AGENT = "agent"
    SKILL = "skill"
    PLUGIN = "plugin"
    MCP = "mcp"
    CLI = "cli"
    MODEL = "model"
    TEST_FRAMEWORK = "test_framework"


class CapabilityStatus(str, Enum):
    """Capability availability status."""

    INSTALLED = "installed"
    CONFIGURED = "configured"
    AUTHENTICATED = "authenticated"
    AVAILABLE = "available"
    VERIFIED_WORKING = "verified_working"
    BROKEN = "broken"
    OBSOLETE = "obsolete"


class PermissionTier(str, Enum):
    """Software permission tiers per policy."""

    TIER1_EXISTING = "tier1_existing"  # Auto-use within granted permissions
    TIER2_REVERSIBLE = "tier2_reversible"  # Auto-install if allowlisted + resource limits
    TIER3_NEW = "tier3_new"  # Explicit approval required
    TIER4_DESTRUCTIVE = "tier4_destructive"  # Explicit authorization + safeguards


class AgentType(str, Enum):
    """Agent definition types."""

    EXISTING = "existing"
    NEW = "new"


class VerificationCheckType(str, Enum):
    """Types of verification checks."""

    UNIT_TEST = "unit_test"
    INTEGRATION_TEST = "integration_test"
    TYPE_CHECK = "type_check"
    LINT = "lint"
    BUILD = "build"
    SECURITY_SCAN = "security_scan"
    SECRET_SCAN = "secret_scan"
    DEPENDENCY_AUDIT = "dependency_audit"
    CONTRACT_TEST = "contract_test"
    OPEN_API_DIFF = "openapi_diff"
    CUSTOM = "custom"


class DecisionStatus(str, Enum):
    """Decision record status."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class TaskEventType(str, Enum):
    """Task history event types."""

    CREATED = "created"
    ASSIGNED = "assigned"
    STARTED = "started"
    BLOCKED = "blocked"
    UNBLOCKED = "unblocked"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRIED = "retried"
    CANCELLED = "cancelled"


# =============================================================================
# Core Models
# =============================================================================


class Task(BaseModel):
    """A single unit of work in the orchestration system."""

    id: str = Field(
        default_factory=lambda: f"MF-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:6]}"
    )
    objective: str
    files_involved: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)  # Other task IDs
    constraints: list[str] = Field(default_factory=list)  # Hardware, licensing, Phase 0 findings
    expected_output: str
    verification_criteria: dict[str, Any] = Field(
        default_factory=dict
    )  # Commands, expected results
    owner: str  # Agent name
    status: TaskStatus = TaskStatus.PLANNED
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    findings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    parallel_group: int | None = None  # For parallel execution
    retry_count: int = 0
    max_retries: int = 3
    assigned_agent: str | None = None
    assigned_skill: str | None = None

    @field_validator("updated_at", mode="before")
    @classmethod
    def update_timestamp(cls, v):
        return datetime.now()

    def can_start(self, completed_tasks: set[str]) -> bool:
        """Check if all dependencies are satisfied."""
        return all(dep in completed_tasks for dep in self.dependencies)

    def is_terminal(self) -> bool:
        """Check if task is in a terminal state."""
        return self.status in (TaskStatus.PASSED, TaskStatus.FAILED, TaskStatus.CANCELLED)


class Capability(BaseModel):
    """A discoverable capability (agent, skill, tool, model, etc.)."""

    name: str
    type: CapabilityType
    version: str | None = None
    location: str
    capabilities: list[str] = Field(default_factory=list)  # What this capability can do
    permissions: list[str] = Field(default_factory=list)  # Required permissions
    dependencies: list[str] = Field(default_factory=list)  # Other capabilities needed
    status: CapabilityStatus = CapabilityStatus.INSTALLED
    validation_command: str | None = None
    validation_result: dict[str, Any] | None = None
    last_verified: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)  # Extra info (model size, license, etc.)

    def is_usable(self) -> bool:
        """Check if capability is available for use."""
        return self.status in (
            CapabilityStatus.AVAILABLE,
            CapabilityStatus.VERIFIED_WORKING,
            CapabilityStatus.AUTHENTICATED,
            CapabilityStatus.CONFIGURED,
        )

    def needs_validation(self) -> bool:
        """Check if capability needs re-validation."""
        if self.last_verified is None:
            return True
        # Re-validate if older than 1 hour
        return (datetime.now() - self.last_verified).total_seconds() > 3600


class AgentAssignment(BaseModel):
    """Assignment of a task to an agent with full handoff context."""

    task_id: str
    agent_name: str
    agent_type: AgentType = AgentType.EXISTING
    scope: list[str] = Field(default_factory=list)  # Files/components this agent owns
    parallel_group: int | None = None
    handoff: dict[str, Any] = Field(default_factory=dict)  # Full handoff protocol data
    created_at: datetime = Field(default_factory=datetime.now)


class VerificationResult(BaseModel):
    """Result of a single verification check."""

    task_id: str
    check_name: str
    check_type: VerificationCheckType
    command: str
    exit_code: int
    stdout: str
    stderr: str
    passed: bool
    evidence: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    duration_ms: int | None = None


class VerificationGate(BaseModel):
    """Collection of verification results for a task."""

    task_id: str
    results: list[VerificationResult] = Field(default_factory=list)
    overall_passed: bool = False
    failed_checks: list[str] = Field(default_factory=list)
    skipped_checks: list[str] = Field(default_factory=list)
    blocked_checks: list[str] = Field(default_factory=list)
    evaluated_at: datetime | None = None

    def evaluate(self) -> bool:
        """Evaluate overall pass/fail."""
        required_checks = [r for r in self.results if r.check_type != VerificationCheckType.CUSTOM]
        self.overall_passed = all(r.passed for r in required_checks)
        self.failed_checks = [r.check_name for r in required_checks if not r.passed]
        self.evaluated_at = datetime.now()
        return self.overall_passed


# =============================================================================
# Project Memory Models
# =============================================================================


class DecisionRecord(BaseModel):
    """Architecture/project decision record (ADR-style)."""

    id: str = Field(
        default_factory=lambda: f"DR-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:4]}"
    )
    title: str
    context: str
    decision: str
    alternatives_considered: list[str] = Field(default_factory=list)
    consequences: list[str] = Field(default_factory=list)
    status: DecisionStatus = DecisionStatus.PROPOSED
    approver: str | None = None
    approved_at: datetime | None = None
    related_tasks: list[str] = Field(default_factory=list)
    related_files: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class TaskHistoryEntry(BaseModel):
    """Single event in a task's history."""

    task_id: str
    event: TaskEventType
    timestamp: datetime = Field(default_factory=datetime.now)
    agent: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)  # Paths to logs, outputs, diffs


class ProjectMemory(BaseModel):
    """Durable project memory: decisions, task history, capability status, learnings."""

    decisions: dict[str, DecisionRecord] = Field(default_factory=dict)
    task_history: list[TaskHistoryEntry] = Field(default_factory=list)
    capability_snapshots: dict[str, dict[str, Any]] = Field(
        default_factory=dict
    )  # capability_name -> snapshot
    learnings: list[dict[str, Any]] = Field(default_factory=list)  # Captured from ce-compound
    updated_at: datetime = Field(default_factory=datetime.now)

    def add_decision(self, decision: DecisionRecord) -> None:
        self.decisions[decision.id] = decision
        self.updated_at = datetime.now()

    def add_history(self, entry: TaskHistoryEntry) -> None:
        self.task_history.append(entry)
        self.updated_at = datetime.now()

    def get_task_history(self, task_id: str) -> list[TaskHistoryEntry]:
        return [e for e in self.task_history if e.task_id == task_id]

    def snapshot_capability(self, capability: Capability) -> None:
        self.capability_snapshots[capability.name] = {
            "status": capability.status.value,
            "version": capability.version,
            "last_verified": capability.last_verified.isoformat()
            if capability.last_verified
            else None,
            "snapshot_at": datetime.now().isoformat(),
        }
        self.updated_at = datetime.now()


# =============================================================================
# Orchestration Context Models
# =============================================================================


class ResourceBudget(BaseModel):
    """Resource constraints for concurrent execution."""

    max_parallel_agents: int = 4
    max_concurrent_models: int = 1
    max_concurrent_docker_builds: int = 1
    max_concurrent_test_runs: int = 2
    max_ram_gb: float = 6.0  # Leave 1GB buffer on 7GB host
    max_vram_gb: float = 1.5  # Leave 0.5GB buffer on 2GB VRAM
    max_disk_gb: float = 4.0  # Leave 1GB buffer on 5GB free


class OrchestrationConfig(BaseModel):
    """Configuration for the orchestrator."""

    project_root: str = "/data/MyFarmAI"
    backend_path: str = "/data/MyFarmAI/backend"
    web_path: str = "/data/MyFarmAI/web"
    android_path: str = "/data/MyFarmAI/android"
    docs_path: str = "/data/MyFarmAI/docs"
    graphify_path: str = "/data/MyFarmAI/graphify-out"
    backup_path: str = "/data/MyFarmAI-backups"
    resource_budget: ResourceBudget = Field(default_factory=ResourceBudget)
    enable_parallel: bool = True
    default_max_retries: int = 3
    verification_timeout_seconds: int = 300
    session_persistence: bool = True


class TaskGraph(BaseModel):
    """Dependency graph of tasks."""

    tasks: dict[str, Task] = Field(default_factory=dict)
    parallel_groups: dict[int, list[str]] = Field(default_factory=dict)  # group_id -> task_ids

    def add_task(self, task: Task) -> None:
        self.tasks[task.id] = task

    def get_ready_tasks(self, completed: set[str]) -> list[Task]:
        """Get tasks that can run now (deps met, not started, not terminal)."""
        ready = []
        for task in self.tasks.values():
            if task.status == TaskStatus.PLANNED and task.can_start(completed):
                ready.append(task)
        return ready

    def get_running_tasks(self) -> list[Task]:
        return [t for t in self.tasks.values() if t.status == TaskStatus.RUNNING]

    def topological_sort(self) -> list[str]:
        """Return task IDs in topological order."""
        # Simple Kahn's algorithm
        in_degree = {tid: 0 for tid in self.tasks}
        for task in self.tasks.values():
            for dep in task.dependencies:
                if dep in in_degree:
                    in_degree[task.id] += 1

        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        result = []

        while queue:
            tid = queue.pop(0)
            result.append(tid)
            task = self.tasks[tid]
            for other in self.tasks.values():
                if tid in other.dependencies:
                    in_degree[other.id] -= 1
                    if in_degree[other.id] == 0:
                        queue.append(other.id)

        if len(result) != len(self.tasks):
            raise ValueError("Cycle detected in task graph")

        return result


# =============================================================================
# Handoff Protocol Models
# =============================================================================


class HandoffProtocol(BaseModel):
    """Standardized handoff protocol for agent delegation."""

    task_id: str
    objective: str
    files_components: list[str]
    dependencies: list[str]
    constraints: list[str]
    expected_output: str
    verification_criteria: dict[str, Any]
    findings: list[str] = Field(default_factory=list)
    unresolved_blockers: list[str] = Field(default_factory=list)
    context_refs: list[str] = Field(default_factory=list)  # Paths to relevant docs, code, decisions


# =============================================================================
# Utility Functions
# =============================================================================


def create_task_id(phase: str, seq: int) -> str:
    """Generate a task ID in MF-<phase>-<seq> format."""
    return f"MF-{phase}-{seq:03d}"


def parse_task_id(task_id: str) -> tuple[str, int]:
    """Parse task ID into (phase, seq)."""
    parts = task_id.split("-")
    if len(parts) >= 3 and parts[0] == "MF":
        return parts[1], int(parts[2])
    raise ValueError(f"Invalid task ID format: {task_id}")
