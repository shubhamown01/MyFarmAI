"""
MyFarmAI Orchestrator - Execution Manager

Tracks task state, captures worker outputs, handles retries with backoff,
and supports resumable runs.
"""

import asyncio
import json
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .core import OrchestratorCore
from .models import (
    AgentAssignment,
    HandoffProtocol,
    OrchestrationConfig,
    ProjectMemory,
    Task,
    TaskEventType,
    TaskHistoryEntry,
    TaskStatus,
    VerificationGate,
)
from .registry import CapabilityRegistry


class ExecutionPhase(Enum):
    """Phases of task execution."""
    PREPARING = "preparing"
    DELEGATING = "delegating"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    INTEGRATING = "integrating"
    COMPLETING = "completing"
    FAILED = "failed"


@dataclass
class ExecutionContext:
    """Context for a single task execution."""
    task: Task
    phase: ExecutionPhase = ExecutionPhase.PREPARING
    started_at: datetime = field(default_factory=datetime.now)
    assigned_agent: str | None = None
    assigned_skill: str | None = None
    worktree_path: str | None = None
    checkpoint_data: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    last_error: str | None = None
    outputs: dict[str, Any] = field(default_factory=dict)
    verification_gate: VerificationGate | None = None


class CheckpointManager:
    """Manages checkpoints for resumable execution."""

    def __init__(self, config: OrchestrationConfig):
        self.config = config
        self.checkpoint_dir = Path(config.project_root) / ".orchestrator" / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(self, context: ExecutionContext) -> str:
        """Save execution checkpoint to disk."""
        checkpoint_file = self.checkpoint_dir / f"{context.task.id}.json"

        # Helper to serialize datetime objects
        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize(v) for v in obj]
            elif hasattr(obj, 'model_dump'):
                return serialize(obj.model_dump(mode='json'))
            return obj

        data = {
            "task_id": context.task.id,
            "phase": context.phase.value,
            "started_at": context.started_at.isoformat(),
            "assigned_agent": context.assigned_agent,
            "assigned_skill": context.assigned_skill,
            "worktree_path": context.worktree_path,
            "checkpoint_data": context.checkpoint_data,
            "retry_count": context.retry_count,
            "last_error": context.last_error,
            "outputs": serialize(context.outputs),
            "task_status": context.task.status.value,
            "task_findings": context.task.findings,
            "task_blockers": context.task.blockers,
            "task_evidence": serialize(context.task.evidence),
            "saved_at": datetime.now().isoformat(),
        }

        checkpoint_file.write_text(json.dumps(data, indent=2))
        return str(checkpoint_file)

    def load_checkpoint(self, task_id: str) -> dict[str, Any] | None:
        """Load execution checkpoint from disk."""
        checkpoint_file = self.checkpoint_dir / f"{task_id}.json"

        if not checkpoint_file.exists():
            return None

        try:
            return json.loads(checkpoint_file.read_text())
        except Exception:
            return None

    def delete_checkpoint(self, task_id: str) -> bool:
        """Delete checkpoint after successful completion."""
        checkpoint_file = self.checkpoint_dir / f"{task_id}.json"
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            return True
        return False

    def list_checkpoints(self) -> list[dict[str, Any]]:
        """List all available checkpoints."""
        checkpoints = []
        for file in self.checkpoint_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text())
                checkpoints.append({
                    "task_id": data.get("task_id"),
                    "phase": data.get("phase"),
                    "saved_at": data.get("saved_at"),
                    "retry_count": data.get("retry_count", 0),
                })
            except Exception:
                pass
        return checkpoints


class ExecutionManager:
    """
    Manages task execution lifecycle with:
    - State tracking (planned, ready, running, blocked, review, passed, failed, cancelled)
    - Worker output capture
    - Retries with limits and exponential backoff
    - Resumable runs via checkpoints
    - Resource budget enforcement
    """

    def __init__(
        self,
        config: OrchestrationConfig,
        registry: CapabilityRegistry,
        memory: ProjectMemory,
        core: OrchestratorCore,
        delegation_executor: Callable[[AgentAssignment, HandoffProtocol], Awaitable[dict[str, Any]]],
        verification_executor: Callable[[Task], Awaitable[VerificationGate]],
        integration_executor: Callable[[list[Task]], Awaitable[dict[str, Any]]],
    ):
        self.config = config
        self.registry = registry
        self.memory = memory
        self.core = core
        self.delegation_executor = delegation_executor
        self.verification_executor = verification_executor
        self.integration_executor = integration_executor

        self.checkpoint_manager = CheckpointManager(config)
        self.active_contexts: dict[str, ExecutionContext] = {}
        self._execution_locks: dict[str, asyncio.Lock] = {}

        # Retry configuration
        self.base_retry_delay = 2.0  # seconds
        self.max_retry_delay = 60.0  # seconds
        self.max_retries = 3

    async def execute_task(self, task: Task) -> Task:
        """
        Execute a single task through the full lifecycle.
        Returns the updated task.
        """
        # Get or create execution lock
        if task.id not in self._execution_locks:
            self._execution_locks[task.id] = asyncio.Lock()

        async with self._execution_locks[task.id]:
            # Check for existing checkpoint
            context = await self._load_or_create_context(task)

            try:
                # Phase 1: Preparing
                context.phase = ExecutionPhase.PREPARING
                await self._prepare_execution(context)

                # Phase 2: Delegating
                context.phase = ExecutionPhase.DELEGATING
                await self._delegate_task(context)

                # Phase 3: Executing
                context.phase = ExecutionPhase.EXECUTING
                await self._execute_delegation(context)

                # Phase 4: Verifying
                context.phase = ExecutionPhase.VERIFYING
                await self._verify_results(context)

                # Phase 5: Integrating (if applicable)
                if context.task.files_involved:
                    context.phase = ExecutionPhase.INTEGRATING
                    await self._integrate_changes(context)

                # Phase 6: Completing
                context.phase = ExecutionPhase.COMPLETING
                await self._complete_task(context)

                # Clean up checkpoint on success
                self.checkpoint_manager.delete_checkpoint(task.id)

            except Exception as e:
                context.last_error = str(e)
                context.task.status = TaskStatus.FAILED
                context.task.findings.append(f"Execution error: {str(e)}")
                context.phase = ExecutionPhase.FAILED

                # Save checkpoint for potential retry
                self.checkpoint_manager.save_checkpoint(context)

                # Record failure
                self.memory.add_history(TaskHistoryEntry(
                    task_id=task.id,
                    event=TaskEventType.FAILED,
                    details={"error": str(e), "phase": context.phase.value},
                    evidence_refs=[self.checkpoint_manager.checkpoint_dir / f"{task.id}.json"]
                ))

                raise

            return context.task

    async def _load_or_create_context(self, task: Task) -> ExecutionContext:
        """Load existing checkpoint or create new context."""
        checkpoint = self.checkpoint_manager.load_checkpoint(task.id)

        if checkpoint and checkpoint.get("task_status") in ["running", "blocked"]:
            # Resume from checkpoint
            context = ExecutionContext(task=task)
            context.phase = ExecutionPhase(checkpoint.get("phase", "preparing"))
            context.started_at = datetime.fromisoformat(checkpoint["started_at"])
            context.assigned_agent = checkpoint.get("assigned_agent")
            context.assigned_skill = checkpoint.get("assigned_skill")
            context.worktree_path = checkpoint.get("worktree_path")
            context.checkpoint_data = checkpoint.get("checkpoint_data", {})
            context.retry_count = checkpoint.get("retry_count", 0)
            context.last_error = checkpoint.get("last_error")
            context.outputs = checkpoint.get("outputs", {})

            # Restore task state
            task.status = TaskStatus(checkpoint.get("task_status", "planned"))
            task.findings = checkpoint.get("task_findings", [])
            task.blockers = checkpoint.get("task_blockers", [])
            task.evidence = checkpoint.get("task_evidence", {})

            self.memory.add_history(TaskHistoryEntry(
                task_id=task.id,
                event=TaskEventType.UNBLOCKED if task.status == TaskStatus.BLOCKED else TaskEventType.STARTED,
                details={"resumed_from_checkpoint": True, "phase": context.phase.value}
            ))
        else:
            # Fresh execution
            context = ExecutionContext(task=task)
            self.memory.add_history(TaskHistoryEntry(
                task_id=task.id,
                event=TaskEventType.STARTED,
                details={"fresh_execution": True}
            ))

        self.active_contexts[task.id] = context
        return context

    async def _prepare_execution(self, context: ExecutionContext) -> None:
        """Prepare for task execution."""
        task = context.task

        # Verify dependencies are met
        for dep_id in task.dependencies:
            dep_task = self.core.get_task(dep_id)
            if dep_task and dep_task.status != TaskStatus.PASSED:
                task.status = TaskStatus.BLOCKED
                task.blockers.append(f"Dependency {dep_id} not complete")
                raise RuntimeError(f"Dependency {dep_id} not satisfied")

        # Check resource availability
        if not await self._check_resources(task):
            task.status = TaskStatus.BLOCKED
            task.blockers.append("Insufficient resources")
            raise RuntimeError("Insufficient resources for task")

        # Create worktree if needed (for file modifications)
        if task.files_involved:
            context.worktree_path = await self._create_worktree(task)

        # Save checkpoint
        self.checkpoint_manager.save_checkpoint(context)

    async def _check_resources(self, task: Task) -> bool:
        """Check if resources are available for task."""
        budget = self.config.resource_budget

        # Check parallel agent limit
        if len(self.core.active_agents) >= budget.max_parallel_agents:
            return False

        # Check model slots
        needs_model = any("model" in c.lower() or "ai" in c.lower() or "inference" in c.lower()
                         for c in task.constraints)
        if needs_model and self.core.active_models >= budget.max_concurrent_models:
            return False

        # Check docker build slots
        needs_docker = any("docker" in c.lower() or "container" in c.lower() or "build" in c.lower()
                          for c in task.constraints)
        if needs_docker and self.core.active_docker_builds >= budget.max_concurrent_docker_builds:
            return False

        # Check test slots
        needs_test = any("test" in c.lower() for c in task.constraints)
        if needs_test and self.core.active_test_runs >= budget.max_concurrent_test_runs:
            return False

        return True

    async def _create_worktree(self, task: Task) -> str:
        """Create a git worktree for isolated task execution."""
        try:
            worktree_name = f"task-{task.id}-{int(time.time())}"
            worktree_path = Path(self.config.project_root) / ".orchestrator" / "worktrees" / worktree_name
            worktree_path.parent.mkdir(parents=True, exist_ok=True)

            # Use git worktree
            proc = await asyncio.create_subprocess_exec(
                "git", "worktree", "add", str(worktree_path), "-b", f"task/{task.id}",
                cwd=self.config.project_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

            if proc.returncode == 0:
                return str(worktree_path)
            else:
                # Worktree creation failed, use main worktree
                return str(self.config.project_root)
        except Exception:
            return str(self.config.project_root)

    async def _delegate_task(self, context: ExecutionContext) -> None:
        """Delegate task to assigned agent."""
        task = context.task

        # Build handoff
        handoff = HandoffProtocol(
            task_id=task.id,
            objective=task.objective,
            files_components=task.files_involved,
            dependencies=task.dependencies,
            constraints=task.constraints,
            expected_output=task.expected_output,
            verification_criteria=task.verification_criteria,
            findings=task.findings,
            unresolved_blockers=task.blockers,
            context_refs=self._get_context_refs(task)
        )

        # Create assignment
        assignment = AgentAssignment(
            task_id=task.id,
            agent_name=task.assigned_agent or task.owner,
            scope=task.files_involved,
            parallel_group=task.parallel_group,
            handoff=handoff.model_dump()
        )

        context.assigned_agent = assignment.agent_name

        # Track active agent
        self.core.active_agents.add(assignment.agent_name)

        # Execute delegation
        try:
            result = await self.delegation_executor(assignment, handoff)
            context.outputs["delegation"] = result
            context.task.evidence["delegation_result"] = result
            context.task.findings.extend(result.get("findings", []))

            # Save checkpoint after delegation
            self.checkpoint_manager.save_checkpoint(context)

        except Exception as e:
            context.last_error = f"Delegation failed: {str(e)}"
            raise

    async def _execute_delegation(self, context: ExecutionContext) -> None:
        """Wait for delegated work to complete (polling or callback)."""
        # In the current model, delegation_executor runs synchronously
        # This phase is for any post-delegation processing
        task = context.task

        # If task was delegated to a subagent that runs in background,
        # we would poll here. For now, assume synchronous completion.

        # Update task status based on delegation result
        delegation_result = context.outputs.get("delegation", {})
        if delegation_result.get("status") == "failed":
            task.status = TaskStatus.FAILED
            task.blockers.append(delegation_result.get("error", "Delegation failed"))
        elif delegation_result.get("status") == "blocked":
            task.status = TaskStatus.BLOCKED
            task.blockers.extend(delegation_result.get("blockers", []))

    async def _verify_results(self, context: ExecutionContext) -> None:
        """Run verification gate on task results."""
        task = context.task

        try:
            gate = await self.verification_executor(task)
            context.verification_gate = gate
            task.evidence["verification"] = {
                "overall_passed": gate.overall_passed,
                "failed_checks": gate.failed_checks,
                "results": [r.model_dump() for r in gate.results]
            }

            if gate.overall_passed:
                task.status = TaskStatus.PASSED
            else:
                task.status = TaskStatus.FAILED
                task.blockers.extend(gate.failed_checks)

            # Save checkpoint after verification
            self.checkpoint_manager.save_checkpoint(context)

        except Exception as e:
            context.last_error = f"Verification failed: {str(e)}"
            task.status = TaskStatus.FAILED
            task.blockers.append(f"Verification error: {str(e)}")
            raise

    async def _integrate_changes(self, context: ExecutionContext) -> None:
        """Integrate changes from task (merge worktree, resolve conflicts)."""
        task = context.task

        if not context.worktree_path or context.worktree_path == self.config.project_root:
            return  # No worktree to integrate

        try:
            # Check for conflicts
            integration_result = await self.integration_executor([task])

            if integration_result.get("conflicts"):
                task.status = TaskStatus.BLOCKED
                task.blockers.extend([f"Integration conflict: {c}" for c in integration_result["conflicts"]])
                context.phase = ExecutionPhase.FAILED
                raise RuntimeError("Integration conflicts detected")

            # Merge worktree back to main
            await self._merge_worktree(context.worktree_path, task.id)

            task.evidence["integration"] = integration_result

        except Exception as e:
            context.last_error = f"Integration failed: {str(e)}"
            raise

    async def _merge_worktree(self, worktree_path: str, task_id: str) -> None:
        """Merge worktree changes back to main branch."""
        try:
            # Get current branch
            proc = await asyncio.create_subprocess_exec(
                "git", "branch", "--show-current",
                cwd=worktree_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            branch = stdout.decode().strip()

            if branch and branch != "main":
                # Merge to main
                proc = await asyncio.create_subprocess_exec(
                    "git", "checkout", "main",
                    cwd=self.config.project_root,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()

                proc = await asyncio.create_subprocess_exec(
                    "git", "merge", "--no-ff", branch, "-m", f"Merge task {task_id}",
                    cwd=self.config.project_root,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()

                if proc.returncode != 0:
                    raise RuntimeError(f"Merge failed: {stderr.decode()}")

                # Clean up worktree
                proc = await asyncio.create_subprocess_exec(
                    "git", "worktree", "remove", worktree_path,
                    cwd=self.config.project_root,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()

                # Delete branch
                proc = await asyncio.create_subprocess_exec(
                    "git", "branch", "-d", branch,
                    cwd=self.config.project_root,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()

        except Exception as e:
            raise RuntimeError(f"Worktree merge failed: {str(e)}")

    async def _complete_task(self, context: ExecutionContext) -> None:
        """Finalize task completion."""
        task = context.task

        task.completed_at = datetime.now()
        task.updated_at = datetime.now()

        # Record completion
        self.memory.add_history(TaskHistoryEntry(
            task_id=task.id,
            event=TaskEventType.COMPLETED if task.status == TaskStatus.PASSED else TaskEventType.FAILED,
            details={
                "status": task.status.value,
                "duration_ms": int((task.completed_at - task.started_at).total_seconds() * 1000) if task.started_at else 0,
                "retry_count": context.retry_count,
            },
            evidence_refs=list(context.outputs.keys())
        ))

        # Release agent
        if context.assigned_agent:
            self.core.active_agents.discard(context.assigned_agent)

        # Release resource slots
        if any("model" in c.lower() for c in task.constraints):
            self.core.release_model_slot()
        if any("docker" in c.lower() for c in task.constraints):
            self.core.release_docker_build_slot()
        if any("test" in c.lower() for c in task.constraints):
            self.core.release_test_slot()

    def _get_context_refs(self, task: Task) -> list[str]:
        """Get relevant context references for a task."""
        refs = []
        if any("backend" in f for f in task.files_involved):
            refs.extend([
                "docs/product/TRD.md",
                "docs/backend/ARCHITECTURE.md",
                "docs/roadmaps/MyFarmAI_Backend_Roadmap.md"
            ])
        if any("web" in f or "frontend" in f for f in task.files_involved):
            refs.extend([
                "docs/product/UI_UX_DESIGN_SYSTEM.md",
                "docs/frontend/DESIGN_SYSTEM.md",
                "docs/roadmaps/MyFarmAI_Frontend_Dashboard_Roadmap.md"
            ])
        if any("android" in f for f in task.files_involved):
            refs.append("docs/integration/ANDROID_INTEGRATION.md")
        return refs

    async def retry_task(self, task: Task) -> Task:
        """Retry a failed task with exponential backoff."""
        if task.retry_count >= task.max_retries:
            raise RuntimeError(f"Task {task.id} exceeded max retries ({task.max_retries})")

        # Calculate backoff delay
        delay = min(self.base_retry_delay * (2 ** task.retry_count), self.max_retry_delay)

        # Add jitter
        import random
        delay += random.uniform(0, 1)

        task.retry_count += 1
        task.status = TaskStatus.READY
        task.blockers.append(f"Retry {task.retry_count}/{task.max_retries} after {delay:.1f}s")

        self.memory.add_history(TaskHistoryEntry(
            task_id=task.id,
            event=TaskEventType.RETRIED,
            details={"retry_count": task.retry_count, "delay_seconds": delay}
        ))

        # Wait before retry
        await asyncio.sleep(delay)

        # Clear checkpoint to start fresh (or keep for resume)
        # self.checkpoint_manager.delete_checkpoint(task.id)

        return await self.execute_task(task)

    def cancel_task(self, task: Task, reason: str = "Cancelled") -> None:
        """Cancel a running task."""
        task.status = TaskStatus.CANCELLED
        task.blockers.append(reason)
        task.completed_at = datetime.now()

        if task.id in self.active_contexts:
            context = self.active_contexts[task.id]
            if context.assigned_agent:
                self.core.active_agents.discard(context.assigned_agent)

        self.memory.add_history(TaskHistoryEntry(
            task_id=task.id,
            event=TaskEventType.CANCELLED,
            details={"reason": reason}
        ))

        # Clean up checkpoint
        self.checkpoint_manager.delete_checkpoint(task.id)

    def get_execution_status(self) -> dict[str, Any]:
        """Get status of all active executions."""
        return {
            "active_contexts": len(self.active_contexts),
            "contexts": {
                task_id: {
                    "task_id": ctx.task.id,
                    "phase": ctx.phase.value,
                    "assigned_agent": ctx.assigned_agent,
                    "retry_count": ctx.retry_count,
                    "last_error": ctx.last_error,
                    "duration_seconds": int((datetime.now() - ctx.started_at).total_seconds()),
                }
                for task_id, ctx in self.active_contexts.items()
            },
            "checkpoints": self.checkpoint_manager.list_checkpoints(),
        }
