"""
MyFarmAI Orchestrator - Skill/Tool Router

Matches tasks to relevant skills, plugins, MCP servers, and CLI tools.
Implements routing priority and fallback logic.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .models import Capability, CapabilityType, OrchestrationConfig, PermissionTier, Task
from .registry import CapabilityRegistry


class RoutingStrategy(Enum):
    """Strategy for selecting capabilities."""
    BEST_MATCH = "best_match"           # Highest capability match score
    LEAST_LOADED = "least_loaded"       # Prefer less utilized capabilities
    MOST_SPECIALIZED = "most_specialized"  # Prefer specialized over general
    FASTEST = "fastest"                  # Prefer fastest validation time


@dataclass
class RoutingRule:
    """A routing rule mapping task patterns to capabilities."""
    name: str
    task_patterns: list[str]            # Keywords in task objective/constraints
    required_capabilities: list[str]    # Required capability names
    preferred_capability_type: CapabilityType
    preferred_agent: str | None = None
    preferred_skill: str | None = None
    fallback_agents: list[str] = None
    fallback_skills: list[str] = None
    strategy: RoutingStrategy = RoutingStrategy.BEST_MATCH
    min_match_score: float = 0.3
    tier: PermissionTier = PermissionTier.TIER1_EXISTING


@dataclass
class RoutingResult:
    """Result of routing a task to capabilities."""
    task_id: str
    primary_agent: Capability | None = None
    primary_skill: Capability | None = None
    fallback_agents: list[Capability] = None
    fallback_skills: list[Capability] = None
    mcp_tools: list[Capability] = None
    cli_tools: list[Capability] = None
    matched_rules: list[str] = None
    match_score: float = 0.0
    requires_approval: bool = False
    approval_reason: str | None = None


class SkillToolRouter:
    """
    Routes tasks to appropriate skills, agents, and tools.
    
    Routing Priority:
    1. Existing Skill (exact match for task type)
    2. Existing Agent + Skill (agent with relevant skill loaded)
    3. Existing Agent Only (agent with built-in capability)
    4. MCP Tool (direct MCP server call)
    5. CLI Tool (installed command-line tool)
    6. New Skill Creation (only if TIER3 approved and gap is real)
    """

    def __init__(self, config: OrchestrationConfig, registry: CapabilityRegistry):
        self.config = config
        self.registry = registry
        self.routing_rules = self._build_routing_rules()
        self._routing_cache: dict[str, RoutingResult] = {}

    def _build_routing_rules(self) -> list[RoutingRule]:
        """Build the routing rule table."""
        return [
            # Backend API development
            RoutingRule(
                name="backend_api",
                task_patterns=["api", "endpoint", "fastapi", "backend", "route", "handler"],
                required_capabilities=["backend", "api"],
                preferred_capability_type=CapabilityType.AGENT,
                preferred_agent="backend-engineer",
                preferred_skill="api-contract",
                fallback_agents=["fastapi-developer", "backend-developer"],
                fallback_skills=["openapi", "pr-review"],
                strategy=RoutingStrategy.MOST_SPECIALIZED
            ),

            # Backend database
            RoutingRule(
                name="backend_database",
                task_patterns=["database", "sql", "migration", "schema", "postgresql", "alembic"],
                required_capabilities=["backend", "database"],
                preferred_capability_type=CapabilityType.AGENT,
                preferred_agent="database-administrator",
                preferred_skill="migration",
                fallback_agents=["postgres-pro", "sql-pro", "backend-engineer"],
                fallback_skills=["sql-pro"],
                strategy=RoutingStrategy.MOST_SPECIALIZED
            ),

            # Frontend components
            RoutingRule(
                name="frontend_component",
                task_patterns=["component", "ui", "frontend", "web", "react", "next.js", "tailwind", "shadcn"],
                required_capabilities=["frontend", "ui"],
                preferred_capability_type=CapabilityType.AGENT,
                preferred_agent="frontend-engineer",
                preferred_skill="shadcn",
                fallback_agents=["frontend-developer", "react-specialist", "nextjs-developer"],
                fallback_skills=["ui-styling", "frontend-design", "vercel-composition-patterns"],
                strategy=RoutingStrategy.MOST_SPECIALIZED
            ),

            # Android features
            RoutingRule(
                name="android_feature",
                task_patterns=["android", "mobile", "expo", "react native", "app", "device", "emulator"],
                required_capabilities=["android", "mobile"],
                preferred_capability_type=CapabilityType.AGENT,
                preferred_agent="android-engineer",
                preferred_skill="vercel-react-native-skills",
                fallback_agents=["mobile-developer", "mobile-app-developer", "flutter-expert"],
                fallback_skills=["vercel-react-native-skills"],
                strategy=RoutingStrategy.MOST_SPECIALIZED
            ),

            # AI/ML model integration
            RoutingRule(
                name="ai_ml_integration",
                task_patterns=["model", "ai", "ml", "ollama", "inference", "qwen", "personaplex", "llm", "embedding"],
                required_capabilities=["ai_ml", "model"],
                preferred_capability_type=CapabilityType.AGENT,
                preferred_agent="ai-ml-engineer",
                preferred_skill="google-agents-cli-adk-code",
                fallback_agents=["llm-architect", "machine-learning-engineer", "nlp-engineer"],
                fallback_skills=["google-agents-cli-workflow", "prompt-engineer"],
                strategy=RoutingStrategy.MOST_SPECIALIZED
            ),

            # Research engine
            RoutingRule(
                name="research_engine",
                task_patterns=["research", "search", "searxng", "citation", "extraction", "web search", "source"],
                required_capabilities=["research", "search"],
                preferred_capability_type=CapabilityType.AGENT,
                preferred_agent="research-engineer",
                preferred_skill="searxng",
                fallback_agents=["search-specialist", "data-researcher", "scientific-literature-researcher"],
                fallback_skills=["context7-mcp", "webapp-testing"],
                strategy=RoutingStrategy.MOST_SPECIALIZED
            ),

            # Security audit
            RoutingRule(
                name="security_audit",
                task_patterns=["security", "auth", "secret", "vulnerability", "penetration", "threat", "audit", "owasp"],
                required_capabilities=["security"],
                preferred_capability_type=CapabilityType.AGENT,
                preferred_agent="security-engineer",
                preferred_skill="gstack-cso",
                fallback_agents=["penetration-tester", "security-auditor", "compliance-auditor"],
                fallback_skills=["dependency-audit", "docker-destructive-guardrails"],
                strategy=RoutingStrategy.MOST_SPECIALIZED,
                tier=PermissionTier.TIER3_NEW  # Security changes need approval
            ),

            # QA/Testing
            RoutingRule(
                name="qa_testing",
                task_patterns=["test", "qa", "quality", "lint", "typecheck", "coverage", "regression", "verify", "pytest"],
                required_capabilities=["qa", "test"],
                preferred_capability_type=CapabilityType.AGENT,
                preferred_agent="qa-reviewer",
                preferred_skill="test-patterns",
                fallback_agents=["test-automator", "test-writer", "accessibility-tester"],
                fallback_skills=["webapp-testing", "ci-pipeline"],
                strategy=RoutingStrategy.BEST_MATCH
            ),

            # Deployment
            RoutingRule(
                name="deployment",
                task_patterns=["deploy", "docker", "ci", "cd", "vercel", "kubernetes", "infrastructure", "container"],
                required_capabilities=["deployment"],
                preferred_capability_type=CapabilityType.AGENT,
                preferred_agent="deployment-engineer",
                preferred_skill="deploy-to-vercel",
                fallback_agents=["devops-engineer", "platform-engineer", "kubernetes-specialist"],
                fallback_skills=["docker-build-strategies", "docker-compose-patterns", "ci-pipeline"],
                strategy=RoutingStrategy.MOST_SPECIALIZED,
                tier=PermissionTier.TIER3_NEW  # Deployment changes need approval
            ),

            # Documentation
            RoutingRule(
                name="documentation",
                task_patterns=["doc", "readme", "documentation", "guide", "api doc", "tutorial", "write docs"],
                required_capabilities=["documentation"],
                preferred_capability_type=CapabilityType.AGENT,
                preferred_agent="docs-writer",
                preferred_skill="document-generate",
                fallback_agents=["technical-writer", "content-marketer"],
                fallback_skills=["changelog-generate", "adr-write"],
                strategy=RoutingStrategy.BEST_MATCH
            ),

            # Architecture decisions
            RoutingRule(
                name="architecture",
                task_patterns=["architecture", "design", "adr", "decision", "review", "refactor", "pattern", "trade-off"],
                required_capabilities=["architecture"],
                preferred_capability_type=CapabilityType.AGENT,
                preferred_agent="architect-reviewer",
                preferred_skill="adr-write",
                fallback_agents=["platform-engineer", "cloud-architect", "microservices-architect"],
                fallback_skills=["ce-pov", "ce-plan", "ce-doc-review"],
                strategy=RoutingStrategy.MOST_SPECIALIZED
            ),

            # Debugging
            RoutingRule(
                name="debugging",
                task_patterns=["debug", "error", "trace", "log", "investigate", "fix", "bug", "crash", "failure"],
                required_capabilities=["debugging"],
                preferred_capability_type=CapabilityType.AGENT,
                preferred_agent="debugger",
                preferred_skill="ce-debug",
                fallback_agents=["error-detective", "error-coordinator"],
                fallback_skills=["systematic-debugging", "error-triage"],
                strategy=RoutingStrategy.FASTEST
            ),

            # Performance optimization
            RoutingRule(
                name="performance",
                task_patterns=["performance", "optimize", "slow", "latency", "benchmark", "profile", "memory", "cpu"],
                required_capabilities=["performance"],
                preferred_capability_type=CapabilityType.AGENT,
                preferred_agent="performance-engineer",
                preferred_skill="performance-profile",
                fallback_agents=["vercel-optimize", "database-optimizer"],
                fallback_skills=["vercel-optimize", "performance-optimization"],
                strategy=RoutingStrategy.MOST_SPECIALIZED
            ),
        ]

    async def route_task(self, task: Task) -> RoutingResult:
        """
        Route a task to the best available capabilities.
        
        Returns a RoutingResult with primary and fallback options.
        """
        # Check cache
        cache_key = f"{task.id}:{hash(task.objective)}"
        if cache_key in self._routing_cache:
            return self._routing_cache[cache_key]

        # Find matching rules
        matched_rules = []
        for rule in self.routing_rules:
            if self._rule_matches_task(rule, task):
                matched_rules.append(rule.name)

        if not matched_rules:
            # No specific rule matched - use general routing
            result = await self._general_routing(task)
        else:
            # Use best matching rule
            best_rule = max(
                (r for r in self.routing_rules if r.name in matched_rules),
                key=lambda r: self._calculate_rule_match_score(r, task)
            )
            result = await self._apply_routing_rule(task, best_rule)

        result.matched_rules = matched_rules
        self._routing_cache[cache_key] = result
        return result

    def _rule_matches_task(self, rule: RoutingRule, task: Task) -> bool:
        """Check if a routing rule matches a task."""
        text = f"{task.objective} {' '.join(task.constraints)} {' '.join(task.files_involved)}".lower()
        return any(pattern.lower() in text for pattern in rule.task_patterns)

    def _calculate_rule_match_score(self, rule: RoutingRule, task: Task) -> float:
        """Calculate how well a rule matches a task (0-1)."""
        text = f"{task.objective} {' '.join(task.constraints)}".lower()
        matches = sum(1 for pattern in rule.task_patterns if pattern.lower() in text)
        return matches / len(rule.task_patterns)

    async def _apply_routing_rule(self, task: Task, rule: RoutingRule) -> RoutingResult:
        """Apply a routing rule to find capabilities."""
        result = RoutingResult(
            task_id=task.id,
            fallback_agents=[],
            fallback_skills=[],
            mcp_tools=[],
            cli_tools=[],
        )

        # Find primary agent
        if rule.preferred_agent:
            agent = self.registry.get_capability(rule.preferred_agent)
            if agent and agent.is_usable():
                result.primary_agent = agent
            else:
                # Try fallbacks
                for fallback in rule.fallback_agents or []:
                    agent = self.registry.get_capability(fallback)
                    if agent and agent.is_usable():
                        result.primary_agent = agent
                        break

        # Find primary skill
        if rule.preferred_skill:
            skill = self.registry.get_capability(rule.preferred_skill)
            if skill and skill.is_usable():
                result.primary_skill = skill
            else:
                # Try fallbacks
                for fallback in rule.fallback_skills or []:
                    skill = self.registry.get_capability(fallback)
                    if skill and skill.is_usable():
                        result.primary_skill = skill
                        break

        # Find MCP tools if needed
        if "mcp" in task.constraints or rule.name in ["research_engine", "ai_ml_integration"]:
            mcp_caps = self.registry.get_capabilities_by_type(CapabilityType.MCP)
            result.mcp_tools = [c for c in mcp_caps if c.is_usable()]

        # Find CLI tools if needed
        cli_caps = self.registry.get_capabilities_by_type(CapabilityType.CLI)
        result.cli_tools = [c for c in cli_caps if c.is_usable()][:5]  # Limit

        # Calculate match score
        if result.primary_agent:
            result.match_score = 0.8
        if result.primary_skill:
            result.match_score = max(result.match_score, 0.9)

        # Check approval requirement
        if rule.tier in (PermissionTier.TIER3_NEW, PermissionTier.TIER4_DESTRUCTIVE):
            result.requires_approval = True
            result.approval_reason = f"Task requires {rule.tier.value} permission"

        return result

    async def _general_routing(self, task: Task) -> RoutingResult:
        """General routing when no specific rule matches."""
        result = RoutingResult(task_id=task.id)

        # Infer required capabilities
        required = self._infer_capabilities_from_task(task)

        # Find best agent
        result.primary_agent = self.registry.find_best_agent_for_task(required)

        # Find relevant skills
        skills = self.registry.get_capabilities_by_type(CapabilityType.SKILL)
        usable_skills = [s for s in skills if s.is_usable()]

        # Match skills to required capabilities
        for skill in usable_skills:
            if any(req in skill.capabilities for req in required):
                if not result.primary_skill:
                    result.primary_skill = skill
                else:
                    result.fallback_skills.append(skill)

        # Get MCP and CLI tools
        mcp_caps = self.registry.get_capabilities_by_type(CapabilityType.MCP)
        result.mcp_tools = [c for c in mcp_caps if c.is_usable()]

        cli_caps = self.registry.get_capabilities_by_type(CapabilityType.CLI)
        result.cli_tools = [c for c in cli_caps if c.is_usable()][:5]

        return result

    def _infer_capabilities_from_task(self, task: Task) -> list[str]:
        """Infer required capabilities from task (shared with team builder)."""
        caps = []
        text = f"{task.objective} {' '.join(task.constraints)} {' '.join(task.files_involved)}".lower()

        capability_keywords = {
            "backend": ["backend", "api", "fastapi", "database", "sql", "migration", "endpoint"],
            "frontend": ["frontend", "web", "react", "next.js", "ui", "component", "tailwind"],
            "android": ["android", "mobile", "expo", "react native", "app", "device"],
            "ai_ml": ["model", "ai", "ml", "ollama", "inference", "qwen", "personaplex"],
            "research": ["research", "search", "searxng", "citation", "extraction", "web search"],
            "security": ["security", "auth", "secret", "vulnerability", "penetration", "threat"],
            "qa": ["test", "qa", "quality", "lint", "typecheck", "coverage", "regression"],
            "deployment": ["deploy", "docker", "ci", "cd", "vercel", "kubernetes", "infrastructure"],
            "documentation": ["doc", "readme", "documentation", "guide", "api doc"],
            "architecture": ["architecture", "design", "adr", "decision", "review", "refactor"],
            "debugging": ["debug", "error", "trace", "log", "investigate", "fix", "bug"],
            "performance": ["performance", "optimize", "slow", "latency", "benchmark", "profile"],
        }

        for cap, keywords in capability_keywords.items():
            if any(kw in text for kw in keywords):
                caps.append(cap)

        return caps if caps else ["general"]

    def get_routing_table(self) -> list[dict[str, Any]]:
        """Get the routing table for documentation."""
        return [
            {
                "name": rule.name,
                "patterns": rule.task_patterns,
                "required_capabilities": rule.required_capabilities,
                "preferred_agent": rule.preferred_agent,
                "preferred_skill": rule.preferred_skill,
                "fallback_agents": rule.fallback_agents or [],
                "fallback_skills": rule.fallback_skills or [],
                "strategy": rule.strategy.value,
                "tier": rule.tier.value,
            }
            for rule in self.routing_rules
        ]

    def add_custom_rule(self, rule: RoutingRule) -> None:
        """Add a custom routing rule (for dynamic extension)."""
        self.routing_rules.insert(0, rule)  # Custom rules take priority
        self._routing_cache.clear()

    def clear_cache(self) -> None:
        """Clear routing cache."""
        self._routing_cache.clear()
