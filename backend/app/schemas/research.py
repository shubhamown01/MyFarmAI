"""Research API schemas (P5D)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResearchResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rank: int
    title: str
    url: str
    snippet: str
    source_domain: str
    official_source: bool


class ResearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    query: str
    results: list[ResearchResultResponse]
    provider: str
    retrieved_at: datetime
