"""
MyFarmAI Orchestrator - Core Orchestration Engine

Main orchestration logic: task graph management, delegation, progress tracking,
and integration with all subsystems.
"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

from .models import (
    AgentAssignment,
    DecisionRecord,
    HandoffProtocol,
    OrchestrationConfig,
    ProjectMemory,
    Task,
    TaskEventType,
    TaskGraph,
    TaskHistoryEntry,
    TaskPriority,
    TaskStatus,
    VerificationGate,
)
from .registry import CapabilityRegistry


@dataclass
class OrchestrationResult:
    """Result of an orchestration run."""

    success: bool
    completed_tasks: list[str]
    failed_tasks: list[str]
    blocked_tasks: list[str]
    total_duration_ms: int
    errors: list[str]
    warnings: list[str]


class OrchestratorCore:
    """
    Core orchestration engine that manages the complete task lifecycle:
    Plan → Build Team → Assign → Execute → Integrate → Test → Secure → Document → Report
    """

    def __init__(
        self,
        config: OrchestrationConfig,
        registry: CapabilityRegistry,
        memory: ProjectMemory,
        delegation_callback: Callable[[AgentAssignment, HandoffProtocol], Awaitable[dict[str, Any]]] | None = None,
        verification_callback: Callable[[Task], Awaitable[VerificationGate]] | None = None,
        integration_callback: Callable[[list[Task]], Awaitable[dict[str, Any]]] | None = None,
    ):
        self.config = config
        self.registry = registry
        self.memory = memory
        self.task_graph = TaskGraph()
        self.delegation_callback = delegation_callback
        self.verification_callback = verification_callback
        self.integration_callback = integration_callback

        # Runtime state
        self.running = False
        self.current_run_id: str | None = None
        self._task_locks: dict[str, asyncio.Lock] = {}
        self._file_ownership: dict[str, str] = {}  # file -> task_id

        # Resource tracking
        self.active_agents: set[str] = set()
        self.active_models: int = 0
        self.active_docker_builds: int = 0
        self.active_test_runs: int = 0

    # =========================================================================
    # Task Management
    # =========================================================================

    def add_task(self, task: Task) -> None:
        """Add a task to the orchestration graph."""
        self.task_graph.add_task(task)
        self._task_locks[task.id] = asyncio.Lock()
        self._record_history(task.id, TaskEventType.CREATED, {"objective": task.objective})

    def add_tasks(self, tasks: list[Task]) -> None:
        """Add multiple tasks."""
        for task in tasks:
            self.add_task(task)

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        return self.task_graph.tasks.get(task_id)

    def get_all_tasks(self) -> list[Task]:
        """Get all tasks."""
        return list(self.task_graph.tasks.values())

    def get_tasks_by_status(self, status: TaskStatus) -> list[Task]:
        """Get tasks by status."""
        return [t for t in self.task_graph.tasks.values() if t.status == status]

    # =========================================================================
    # Task Planning & Decomposition
    # =========================================================================

    def decompose_objective(
        self, objective: str, context: dict[str, Any], phase: str = "AUTO"
    ) -> list[Task]:
        """
        Decompose a high-level objective into concrete tasks.
        Uses the registry to find relevant capabilities and create appropriate tasks.
        """
        # This is a simplified decomposition - in practice would use AI/LLM
        # For now, create a basic task structure based on objective keywords

        tasks = []
        seq = 1

        # Analyze objective for required capabilities
        required_caps = self._analyze_objective(objective)

        # Create tasks for each capability area
        for cap_area in required_caps:
            task = Task(
                id=f"MF-{phase}-{seq:03d}",
                objective=f"{cap_area}: {objective}",
                files_involved=[],
                dependencies=[],
                constraints=context.get("constraints", []),
                expected_output=f"Completed {cap_area} work for: {objective}",
                verification_criteria=context.get("verification_criteria", {}),
                owner="",  # Will be assigned by team builder
                priority=self._determine_priority(cap_area),
            )
            tasks.append(task)
            seq += 1

        # Add dependency chain for sequential areas
        for i in range(1, len(tasks)):
            tasks[i].dependencies.append(tasks[i - 1].id)

        return tasks

    def _analyze_objective(self, objective: str) -> list[str]:
        """Analyze objective to determine required capability areas."""
        obj_lower = objective.lower()
        areas = []

        capability_keywords = {
            "backend": [
                "api",
                "backend",
                "fastapi",
                "database",
                "sql",
                "migration",
                "endpoint",
                "auth",
            ],
            "frontend": [
                "frontend",
                "web",
                "react",
                "next.js",
                "ui",
                "component",
                "dashboard",
                "page",
            ],
            "android": ["android", "mobile", "expo", "react native", "app", "device"],
            "ai_ml": [
                "model",
                "ai",
                "ml",
                "ollama",
                "inference",
                "qwen",
                "personaplex",
                "training",
            ],
            "research": ["research", "search", "searxng", "citation", "extraction", "web search"],
            "security": ["security", "auth", "secret", "vulnerability", "penetration", "threat"],
            "qa": ["test", "qa", "quality", "lint", "typecheck", "coverage", "regression"],
            "deployment": [
                "deploy",
                "docker",
                "ci",
                "cd",
                "vercel",
                "kubernetes",
                "infrastructure",
            ],
            "documentation": ["doc", "readme", "documentation", "guide", "api doc"],
            "architecture": ["architecture", "design", "adr", "decision", "review", "refactor"],
        }

        for area, keywords in capability_keywords.items():
            if any(kw in obj_lower for kw in keywords):
                areas.append(area)

        return areas if areas else ["general"]

    def _determine_priority(self, capability_area: str) -> TaskPriority:
        """Determine task priority based on capability area."""
        critical_areas = ["security", "deployment"]
        high_areas = ["backend", "ai_ml", "architecture"]
        low_areas = ["documentation"]

        if capability_area in critical_areas:
            return TaskPriority.CRITICAL
        elif capability_area in high_areas:
            return TaskPriority.HIGH
        elif capability_area in low_areas:
            return TaskPriority.LOW
        return TaskPriority.MEDIUM

    # =========================================================================
    # Execution Control
    # =========================================================================

    async def run(self, task_ids: list[str] | None = None) -> OrchestrationResult:
        """
        Run the orchestration for specified tasks (or all ready tasks).
        Returns when all tasks reach terminal state or max iterations reached.
        """
        self.running = True
        self.current_run_id = f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"
        start_time = datetime.now()

        completed: set[str] = set()
        failed_tasks: list[str] = []
        blocked_tasks: list[str] = []
        errors: list[str] = []
        warnings: list[str] = []

        try:
            # If specific tasks provided, only run those and their dependencies
            if task_ids:
                target_tasks = set(task_ids)
                # Add dependencies
                for tid in list(target_tasks):
                    task = self.get_task(tid)
                    if task:
                        target_tasks.update(task.dependencies)
            else:
                target_tasks = set(self.task_graph.tasks.keys())

            max_iterations = 100
            iteration = 0

            while self.running and iteration < max_iterations:
                iteration += 1

                # Get ready tasks
                ready_tasks = self.task_graph.get_ready_tasks(completed)
                ready_tasks = [t for t in ready_tasks if t.id in target_tasks]

                # Filter by resource availability
                ready_tasks = self._filter_by_resources(ready_tasks)

                if not ready_tasks:
                    # Check if all target tasks are done
                    remaining = [
                        t
                        for t in self.task_graph.tasks.values()
                        if t.id in target_tasks and not t.is_terminal()
                    ]
                    if not remaining:
                        break  # All done

                    # Check for blocked tasks
                    blocked = [t for t in remaining if t.status == TaskStatus.BLOCKED]
                    if blocked:
                        blocked_tasks.extend([t.id for t in blocked])
                        warnings.append(f"{len(blocked)} tasks blocked")

                    # Wait a bit and continue
                    await asyncio.sleep(1)
                    continue

                # Assign and run ready tasks
                for task in ready_tasks:
                    # Check file ownership conflicts
                    conflict = self._check_file_conflicts(task)
                    if conflict:
                        task.status = TaskStatus.BLOCKED
                        task.blockers.append(f"File conflict: {conflict}")
                        blocked_tasks.append(task.id)
                        continue

                    # Assign ownership
                    self._assign_file_ownership(task)

                    # Run task
                    try:
                        await self._execute_task(task)
                        if task.status == TaskStatus.PASSED:
                            completed.add(task.id)
                        elif task.status == TaskStatus.FAILED:
                            failed_tasks.append(task.id)
                            # Retry logic
                            if task.retry_count < task.max_retries:
                                task.retry_count += 1
                                task.status = TaskStatus.READY
                                task.blockers.append(f"Retry {task.retry_count}/{task.max_retries}")
                                await asyncio.sleep(2**task.retry_count)  # Exponential backoff
                            else:
                                errors.append(
                                    f"Task {task.id} failed after {task.max_retries} retries"
                                )
                        elif task.status == TaskStatus.BLOCKED:
                            blocked_tasks.append(task.id)
                    except Exception as e:
                        task.status = TaskStatus.FAILED
                        task.findings.append(f"Execution error: {str(e)}")
                        failed_tasks.append(task.id)
                        errors.append(f"Task {task.id} error: {str(e)}")

                    # Release ownership
                    self._release_file_ownership(task)

                # Small delay to prevent busy loop
                await asyncio.sleep(0.1)

            if iteration >= max_iterations:
                warnings.append("Max iterations reached")

        finally:
            self.running = False

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return OrchestrationResult(
            success=len(failed_tasks) == 0 and len(blocked_tasks) == 0,
            completed_tasks=list(completed),
            failed_tasks=failed_tasks,
            blocked_tasks=blocked_tasks,
            total_duration_ms=duration_ms,
            errors=errors,
            warnings=warnings,
        )

    def stop(self) -> None:
        """Stop the orchestration run."""
        self.running = False

    # =========================================================================
    # Task Execution
    # =========================================================================

    async def _execute_task(self, task: Task) -> None:
        """Execute a single task through the full lifecycle."""
        async with self._task_locks[task.id]:
            # Update status
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            task.updated_at = datetime.now()
            self._record_history(task.id, TaskEventType.STARTED, {"agent": task.assigned_agent})

            # Build handoff protocol
            handoff = self._build_handoff(task)

            # Create agent assignment
            assignment = AgentAssignment(
                task_id=task.id,
                agent_name=task.assigned_agent or task.owner,
                agent_type="existing",
                scope=task.files_involved,
                parallel_group=task.parallel_group,
                handoff=handoff.model_dump(),
            )

            # Track active agent
            self.active_agents.add(assignment.agent_name)

            try:
                # Delegate to agent
                if self.delegation_callback:
                    result = await self.delegation_callback(assignment, handoff)
                    task.evidence["delegation_result"] = result
                    task.findings.extend(result.get("findings", []))

                # Run verification gate
                if self.verification_callback:
                    gate = await self.verification_callback(task)
                    task.evidence["verification"] = {
                        "overall_passed": gate.overall_passed,
                        "failed_checks": gate.failed_checks,
                        "results": [r.model_dump() for r in gate.results],
                    }

                    if gate.overall_passed:
                        task.status = TaskStatus.PASSED
                    else:
                        task.status = TaskStatus.FAILED
                        task.blockers.extend(gate.failed_checks)
                else:
                    # No verification callback - assume pass for now
                    task.status = TaskStatus.PASSED

                task.completed_at = datetime.now()
                task.updated_at = datetime.now()

                if task.status == TaskStatus.PASSED:
                    self._record_history(
                        task.id, TaskEventType.COMPLETED, {"evidence": task.evidence}
                    )
                else:
                    self._record_history(task.id, TaskEventType.FAILED, {"blockers": task.blockers})

            finally:
                self.active_agents.discard(assignment.agent_name)

    def _build_handoff(self, task: Task) -> HandoffProtocol:
        """Build handoff protocol for task delegation."""
        return HandoffProtocol(
            task_id=task.id,
            objective=task.objective,
            files_components=task.files_involved,
            dependencies=task.dependencies,
            constraints=task.constraints,
            expected_output=task.expected_output,
            verification_criteria=task.verification_criteria,
            findings=task.findings,
            unresolved_blockers=task.blockers,
            context_refs=self._get_context_refs(task),
        )

    def _get_context_refs(self, task: Task) -> list[str]:
        """Get relevant context references for a task."""
        refs = []
        # Add relevant docs based on task type
        if any("backend" in f for f in task.files_involved):
            refs.extend(
                [
                    "docs/product/TRD.md",
                    "docs/backend/ARCHITECTURE.md",
                    "docs/roadmaps/MyFarmAI_Backend_Roadmap.md",
                ]
            )
        if any("web" in f or "frontend" in f for f in task.files_involved):
            refs.extend(
                [
                    "docs/product/UI_UX_DESIGN_SYSTEM.md",
                    "docs/frontend/DESIGN_SYSTEM.md",
                    "docs/roadmaps/MyFarmAI_Frontend_Dashboard_Roadmap.md",
                ]
            )
        if any("android" in f for f in task.files_involved):
            refs.append("docs/integration/ANDROID_INTEGRATION.md")
        return refs

    # =========================================================================
    # Resource Management
    # =========================================================================

    def _filter_by_resources(self, tasks: list[Task]) -> list[Task]:
        """Filter tasks that can run within resource budgets."""
        budget = self.config.resource_budget
        filtered = []

        for task in tasks:
            # Check agent limit
            if len(self.active_agents) >= budget.max_parallel_agents:
                break

            # Check model limit (if task needs model)
            needs_model = any("model" in c.lower() or "ai" in c.lower() for c in task.constraints)
            if needs_model and self.active_models >= budget.max_concurrent_models:
                continue

            # Check docker build limit
            needs_docker = any(
                "docker" in c.lower() or "container" in c.lower() or "build" in c.lower()
                for c in task.constraints
            )
            if needs_docker and self.active_docker_builds >= budget.max_concurrent_docker_builds:
                continue

            # Check test run limit
            needs_test = any("test" in c.lower() for c in task.constraints)
            if needs_test and self.active_test_runs >= budget.max_concurrent_test_runs:
                continue

            filtered.append(task)

        return filtered

    def acquire_model_slot(self) -> bool:
        """Try to acquire a model inference slot."""
        if self.active_models < self.config.resource_budget.max_concurrent_models:
            self.active_models += 1
            return True
        return False

    def release_model_slot(self) -> None:
        """Release a model inference slot."""
        self.active_models = max(0, self.active_models - 1)

    def acquire_docker_build_slot(self) -> bool:
        """Try to acquire a Docker build slot."""
        if self.active_docker_builds < self.config.resource_budget.max_concurrent_docker_builds:
            self.active_docker_builds += 1
            return True
        return False

    def release_docker_build_slot(self) -> None:
        """Release a Docker build slot."""
        self.active_docker_builds = max(0, self.active_docker_builds - 1)

    def acquire_test_slot(self) -> bool:
        """Try to acquire a test run slot."""
        if self.active_test_runs < self.config.resource_budget.max_concurrent_test_runs:
            self.active_test_runs += 1
            return True
        return False

    def release_test_slot(self) -> None:
        """Release a test run slot."""
        self.active_test_runs = max(0, self.active_test_runs - 1)

    # =========================================================================
    # File Ownership & Conflict Prevention
    # =========================================================================

    def _check_file_conflicts(self, task: Task) -> str | None:
        """Check if task's files conflict with other running tasks."""
        for file_path in task.files_involved:
            if file_path in self._file_ownership:
                owner_task = self._file_ownership[file_path]
                owner = self.get_task(owner_task)
                if owner and owner.status == TaskStatus.RUNNING:
                    return f"{file_path} owned by running task {owner_task}"
        return None

    def _assign_file_ownership(self, task: Task) -> None:
        """Assign file ownership to task."""
        for file_path in task.files_involved:
            self._file_ownership[file_path] = task.id

    def _release_file_ownership(self, task: Task) -> None:
        """Release file ownership from task."""
        for file_path in task.files_involved:
            if self._file_ownership.get(file_path) == task.id:
                del self._file_ownership[file_path]

    # =========================================================================
    # History & Memory
    # =========================================================================

    def _record_history(
        self,
        task_id: str,
        event: TaskEventType,
        details: dict[str, Any],
        agent: str | None = None,
        evidence_refs: list[str] | None = None,
    ) -> None:
        """Record a task history event."""
        entry = TaskHistoryEntry(
            task_id=task_id,
            event=event,
            agent=agent,
            details=details,
            evidence_refs=evidence_refs or [],
        )
        self.memory.add_history(entry)

    def add_decision(self, decision: DecisionRecord) -> None:
        """Add a decision record to project memory."""
        self.memory.add_decision(decision)

    # =========================================================================
    # Status & Reporting
    # =========================================================================

    def get_status(self) -> dict[str, Any]:
        """Get current orchestration status."""
        return {
            "run_id": self.current_run_id,
            "running": self.running,
            "task_counts": {
                status.value: len(self.get_tasks_by_status(status)) for status in TaskStatus
            },
            "active_agents": list(self.active_agents),
            "resource_usage": {
                "model_slots": f"{self.active_models}/{self.config.resource_budget.max_concurrent_models}",
                "docker_build_slots": f"{self.active_docker_builds}/{self.config.resource_budget.max_concurrent_docker_builds}",
                "test_slots": f"{self.active_test_runs}/{self.config.resource_budget.max_concurrent_test_runs}",
            },
            "file_ownership": dict(self._file_ownership),
        }

    def export_task_graph(self) -> dict[str, Any]:
        """Export task graph for visualization/debugging."""
        return {
            "tasks": {
                tid: {
                    "id": task.id,
                    "objective": task.objective,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "owner": task.owner,
                    "assigned_agent": task.assigned_agent,
                    "dependencies": task.dependencies,
                    "files_involved": task.files_involved,
                    "created_at": task.created_at.isoformat(),
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "retry_count": task.retry_count,
                    "blockers": task.blockers,
                }
                for tid, task in self.task_graph.tasks.items()
            },
            "parallel_groups": self.task_graph.parallel_groups,
        }
