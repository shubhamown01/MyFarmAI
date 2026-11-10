"""
MyFarmAI Orchestrator - Project Memory & Audit Trail

Records durable project decisions, architecture constraints, task history,
capability status, and recurring failures.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .models import (
    Capability,
    DecisionRecord,
    DecisionStatus,
    OrchestrationConfig,
    ProjectMemory,
    TaskEventType,
    TaskHistoryEntry,
)


class MemoryStorage:
    """Persistent storage for project memory."""

    def __init__(self, config: OrchestrationConfig):
        self.config = config
        self.memory_dir = Path(config.project_root) / ".orchestrator" / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.decisions_file = self.memory_dir / "decisions.json"
        self.history_file = self.memory_dir / "history.jsonl"
        self.capabilities_file = self.memory_dir / "capabilities.json"
        self.learnings_file = self.memory_dir / "learnings.json"
        self.metadata_file = self.memory_dir / "metadata.json"

    def save_decisions(self, decisions: dict[str, DecisionRecord]) -> None:
        """Save decisions to disk."""
        data = {
            "decisions": {k: v.model_dump(mode="json") for k, v in decisions.items()},
            "saved_at": datetime.now().isoformat(),
        }
        self.decisions_file.write_text(json.dumps(data, indent=2))

    def load_decisions(self) -> dict[str, DecisionRecord]:
        """Load decisions from disk."""
        if not self.decisions_file.exists():
            return {}

        try:
            data = json.loads(self.decisions_file.read_text())
            return {
                k: DecisionRecord.model_validate(v) for k, v in data.get("decisions", {}).items()
            }
        except Exception:
            return {}

    def append_history(self, entry: TaskHistoryEntry) -> None:
        """Append history entry to JSONL file."""
        with self.history_file.open("a") as f:
            f.write(json.dumps(entry.model_dump(mode="json")) + "\n")

    def load_history(
        self, since: datetime | None = None, limit: int = 1000
    ) -> list[TaskHistoryEntry]:
        """Load history entries from JSONL file."""
        entries = []
        if not self.history_file.exists():
            return entries

        try:
            with self.history_file.open("r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    entry = TaskHistoryEntry.model_validate(json.loads(line))
                    if since and entry.timestamp < since:
                        continue
                    entries.append(entry)
                    if len(entries) >= limit:
                        break
        except Exception:
            pass

        return entries

    def save_capabilities(self, capabilities: dict[str, dict[str, Any]]) -> None:
        """Save capability snapshots."""
        data = {"capabilities": capabilities, "saved_at": datetime.now().isoformat()}
        self.capabilities_file.write_text(json.dumps(data, indent=2))

    def load_capabilities(self) -> dict[str, dict[str, Any]]:
        """Load capability snapshots."""
        if not self.capabilities_file.exists():
            return {}

        try:
            data = json.loads(self.capabilities_file.read_text())
            return data.get("capabilities", {})
        except Exception:
            return {}

    def save_learnings(self, learnings: list[dict[str, Any]]) -> None:
        """Save captured learnings."""
        data = {"learnings": learnings, "saved_at": datetime.now().isoformat()}
        self.learnings_file.write_text(json.dumps(data, indent=2))

    def load_learnings(self) -> list[dict[str, Any]]:
        """Load captured learnings."""
        if not self.learnings_file.exists():
            return []

        try:
            data = json.loads(self.learnings_file.read_text())
            return data.get("learnings", [])
        except Exception:
            return []

    def save_metadata(self, metadata: dict[str, Any]) -> None:
        """Save metadata."""
        data = {"metadata": metadata, "saved_at": datetime.now().isoformat()}
        self.metadata_file.write_text(json.dumps(data, indent=2))

    def load_metadata(self) -> dict[str, Any]:
        """Load metadata."""
        if not self.metadata_file.exists():
            return {}

        try:
            data = json.loads(self.metadata_file.read_text())
            return data.get("metadata", {})
        except Exception:
            return {}


class ProjectMemoryManager:
    """
    Manages durable project memory:
    - Architecture decisions (ADR-style)
    - Task execution history
    - Capability status snapshots
    - Learnings from completed work
    - Recurring failure patterns
    """

    def __init__(self, config: OrchestrationConfig):
        self.config = config
        self.storage = MemoryStorage(config)
        self.memory = ProjectMemory()
        self._load_all()

    def _load_all(self) -> None:
        """Load all memory from disk."""
        self.memory.decisions = self.storage.load_decisions()
        self.memory.task_history = self.storage.load_history()
        self.memory.capability_snapshots = self.storage.load_capabilities()
        self.memory.learnings = self.storage.load_learnings()

    def save_all(self) -> None:
        """Save all memory to disk."""
        self.storage.save_decisions(self.memory.decisions)
        self.storage.save_capabilities(self.memory.capability_snapshots)
        self.storage.save_learnings(self.memory.learnings)
        self.storage.save_metadata(
            {
                "total_decisions": len(self.memory.decisions),
                "total_history_entries": len(self.memory.task_history),
                "total_learnings": len(self.memory.learnings),
            }
        )

    # =========================================================================
    # Decision Records
    # =========================================================================

    def add_decision(self, decision: DecisionRecord) -> None:
        """Add a decision record."""
        self.memory.add_decision(decision)
        self.storage.save_decisions(self.memory.decisions)

    def get_decision(self, decision_id: str) -> DecisionRecord | None:
        """Get a decision by ID."""
        return self.memory.decisions.get(decision_id)

    def get_decisions_by_status(self, status: DecisionStatus) -> list[DecisionRecord]:
        """Get decisions by status."""
        return [d for d in self.memory.decisions.values() if d.status == status]

    def get_recent_decisions(self, days: int = 30) -> list[DecisionRecord]:
        """Get decisions from the last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        return [d for d in self.memory.decisions.values() if d.created_at >= cutoff]

    def update_decision_status(
        self, decision_id: str, status: DecisionStatus, approver: str | None = None
    ) -> bool:
        """Update decision status."""
        decision = self.memory.decisions.get(decision_id)
        if not decision:
            return False

        decision.status = status
        if status == DecisionStatus.APPROVED:
            decision.approver = approver
            decision.approved_at = datetime.now()
        decision.updated_at = datetime.now()

        self.storage.save_decisions(self.memory.decisions)
        return True

    # =========================================================================
    # Task History
    # =========================================================================

    def add_history(self, entry: TaskHistoryEntry) -> None:
        """Add a history entry."""
        self.memory.add_history(entry)
        self.storage.append_history(entry)

    def get_task_history(self, task_id: str) -> list[TaskHistoryEntry]:
        """Get history for a specific task."""
        return self.memory.get_task_history(task_id)

    def get_recent_history(self, hours: int = 24, limit: int = 100) -> list[TaskHistoryEntry]:
        """Get recent history entries."""
        cutoff = datetime.now() - timedelta(hours=hours)
        entries = [e for e in self.memory.task_history if e.timestamp >= cutoff]
        return sorted(entries, key=lambda e: e.timestamp, reverse=True)[:limit]

    def get_history_by_event(self, event: TaskEventType, hours: int = 24) -> list[TaskHistoryEntry]:
        """Get history entries by event type."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [e for e in self.memory.task_history if e.event == event and e.timestamp >= cutoff]

    def get_failure_patterns(self, days: int = 7) -> dict[str, int]:
        """Analyze recurring failure patterns."""
        cutoff = datetime.now() - timedelta(days=days)
        failures = [
            e
            for e in self.memory.task_history
            if e.event in (TaskEventType.FAILED, TaskEventType.BLOCKED) and e.timestamp >= cutoff
        ]

        patterns: dict[str, int] = {}
        for failure in failures:
            # Extract error pattern from details
            error = failure.details.get("error", "")
            blocker = failure.details.get("blockers", [])

            key = error or (blocker[0] if blocker else "unknown")
            # Simplify key
            key = key[:100] if key else "unknown"
            patterns[key] = patterns.get(key, 0) + 1

        return dict(sorted(patterns.items(), key=lambda x: x[1], reverse=True))

    def get_agent_performance(self, days: int = 30) -> dict[str, dict[str, Any]]:
        """Get performance metrics per agent."""
        cutoff = datetime.now() - timedelta(days=days)
        entries = [e for e in self.memory.task_history if e.agent and e.timestamp >= cutoff]

        agent_stats: dict[str, dict[str, Any]] = {}

        for entry in entries:
            agent = entry.agent
            if agent not in agent_stats:
                agent_stats[agent] = {
                    "total_tasks": 0,
                    "completed": 0,
                    "failed": 0,
                    "blocked": 0,
                    "retried": 0,
                    "avg_duration_ms": 0,
                    "durations": [],
                }

            stats = agent_stats[agent]
            stats["total_tasks"] += 1

            if entry.event == TaskEventType.COMPLETED:
                stats["completed"] += 1
            elif entry.event == TaskEventType.FAILED:
                stats["failed"] += 1
            elif entry.event == TaskEventType.BLOCKED:
                stats["blocked"] += 1
            elif entry.event == TaskEventType.RETRIED:
                stats["retried"] += 1

            duration = entry.details.get("duration_ms")
            if duration:
                stats["durations"].append(duration)

        # Calculate averages
        for stats in agent_stats.values():
            if stats["durations"]:
                stats["avg_duration_ms"] = sum(stats["durations"]) // len(stats["durations"])
            del stats["durations"]

        return agent_stats

    # =========================================================================
    # Capability Snapshots
    # =========================================================================

    def snapshot_capability(self, capability: Capability) -> None:
        """Snapshot a capability's current state."""
        self.memory.snapshot_capability(capability)
        self.storage.save_capabilities(self.memory.capability_snapshots)

    def get_capability_snapshot(self, name: str) -> dict[str, Any] | None:
        """Get capability snapshot."""
        return self.memory.capability_snapshots.get(name)

    def get_capability_history(self, name: str) -> list[dict[str, Any]]:
        """Get capability history from snapshots."""
        # This would need a time-series approach; for now return current
        snapshot = self.memory.capability_snapshots.get(name)
        return [snapshot] if snapshot else []

    # =========================================================================
    # Learnings
    # =========================================================================

    def add_learning(
        self,
        title: str,
        description: str,
        category: str,
        related_tasks: list[str],
        related_files: list[str],
        tags: list[str] = None,
    ) -> None:
        """Add a captured learning (from ce-compound or manual)."""
        learning = {
            "id": f"LRN-{datetime.now().strftime('%Y%m%d')}-{len(self.memory.learnings):04d}",
            "title": title,
            "description": description,
            "category": category,
            "related_tasks": related_tasks,
            "related_files": related_files,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "source": "manual",  # or "ce-compound"
        }
        self.memory.learnings.append(learning)
        self.storage.save_learnings(self.memory.learnings)

    def get_learnings_by_category(self, category: str) -> list[dict[str, Any]]:
        """Get learnings by category."""
        return [l for l in self.memory.learnings if l.get("category") == category]

    def get_learnings_by_tag(self, tag: str) -> list[dict[str, Any]]:
        """Get learnings by tag."""
        return [l for l in self.memory.learnings if tag in l.get("tags", [])]

    def search_learnings(self, query: str) -> list[dict[str, Any]]:
        """Search learnings by text."""
        query_lower = query.lower()
        return [
            l
            for l in self.memory.learnings
            if query_lower in l.get("title", "").lower()
            or query_lower in l.get("description", "").lower()
            or any(query_lower in tag.lower() for tag in l.get("tags", []))
        ]

    # =========================================================================
    # Audit Trail & Reporting
    # =========================================================================

    def generate_audit_report(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> dict[str, Any]:
        """Generate an audit report for a time period."""
        start = start_date or (datetime.now() - timedelta(days=30))
        end = end_date or datetime.now()

        # Filter history
        history = [e for e in self.memory.task_history if start <= e.timestamp <= end]

        # Count by event type
        events: dict[str, int] = {}
        for entry in history:
            events[entry.event.value] = events.get(entry.event.value, 0) + 1

        # Count by agent
        agents: dict[str, int] = {}
        for entry in history:
            if entry.agent:
                agents[entry.agent] = agents.get(entry.agent, 0) + 1

        # Decisions in period
        decisions = [d for d in self.memory.decisions.values() if start <= d.created_at <= end]

        # Learnings in period
        learnings = [
            l
            for l in self.memory.learnings
            if start <= datetime.fromisoformat(l.get("created_at", "")) <= end
        ]

        return {
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "summary": {
                "total_tasks": len([e for e in history if e.event == TaskEventType.CREATED]),
                "completed": events.get(TaskEventType.COMPLETED.value, 0),
                "failed": events.get(TaskEventType.FAILED.value, 0),
                "blocked": events.get(TaskEventType.BLOCKED.value, 0),
                "retried": events.get(TaskEventType.RETRIED.value, 0),
                "decisions_made": len(decisions),
                "learnings_captured": len(learnings),
            },
            "events": events,
            "agent_activity": agents,
            "decisions": [
                {
                    "id": d.id,
                    "title": d.title,
                    "status": d.status.value,
                    "created_at": d.created_at.isoformat(),
                }
                for d in decisions
            ],
            "failure_patterns": self.get_failure_patterns(30),
            "agent_performance": self.get_agent_performance(30),
        }

    def export_for_documentation(self) -> dict[str, Any]:
        """Export memory for documentation generation."""
        return {
            "decisions": {k: v.model_dump(mode="json") for k, v in self.memory.decisions.items()},
            "recent_history": [
                e.model_dump(mode="json")
                for e in self.get_recent_history(hours=168)  # Last week
            ],
            "capability_snapshots": self.memory.capability_snapshots,
            "learnings": self.memory.learnings,
            "failure_patterns": self.get_failure_patterns(30),
            "agent_performance": self.get_agent_performance(30),
            "exported_at": datetime.now().isoformat(),
        }

    def cleanup_old_data(self, days: int = 90) -> dict[str, int]:
        """Clean up old data beyond retention period."""
        cutoff = datetime.now() - timedelta(days=days)

        # Clean history
        original_count = len(self.memory.task_history)
        self.memory.task_history = [e for e in self.memory.task_history if e.timestamp >= cutoff]
        history_removed = original_count - len(self.memory.task_history)

        # Clean learnings (keep all by default)
        # learnings_removed = 0

        # Re-save
        self.save_all()

        return {
            "history_removed": history_removed,
            "learnings_removed": 0,
            "cutoff_date": cutoff.isoformat(),
        }
