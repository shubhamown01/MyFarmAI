"""Research query, source, and citation models."""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class ResearchQueryStatus(str, PyEnum):
    """Research query status."""

    PENDING = "pending"
    SEARCHING = "searching"
    EXTRACTING = "extracting"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchQuery(Base, TimestampMixin, UUIDMixin):
    """Research query initiated by a user."""

    __tablename__ = "research_queries"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Query details
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    status: Mapped[ResearchQueryStatus] = mapped_column(
        SQLEnum(ResearchQueryStatus, native_enum=False),
        default=ResearchQueryStatus.PENDING,
        nullable=False,
    )

    # Results
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Error info
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    sources: Mapped[list["ResearchSource"]] = relationship(
        "ResearchSource",
        back_populates="query",
        cascade="all, delete-orphan",
    )
    citations: Mapped[list["Citation"]] = relationship(
        "Citation",
        back_populates="query",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_research_queries_user_status", "user_id", "status"),
        Index("ix_research_queries_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ResearchQuery(id={self.id}, user_id={self.user_id}, status={self.status})>"


class ResearchSource(Base, TimestampMixin, UUIDMixin):
    """Research source - a web page or document used in research."""

    __tablename__ = "research_sources"

    query_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("research_queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Source metadata
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Content
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Extraction metadata
    extraction_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    extraction_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Licensing/attribution
    license: Mapped[str | None] = mapped_column(String(100), nullable=True)
    attribution_required: Mapped[bool] = mapped_column(default=True, nullable=False)
    robots_compliant: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Quality
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    credibility_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    query: Mapped["ResearchQuery"] = relationship(
        "ResearchQuery",
        back_populates="sources",
    )
    citations: Mapped[list["Citation"]] = relationship(
        "Citation",
        back_populates="source",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_research_sources_query_status", "query_id", "extraction_status"),
        Index("ix_research_sources_domain", "domain"),
    )

    def __repr__(self) -> str:
        return f"<ResearchSource(id={self.id}, query_id={self.query_id}, url={self.url[:50]}...)>"


class Citation(Base, TimestampMixin, UUIDMixin):
    """Citation linking a claim in an answer to a source."""

    __tablename__ = "citations"

    query_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("research_queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("research_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Citation details
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    position_in_answer: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    query: Mapped["ResearchQuery"] = relationship(
        "ResearchQuery",
        back_populates="citations",
    )
    source: Mapped["ResearchSource"] = relationship(
        "ResearchSource",
        back_populates="citations",
    )

    __table_args__ = (
        Index("ix_citations_query_source", "query_id", "source_id"),
    )

    def __repr__(self) -> str:
        return f"<Citation(id={self.id}, query_id={self.query_id}, source_id={self.source_id})>"