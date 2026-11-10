"""
MyFarmAI Orchestrator - Main Package

Advanced project-aware orchestration system for MyFarmAI.
"""

from .core import OrchestrationResult, OrchestratorCore
from .execution import CheckpointManager, ExecutionContext, ExecutionManager, ExecutionPhase
from .integration import (
    ConflictSeverity,
    ConflictType,
    FileOwnershipTracker,
    IntegrationConflict,
    IntegrationResult,
    IntegrationReviewManager,
)
from .memory import MemoryStorage, ProjectMemoryManager
from .models import (
    AgentAssignment,
    AgentType,
    Capability,
    CapabilityStatus,
    CapabilityType,
    DecisionRecord,
    DecisionStatus,
    HandoffProtocol,
    OrchestrationConfig,
    PermissionTier,
    ProjectMemory,
    ResourceBudget,
    Task,
    TaskEventType,
    TaskGraph,
    TaskHistoryEntry,
    TaskPriority,
    TaskStatus,
    VerificationCheckType,
    VerificationGate,
    VerificationResult,
    create_task_id,
    parse_task_id,
)
from .registry import CapabilityRegistry, DiscoveryResult
from .router import RoutingResult, RoutingRule, RoutingStrategy, SkillToolRouter
from .team_builder import DynamicTeamBuilder, TeamOptimizer, TeamPlan
from .verification import (
    GateResult,
    GateType,
    VerificationCheck,
    VerificationCheckType,
    VerificationSecurityGate,
)

__all__ = [
    # Models
    "Task",
    "TaskStatus",
    "TaskPriority",
    "TaskGraph",
    "OrchestrationConfig",
    "ProjectMemory",
    "Capability",
    "CapabilityType",
    "CapabilityStatus",
    "AgentAssignment",
    "AgentType",
    "VerificationResult",
    "VerificationGate",
    "VerificationCheckType",
    "HandoffProtocol",
    "DecisionRecord",
    "DecisionStatus",
    "TaskHistoryEntry",
    "TaskEventType",
    "ResourceBudget",
    "PermissionTier",
    "create_task_id",
    "parse_task_id",
    # Registry
    "CapabilityRegistry",
    "DiscoveryResult",
    # Core
    "OrchestratorCore",
    "OrchestrationResult",
    # Team Builder
    "DynamicTeamBuilder",
    "TeamPlan",
    "TeamOptimizer",
    # Router
    "SkillToolRouter",
    "RoutingRule",
    "RoutingResult",
    "RoutingStrategy",
    # Execution
    "ExecutionManager",
    "ExecutionContext",
    "ExecutionPhase",
    "CheckpointManager",
    # Integration
    "IntegrationReviewManager",
    "IntegrationConflict",
    "IntegrationResult",
    "ConflictType",
    "ConflictSeverity",
    "FileOwnershipTracker",
    # Verification
    "VerificationSecurityGate",
    "VerificationCheck",
    "GateResult",
    "GateType",
    # Memory
    "ProjectMemoryManager",
    "MemoryStorage",
]

__version__ = "1.0.0"
