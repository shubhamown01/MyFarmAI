"""Agricultural research API (P5D): verifiable citations via SearXNG.

Auth required; query bounded; provider failures map to 503 RESEARCH_UNAVAILABLE.
No user-supplied URL is ever fetched server-side (SSRF-safe by construction —
see services/research.py).
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.v1.auth import get_current_user_id
from app.core.config import Settings
from app.schemas.research import ResearchResponse, ResearchResultResponse
from app.services.research import ResearchService, ResearchServiceError

router = APIRouter(tags=["Research"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings  # type: ignore[no-any-return]


@router.get("/research", response_model=ResearchResponse)
async def search_research(
    q: str = Query(..., min_length=2, max_length=200),
    limit: int = Query(8, ge=1, le=20),
    settings: Settings = Depends(get_settings),
    user_id: UUID = Depends(get_current_user_id),
) -> ResearchResponse:
    svc = ResearchService(settings)
    try:
        results = await svc.search(q, limit=limit)
    except ResearchServiceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "detail": "research provider unavailable",
                "error_code": "RESEARCH_UNAVAILABLE",
            },
        ) from None
    return ResearchResponse(
        query=q,
        results=[ResearchResultResponse(**r.as_dict()) for r in results],
        provider="searxng",
        retrieved_at=datetime.now(UTC),
    )
