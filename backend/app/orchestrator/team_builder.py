"""
MyFarmAI Orchestrator - Dynamic Team Builder

Selects the smallest effective team for each task, creates task-specific assignments
from existing specialist agents, and manages parallel execution groups.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from .models import (
    AgentAssignment,
    AgentType,
    CapabilityType,
    HandoffProtocol,
    OrchestrationConfig,
    Task,
    TaskGraph,
)
from .registry import CapabilityRegistry


@dataclass
class TeamPlan:
    """Plan for executing a set of tasks with assigned agents."""

    assignments: list[AgentAssignment]
    parallel_groups: dict[int, list[str]]  # group_id -> task_ids
    execution_order: list[list[str]]  # List of parallel groups in order
    resource_requirements: dict[str, int]
    estimated_duration_ms: int


class DynamicTeamBuilder:
    """
    Builds optimal teams for task execution.

    Principles:
    - Select smallest effective team
    - Reuse existing agents before creating new ones
    - Single accountable owner per task
    - Parallel execution for independent work
    - Concurrency limits based on resources
    - Prevent recursive delegation
    """

    def __init__(self, config: OrchestrationConfig, registry: CapabilityRegistry):
        self.config = config
        self.registry = registry
        self._agent_load: dict[str, int] = defaultdict(int)  # agent -> active task count
        self._delegation_depth: dict[str, int] = defaultdict(int)  # task_id -> depth
        self._max_delegation_depth = 3

    def build_team_for_tasks(
        self, tasks: list[Task], task_graph: TaskGraph, max_parallel: int | None = None
    ) -> TeamPlan:
        """
        Build a complete team plan for a set of tasks.

        Args:
            tasks: Tasks to plan for
            task_graph: Full task graph for dependency analysis
            max_parallel: Override max parallel agents

        Returns:
            TeamPlan with assignments and execution order
        """
        max_parallel = max_parallel or self.config.resource_budget.max_parallel_agents

        # Step 1: Assign agents to each task
        assignments = []
        for task in tasks:
            assignment = self._assign_agent_to_task(task, task_graph)
            if assignment:
                assignments.append(assignment)
                self._agent_load[assignment.agent_name] += 1

        # Step 2: Build parallel groups based on dependencies
        parallel_groups = self._build_parallel_groups(tasks, task_graph)

        # Step 3: Create execution order (topological sort of groups)
        execution_order = self._create_execution_order(parallel_groups, task_graph)

        # Step 4: Calculate resource requirements
        resource_reqs = self._calculate_resource_requirements(assignments)

        # Step 5: Estimate duration
        estimated_duration = self._estimate_duration(execution_order, assignments)

        return TeamPlan(
            assignments=assignments,
            parallel_groups=parallel_groups,
            execution_order=execution_order,
            resource_requirements=resource_reqs,
            estimated_duration_ms=estimated_duration,
        )

    def _assign_agent_to_task(self, task: Task, task_graph: TaskGraph) -> AgentAssignment | None:
        """Assign the best available agent to a task."""
        # Determine required capabilities from task
        required_caps = self._infer_required_capabilities(task)

        # Find best matching agent
        best_agent = self.registry.find_best_agent_for_task(required_caps)

        if not best_agent:
            # No suitable existing agent - would need Tier 3 approval to create new
            return None

        # Check delegation depth to prevent loops
        task_key = f"{task.id}"
        if self._delegation_depth.get(task_key, 0) >= self._max_delegation_depth:
            return None

        # Determine parallel group
        parallel_group = self._determine_parallel_group(task, task_graph)

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
            context_refs=self._get_context_refs(task),
        )

        # Create assignment
        assignment = AgentAssignment(
            task_id=task.id,
            agent_name=best_agent.name,
            agent_type=AgentType.EXISTING,
            scope=task.files_involved,
            parallel_group=parallel_group,
            handoff=handoff.model_dump(),
        )

        # Update task with assignment
        task.assigned_agent = best_agent.name
        task.parallel_group = parallel_group

        return assignment

    def _infer_required_capabilities(self, task: Task) -> list[str]:
        """Infer required capabilities from task properties."""
        caps = []

        # From constraints
        for constraint in task.constraints:
            constraint_lower = constraint.lower()
            if any(kw in constraint_lower for kw in ["backend", "api", "fastapi", "database"]):
                caps.append("backend")
            if any(kw in constraint_lower for kw in ["frontend", "web", "react", "ui"]):
                caps.append("frontend")
            if any(kw in constraint_lower for kw in ["android", "mobile", "expo"]):
                caps.append("android")
            if any(kw in constraint_lower for kw in ["model", "ai", "ollama", "inference"]):
                caps.append("ai_ml")
            if any(kw in constraint_lower for kw in ["research", "search", "searxng"]):
                caps.append("research")
            if any(kw in constraint_lower for kw in ["security", "auth", "secret"]):
                caps.append("security")
            if any(kw in constraint_lower for kw in ["test", "qa", "lint", "typecheck"]):
                caps.append("qa")
            if any(kw in constraint_lower for kw in ["deploy", "docker", "ci", "cd"]):
                caps.append("deployment")
            if any(kw in constraint_lower for kw in ["doc", "readme", "documentation"]):
                caps.append("documentation")
            if any(kw in constraint_lower for kw in ["architecture", "design", "adr"]):
                caps.append("architecture")

        # From files involved
        for file_path in task.files_involved:
            file_lower = file_path.lower()
            if "backend" in file_lower or file_lower.startswith("backend/"):
                caps.append("backend")
            if "web" in file_lower or "frontend" in file_lower or file_lower.startswith("web/"):
                caps.append("frontend")
            if "android" in file_lower or file_lower.startswith("android/"):
                caps.append("android")

        # From objective
        obj_lower = task.objective.lower()
        if any(kw in obj_lower for kw in ["api", "endpoint", "backend", "database"]):
            caps.append("backend")
        if any(kw in obj_lower for kw in ["ui", "component", "page", "frontend", "web"]):
            caps.append("frontend")
        if any(kw in obj_lower for kw in ["mobile", "android", "app", "device"]):
            caps.append("android")
        if any(kw in obj_lower for kw in ["model", "ai", "inference", "ollama"]):
            caps.append("ai_ml")
        if any(kw in obj_lower for kw in ["research", "search", "citation"]):
            caps.append("research")
        if any(kw in obj_lower for kw in ["security", "auth", "vulnerability"]):
            caps.append("security")
        if any(kw in obj_lower for kw in ["test", "qa", "quality"]):
            caps.append("qa")
        if any(kw in obj_lower for kw in ["deploy", "docker", "ci", "cd"]):
            caps.append("deployment")
        if any(kw in obj_lower for kw in ["doc", "document", "readme"]):
            caps.append("documentation")
        if any(kw in obj_lower for kw in ["architecture", "design", "adr", "decision"]):
            caps.append("architecture")

        return list(set(caps)) if caps else ["general"]

    def _determine_parallel_group(self, task: Task, task_graph: TaskGraph) -> int:
        """Determine which parallel group a task belongs to."""
        # Tasks with no dependencies can run in group 0
        if not task.dependencies:
            return 0

        # Find the max group of dependencies + 1
        max_group = -1
        for dep_id in task.dependencies:
            dep_task = task_graph.tasks.get(dep_id)
            if dep_task and dep_task.parallel_group is not None:
                max_group = max(max_group, dep_task.parallel_group)

        return max_group + 1

    def _build_parallel_groups(
        self, tasks: list[Task], task_graph: TaskGraph
    ) -> dict[int, list[str]]:
        """Build parallel groups from tasks."""
        groups: dict[int, list[str]] = defaultdict(list)

        for task in tasks:
            group = task.parallel_group if task.parallel_group is not None else 0
            groups[group].append(task.id)

        return dict(groups)

    def _create_execution_order(
        self, parallel_groups: dict[int, list[str]], task_graph: TaskGraph
    ) -> list[list[str]]:
        """Create execution order as list of parallel groups."""
        if not parallel_groups:
            return []

        max_group = max(parallel_groups.keys())
        order = []

        for group_id in range(max_group + 1):
            if group_id in parallel_groups:
                # Filter to only tasks that are ready (deps satisfied)
                ready_tasks = []
                for task_id in parallel_groups[group_id]:
                    task = task_graph.tasks.get(task_id)
                    if task:
                        ready_tasks.append(task_id)
                if ready_tasks:
                    order.append(ready_tasks)

        return order

    def _calculate_resource_requirements(
        self, assignments: list[AgentAssignment]
    ) -> dict[str, int]:
        """Calculate resource requirements for assignments."""
        reqs = {
            "agents": len(set(a.agent_name for a in assignments)),
            "max_parallel": max((a.parallel_group for a in assignments), default=0) + 1,
        }

        # Count special resource needs
        model_agents = {"ai-ml-engineer", "research-engineer"}
        docker_agents = {"deployment-engineer", "devops-engineer", "backend-engineer"}
        test_agents = {"qa-reviewer", "test-automator"}

        reqs["model_slots"] = sum(1 for a in assignments if a.agent_name in model_agents)
        reqs["docker_build_slots"] = sum(1 for a in assignments if a.agent_name in docker_agents)
        reqs["test_slots"] = sum(1 for a in assignments if a.agent_name in test_agents)

        return reqs

    def _estimate_duration(
        self, execution_order: list[list[str]], assignments: list[AgentAssignment]
    ) -> int:
        """Estimate total execution duration in milliseconds."""
        # Base estimates per agent type (in seconds)
        agent_base_time = {
            "backend-engineer": 120,
            "frontend-engineer": 180,
            "android-engineer": 180,
            "ai-ml-engineer": 240,
            "research-engineer": 180,
            "security-engineer": 120,
            "qa-reviewer": 60,
            "release-coordinator": 60,
            "architect-reviewer": 60,
            "docs-writer": 60,
            "deployment-engineer": 120,
            "database-administrator": 120,
        }

        total_seconds = 0
        for group in execution_order:
            group_max = 0
            for task_id in group:
                assignment = next((a for a in assignments if a.task_id == task_id), None)
                if assignment:
                    base_time = agent_base_time.get(assignment.agent_name, 120)
                    group_max = max(group_max, base_time)
            total_seconds += group_max

        return total_seconds * 1000  # Convert to ms

    def _get_context_refs(self, task: Task) -> list[str]:
        """Get relevant context references for a task."""
        refs = []
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

    def get_agent_load(self) -> dict[str, int]:
        """Get current load per agent."""
        return dict(self._agent_load)

    def release_agent(self, agent_name: str) -> None:
        """Release an agent (decrement load)."""
        if agent_name in self._agent_load:
            self._agent_load[agent_name] = max(0, self._agent_load[agent_name] - 1)

    def can_delegate_to(self, agent_name: str, task_id: str) -> bool:
        """Check if we can delegate to an agent (prevent loops, check load)."""
        # Check load
        max_load = 3  # Max concurrent tasks per agent
        if self._agent_load.get(agent_name, 0) >= max_load:
            return False

        # Check delegation depth
        if self._delegation_depth.get(task_id, 0) >= self._max_delegation_depth:
            return False

        return True

    def increment_delegation_depth(self, task_id: str) -> None:
        """Increment delegation depth for a task chain."""
        self._delegation_depth[task_id] = self._delegation_depth.get(task_id, 0) + 1

    def suggest_team_for_objective(self, objective: str, context: dict[str, Any]) -> dict[str, Any]:
        """
        Suggest a team composition for a high-level objective.
        Used for planning before task decomposition.
        """
        required_caps = self._analyze_objective_for_team(objective)
        available_agents = self.registry.get_capabilities_by_type(CapabilityType.AGENT)
        usable_agents = [a for a in available_agents if a.is_usable()]

        suggestions = []
        for cap in required_caps:
            matches = [a for a in usable_agents if cap in a.capabilities]
            if matches:
                best = max(matches, key=lambda a: len(set(a.capabilities) & set(required_caps)))
                suggestions.append(
                    {
                        "capability_area": cap,
                        "recommended_agent": best.name,
                        "agent_capabilities": best.capabilities,
                        "status": best.status.value,
                    }
                )
            else:
                suggestions.append(
                    {
                        "capability_area": cap,
                        "recommended_agent": None,
                        "gap": True,
                        "message": f"No available agent for {cap}",
                    }
                )

        return {
            "objective": objective,
            "required_capabilities": required_caps,
            "suggested_team": suggestions,
            "estimated_agents": len([s for s in suggestions if s["recommended_agent"]]),
            "gaps": [s for s in suggestions if s.get("gap")],
        }

    def _analyze_objective_for_team(self, objective: str) -> list[str]:
        """Analyze objective for team planning (more detailed than task decomposition)."""
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
                "server",
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
                "tailwind",
            ],
            "android": ["android", "mobile", "expo", "react native", "app", "device", "emulator"],
            "ai_ml": [
                "model",
                "ai",
                "ml",
                "ollama",
                "inference",
                "qwen",
                "personaplex",
                "training",
                "llm",
            ],
            "research": [
                "research",
                "search",
                "searxng",
                "citation",
                "extraction",
                "web search",
                "source",
            ],
            "security": [
                "security",
                "auth",
                "secret",
                "vulnerability",
                "penetration",
                "threat",
                "audit",
            ],
            "qa": [
                "test",
                "qa",
                "quality",
                "lint",
                "typecheck",
                "coverage",
                "regression",
                "verify",
            ],
            "deployment": [
                "deploy",
                "docker",
                "ci",
                "cd",
                "vercel",
                "kubernetes",
                "infrastructure",
                "container",
            ],
            "documentation": ["doc", "readme", "documentation", "guide", "api doc", "tutorial"],
            "architecture": [
                "architecture",
                "design",
                "adr",
                "decision",
                "review",
                "refactor",
                "pattern",
            ],
        }

        for area, keywords in capability_keywords.items():
            if any(kw in obj_lower for kw in keywords):
                areas.append(area)

        return areas if areas else ["general"]


class TeamOptimizer:
    """Optimizes team composition for efficiency."""

    def __init__(self, team_builder: DynamicTeamBuilder):
        self.team_builder = team_builder

    def optimize_for_parallelism(self, plan: TeamPlan) -> TeamPlan:
        """Optimize plan for maximum parallelism within resource constraints."""
        # Re-assign tasks to balance load across agents
        # This is a simplified version - full implementation would use constraint solving
        return plan

    def optimize_for_specialization(self, plan: TeamPlan) -> TeamPlan:
        """Optimize plan to use most specialized agents."""
        # Re-assign tasks to agents with best capability match
        return plan

    def minimize_context_switching(self, plan: TeamPlan) -> TeamPlan:
        """Minimize context switching by grouping related tasks per agent."""
        return plan
