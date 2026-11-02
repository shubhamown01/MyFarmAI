"""Database models package."""

from app.db.models.audit import AuditEvent, AuditEventType
from app.db.models.base import Base, ModelBase, TimestampMixin, UUIDMixin
from app.db.models.conversation import Conversation, Message, MessageRole
from app.db.models.crop import Crop, CropCategory, CropCycle, CropCycleStatus
from app.db.models.crop_plan import (
    CropPlan,
    CropPlanRevision,
    CropPlanTask,
    CropPlanTaskSource,
    CropPlanTaskStatus,
)
from app.db.models.farm import Farm, FarmMember, FarmRole
from app.db.models.research import Citation, ResearchQuery, ResearchQueryStatus, ResearchSource
from app.db.models.session import RefreshToken, Session
from app.db.models.user import User, UserRole

__all__ = [
    # Base
    "Base",
    "ModelBase",
    "TimestampMixin",
    "UUIDMixin",
    # User
    "User",
    "UserRole",
    # Farm
    "Farm",
    "FarmMember",
    "FarmRole",
    # Crop
    "Crop",
    "CropCategory",
    "CropCycle",
    "CropCycleStatus",
    # Crop planning
    "CropPlan",
    "CropPlanTask",
    "CropPlanTaskSource",
    "CropPlanTaskStatus",
    "CropPlanRevision",
    # Conversation
    "Conversation",
    "Message",
    "MessageRole",
    # Research
    "ResearchQuery",
    "ResearchSource",
    "Citation",
    "ResearchQueryStatus",
    # Audit
    "AuditEvent",
    "AuditEventType",
    # Session
    "Session",
    "RefreshToken",
]
