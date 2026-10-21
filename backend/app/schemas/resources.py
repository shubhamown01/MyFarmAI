from pydantic import BaseModel, Field


class AgriculturalResource(BaseModel):
    title: str = Field(..., description="Resource title")
    category: str = Field(..., description="Resource category")
    url: str = Field(..., description="Resource URL")
    source: str = Field(..., description="Source organization")
    description: str = Field(..., description="Short factual description")


class ResourcesListRequest(BaseModel):
    category: str | None = Field(
        default=None,
        description="Filter by category (e.g., 'schemes', 'advisory', 'market', 'weather')",
    )


class ResourcesResponse(BaseModel):
    resources: list[AgriculturalResource]
    total: int
    categories: list[str]
