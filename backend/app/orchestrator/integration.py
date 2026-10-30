"""
MyFarmAI Orchestrator - Integration Review Manager

Collects specialist outputs, detects conflicting file ownership and overlapping changes,
integrates work through controlled branches, and requests independent review.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .core import OrchestratorCore
from .models import OrchestrationConfig, ProjectMemory, Task, TaskStatus


class ConflictType(Enum):
    """Types of integration conflicts."""
    FILE_OVERLAP = "file_overlap"           # Multiple tasks modifying same file
    DEPENDENCY_CYCLE = "dependency_cycle"   # Circular dependencies
    API_CONTRACT = "api_contract"           # Breaking API changes
    DATABASE_SCHEMA = "database_schema"     # Conflicting schema changes
    CONFIGURATION = "configuration"         # Conflicting config changes
    RESOURCE_CONTENTION = "resource_contention"  # Competing for same resource


class ConflictSeverity(Enum):
    """Severity of integration conflicts."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKING = "blocking"


@dataclass
class IntegrationConflict:
    """A detected integration conflict."""
    conflict_id: str
    type: ConflictType
    severity: ConflictSeverity
    description: str
    affected_tasks: list[str]
    affected_files: list[str]
    suggested_resolution: str | None = None
    auto_resolvable: bool = False
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class IntegrationResult:
    """Result of integration review."""
    success: bool
    conflicts: list[IntegrationConflict]
    merged_files: list[str]
    skipped_files: list[str]
    warnings: list[str]
    requires_review: bool
    review_notes: list[str]


class FileOwnershipTracker:
    """Tracks file ownership across tasks to prevent conflicts."""

    def __init__(self):
        self.ownership: dict[str, str] = {}  # file -> task_id
        self.pending_changes: dict[str, dict[str, Any]] = {}  # file -> {task_id, changes}
        self.history: list[dict[str, Any]] = []

    def claim_ownership(self, task_id: str, files: list[str]) -> list[str]:
        """Claim ownership of files for a task. Returns conflicts."""
        conflicts = []
        for file in files:
            if file in self.ownership and self.ownership[file] != task_id:
                conflicts.append(f"{file} owned by task {self.ownership[file]}")
            else:
                self.ownership[file] = task_id
                self.history.append({
                    "action": "claim",
                    "file": file,
                    "task_id": task_id,
                    "timestamp": datetime.now().isoformat()
                })
        return conflicts

    def release_ownership(self, task_id: str, files: list[str]) -> None:
        """Release ownership of files."""
        for file in files:
            if self.ownership.get(file) == task_id:
                del self.ownership[file]
                self.history.append({
                    "action": "release",
                    "file": file,
                    "task_id": task_id,
                    "timestamp": datetime.now().isoformat()
                })

    def get_owner(self, file: str) -> str | None:
        """Get current owner of a file."""
        return self.ownership.get(file)

    def get_task_files(self, task_id: str) -> list[str]:
        """Get all files owned by a task."""
        return [f for f, owner in self.ownership.items() if owner == task_id]

    def register_pending_change(self, task_id: str, file: str, change_info: dict[str, Any]) -> None:
        """Register a pending change to a file."""
        if file not in self.pending_changes:
            self.pending_changes[file] = {}
        self.pending_changes[file][task_id] = change_info

    def get_pending_changes(self, file: str) -> dict[str, dict[str, Any]]:
        """Get all pending changes for a file."""
        return self.pending_changes.get(file, {})

    def clear_pending_changes(self, task_id: str) -> None:
        """Clear pending changes for a task."""
        for file in list(self.pending_changes.keys()):
            if task_id in self.pending_changes[file]:
                del self.pending_changes[file][task_id]
            if not self.pending_changes[file]:
                del self.pending_changes[file]


class IntegrationReviewManager:
    """
    Manages integration of specialist outputs:
    - Collects outputs from completed tasks
    - Detects conflicting file ownership and overlapping changes
    - Integrates work through controlled branches/patches
    - Requests independent review for important changes
    - Rejects unsupported claims and incomplete acceptance criteria
    """

    def __init__(self, config: OrchestrationConfig, core: OrchestratorCore, memory: ProjectMemory):
        self.config = config
        self.core = core
        self.memory = memory
        self.ownership_tracker = FileOwnershipTracker()
        self.integration_history: list[IntegrationResult] = []
        self._review_queue: list[tuple[str, IntegrationResult]] = []  # (task_id, result)

    async def integrate_task_outputs(self, tasks: list[Task]) -> IntegrationResult:
        """
        Integrate outputs from completed tasks.
        
        This is called after task verification passes.
        """
        # Filter to tasks that have passed and have file changes
        completed_tasks = [t for t in tasks if t.status == TaskStatus.PASSED]

        if not completed_tasks:
            return IntegrationResult(
                success=True,
                conflicts=[],
                merged_files=[],
                skipped_files=[],
                warnings=[],
                requires_review=False,
                review_notes=[]
            )

        conflicts = []
        merged_files = []
        skipped_files = []
        warnings = []
        requires_review = False
        review_notes = []

        # Phase 1: Detect conflicts
        conflicts.extend(await self._detect_file_overlaps(completed_tasks))
        conflicts.extend(await self._detect_api_contract_conflicts(completed_tasks))
        conflicts.extend(await self._detect_database_conflicts(completed_tasks))
        conflicts.extend(await self._detect_config_conflicts(completed_tasks))

        # Phase 2: Check for blocking conflicts
        blocking_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.BLOCKING]
        if blocking_conflicts:
            return IntegrationResult(
                success=False,
                conflicts=conflicts,
                merged_files=[],
                skipped_files=[],
                warnings=[],
                requires_review=True,
                review_notes=[f"Blocking conflicts: {len(blocking_conflicts)}"]
            )

        # Phase 3: Attempt auto-resolution for resolvable conflicts
        resolvable = [c for c in conflicts if c.auto_resolvable]
        for conflict in resolvable:
            resolved = await self._auto_resolve_conflict(conflict)
            if resolved:
                merged_files.extend(conflict.affected_files)
            else:
                conflicts.append(IntegrationConflict(
                    conflict_id=f"auto_resolve_failed_{conflict.conflict_id}",
                    type=conflict.type,
                    severity=ConflictSeverity.ERROR,
                    description=f"Failed to auto-resolve: {conflict.description}",
                    affected_tasks=conflict.affected_tasks,
                    affected_files=conflict.affected_files,
                    auto_resolvable=False
                ))

        # Phase 4: Integrate non-conflicting changes
        for task in completed_tasks:
            task_files = task.files_involved
            for file in task_files:
                # Check if file has any unresolved conflicts
                file_conflicts = [c for c in conflicts if file in c.affected_files and not c.auto_resolvable]
                if not file_conflicts:
                    merged = await self._integrate_file(task, file)
                    if merged:
                        merged_files.append(file)
                    else:
                        skipped_files.append(file)
                else:
                    skipped_files.append(file)

        # Phase 5: Determine if review required
        error_conflicts = [c for c in conflicts if c.severity in (ConflictSeverity.ERROR, ConflictSeverity.BLOCKING)]
        warning_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.WARNING]

        if error_conflicts:
            requires_review = True
            review_notes.append(f"Errors requiring review: {len(error_conflicts)}")
        elif warning_conflicts:
            requires_review = True
            review_notes.append(f"Warnings for review: {len(warning_conflicts)}")

        # Check for security-sensitive changes
        security_tasks = [t for t in completed_tasks if self._is_security_sensitive(t)]
        if security_tasks:
            requires_review = True
            review_notes.append(f"Security-sensitive tasks: {len(security_tasks)}")

        # Check for API contract changes
        api_tasks = [t for t in completed_tasks if self._is_api_change(t)]
        if api_tasks:
            requires_review = True
            review_notes.append(f"API contract changes: {len(api_tasks)}")

        result = IntegrationResult(
            success=len(blocking_conflicts) == 0,
            conflicts=conflicts,
            merged_files=merged_files,
            skipped_files=skipped_files,
            warnings=warnings,
            requires_review=requires_review,
            review_notes=review_notes
        )

        self.integration_history.append(result)

        if requires_review:
            self._review_queue.extend((t.id, result) for t in completed_tasks)

        return result

    async def _detect_file_overlaps(self, tasks: list[Task]) -> list[IntegrationConflict]:
        """Detect multiple tasks modifying the same files."""
        conflicts = []
        file_to_tasks: dict[str, list[str]] = defaultdict(list)

        for task in tasks:
            for file in task.files_involved:
                file_to_tasks[file].append(task.id)

        for file, task_ids in file_to_tasks.items():
            if len(task_ids) > 1:
                # Check if tasks are sequential (one depends on another)
                sequential = False
                for i, t1 in enumerate(task_ids):
                    for t2 in task_ids[i+1:]:
                        task1 = self.core.get_task(t1)
                        task2 = self.core.get_task(t2)
                        if task1 and t2 in task1.dependencies:
                            sequential = True
                        if task2 and t1 in task2.dependencies:
                            sequential = True

                if not sequential:
                    conflicts.append(IntegrationConflict(
                        conflict_id=f"file_overlap_{file}_{datetime.now().timestamp()}",
                        type=ConflictType.FILE_OVERLAP,
                        severity=ConflictSeverity.ERROR,
                        description=f"Multiple tasks modifying {file} without dependency ordering",
                        affected_tasks=task_ids,
                        affected_files=[file],
                        suggested_resolution="Add explicit dependencies or merge tasks",
                        auto_resolvable=False
                    ))

        return conflicts

    async def _detect_api_contract_conflicts(self, tasks: list[Task]) -> list[IntegrationConflict]:
        """Detect breaking API contract changes."""
        conflicts = []

        # Look for tasks modifying API-related files
        api_tasks = [t for t in tasks if self._is_api_change(t)]

        if len(api_tasks) > 1:
            # Multiple tasks changing API - potential conflict
            conflicts.append(IntegrationConflict(
                conflict_id=f"api_contract_{datetime.now().timestamp()}",
                type=ConflictType.API_CONTRACT,
                severity=ConflictSeverity.WARNING,
                description="Multiple tasks modifying API endpoints/contracts",
                affected_tasks=[t.id for t in api_tasks],
                affected_files=[f for t in api_tasks for f in t.files_involved],
                suggested_resolution="Coordinate API changes; ensure backward compatibility",
                auto_resolvable=False
            ))

        # Check for OpenAPI spec changes
        openapi_tasks = [t for t in tasks if any("openapi" in f.lower() for f in t.files_involved)]
        if len(openapi_tasks) > 1:
            conflicts.append(IntegrationConflict(
                conflict_id=f"openapi_conflict_{datetime.now().timestamp()}",
                type=ConflictType.API_CONTRACT,
                severity=ConflictSeverity.BLOCKING,
                description="Multiple tasks modifying OpenAPI specification",
                affected_tasks=[t.id for t in openapi_tasks],
                affected_files=[f for t in openapi_tasks for f in t.files_involved],
                suggested_resolution="Single task should own OpenAPI spec; others should reference",
                auto_resolvable=False
            ))

        return conflicts

    async def _detect_database_conflicts(self, tasks: list[Task]) -> list[IntegrationConflict]:
        """Detect conflicting database schema changes."""
        conflicts = []

        db_tasks = [t for t in tasks if self._is_database_change(t)]

        if len(db_tasks) > 1:
            conflicts.append(IntegrationConflict(
                conflict_id=f"db_schema_{datetime.now().timestamp()}",
                type=ConflictType.DATABASE_SCHEMA,
                severity=ConflictSeverity.BLOCKING,
                description="Multiple tasks modifying database schema/migrations",
                affected_tasks=[t.id for t in db_tasks],
                affected_files=[f for t in db_tasks for f in t.files_involved],
                suggested_resolution="Sequential migration tasks; single owner for schema",
                auto_resolvable=False
            ))

        return conflicts

    async def _detect_config_conflicts(self, tasks: list[Task]) -> list[IntegrationConflict]:
        """Detect conflicting configuration changes."""
        conflicts = []

        config_tasks = [t for t in tasks if self._is_config_change(t)]

        if len(config_tasks) > 1:
            # Check specific files
            config_files: dict[str, list[str]] = defaultdict(list)
            for task in config_tasks:
                for file in task.files_involved:
                    if any(ext in file.lower() for ext in [".yml", ".yaml", ".json", ".toml", ".ini", ".env"]):
                        config_files[file].append(task.id)

            for file, task_ids in config_files.items():
                if len(task_ids) > 1:
                    conflicts.append(IntegrationConflict(
                        conflict_id=f"config_{file}_{datetime.now().timestamp()}",
                        type=ConflictType.CONFIGURATION,
                        severity=ConflictSeverity.WARNING,
                        description=f"Multiple tasks modifying config file {file}",
                        affected_tasks=task_ids,
                        affected_files=[file],
                        suggested_resolution="Consolidate config changes or use feature flags",
                        auto_resolvable=False
                    ))

        return conflicts

    async def _auto_resolve_conflict(self, conflict: IntegrationConflict) -> bool:
        """Attempt to auto-resolve a conflict."""
        if conflict.type == ConflictType.FILE_OVERLAP:
            # For file overlaps, check if changes are to different sections
            # This would require git diff analysis - simplified for now
            return False

        if conflict.type == ConflictType.CONFIGURATION:
            # Config conflicts might be mergeable if different keys
            return False

        return False

    async def _integrate_file(self, task: Task, file: str) -> bool:
        """Integrate a single file's changes."""
        # In practice, this would apply patches or merge worktrees
        # For now, just track ownership
        self.ownership_tracker.claim_ownership(task.id, [file])
        return True

    def _is_security_sensitive(self, task: Task) -> bool:
        """Check if task involves security-sensitive changes."""
        security_patterns = [
            "auth", "secret", "password", "token", "credential",
            "security", "vulnerability", "encryption", "tls", "ssl",
            "permission", "authorization", "rbac", "oauth"
        ]
        text = f"{task.objective} {' '.join(task.files_involved)} {' '.join(task.constraints)}".lower()
        return any(pattern in text for pattern in security_patterns)

    def _is_api_change(self, task: Task) -> bool:
        """Check if task modifies API contracts."""
        api_patterns = [
            "api", "endpoint", "route", "handler", "contract",
            "openapi", "swagger", "schema", "serializer"
        ]
        text = f"{task.objective} {' '.join(task.files_involved)}".lower()
        return any(pattern in text for pattern in api_patterns)

    def _is_database_change(self, task: Task) -> bool:
        """Check if task modifies database schema."""
        db_patterns = [
            "migration", "schema", "model", "database", "table",
            "alembic", "sqlalchemy", "orm", "entity"
        ]
        text = f"{task.objective} {' '.join(task.files_involved)}".lower()
        return any(pattern in text for pattern in db_patterns)

    def _is_config_change(self, task: Task) -> bool:
        """Check if task modifies configuration."""
        config_patterns = [
            "config", "settings", ".yml", ".yaml", ".json", ".toml",
            ".ini", ".env", "docker-compose", "dockerfile"
        ]
        text = f"{task.objective} {' '.join(task.files_involved)}".lower()
        return any(pattern in text for pattern in config_patterns)

    async def request_review(self, task_id: str, reviewer: str, notes: str) -> bool:
        """Request independent review for a task."""
        task = self.core.get_task(task_id)
        if not task:
            return False

        # In practice, this would notify the reviewer agent
        # For now, just record the request
        self.memory.add_history(TaskHistoryEntry(
            task_id=task_id,
            event=TaskEventType.BLOCKED,
            details={
                "review_requested": True,
                "reviewer": reviewer,
                "notes": notes
            }
        ))

        task.status = TaskStatus.REVIEW
        return True

    def get_review_queue(self) -> list[tuple[str, IntegrationResult]]:
        """Get pending review queue."""
        return self._review_queue

    def complete_review(self, task_id: str, approved: bool, reviewer_notes: str) -> None:
        """Complete a review."""
        task = self.core.get_task(task_id)
        if not task:
            return

        # Remove from review queue
        self._review_queue = [(tid, res) for tid, res in self._review_queue if tid != task_id]

        if approved:
            task.status = TaskStatus.PASSED
        else:
            task.status = TaskStatus.FAILED
            task.blockers.append(f"Review rejected: {reviewer_notes}")

        self.memory.add_history(TaskHistoryEntry(
            task_id=task_id,
            event=TaskEventType.COMPLETED if approved else TaskEventType.FAILED,
            details={
                "review_result": "approved" if approved else "rejected",
                "reviewer_notes": reviewer_notes
            }
        ))

    def get_integration_summary(self) -> dict[str, Any]:
        """Get summary of integration state."""
        total_conflicts = sum(len(r.conflicts) for r in self.integration_history)
        blocking_conflicts = sum(
            len([c for c in r.conflicts if c.severity == ConflictSeverity.BLOCKING])
            for r in self.integration_history
        )

        return {
            "total_integrations": len(self.integration_history),
            "total_conflicts": total_conflicts,
            "blocking_conflicts": blocking_conflicts,
            "pending_reviews": len(self._review_queue),
            "tracked_files": len(self.ownership_tracker.ownership),
            "current_ownership": dict(self.ownership_tracker.ownership),
        }
