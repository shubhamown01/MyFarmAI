from fastapi import APIRouter, Query, status

from app.schemas.resources import ResourcesResponse
from app.services.resources import resources_catalogue

router = APIRouter(tags=["Agricultural Resources"])


@router.get(
    "/resources",
    response_model=ResourcesResponse,
    responses={
        400: {"description": "Invalid category filter"},
    },
)
async def list_resources(
    category: str | None = Query(
        None,
        description="Filter by category (e.g., 'schemes', 'advisory', 'market', 'weather', 'research', 'financial', 'digital')",
    ),
) -> ResourcesResponse:
    if category:
        resources = resources_catalogue.get_by_category(category)
    else:
        resources = resources_catalogue.get_all()

    return ResourcesResponse(
        resources=resources,
        total=len(resources),
        categories=resources_catalogue.get_categories(),
    )


@router.get(
    "/resources/categories",
    response_model=list[str],
)
async def list_categories() -> list[str]:
    return resources_catalogue.get_categories()


@router.get(
    "/resources/{category}",
    response_model=ResourcesResponse,
    responses={
        404: {"description": "Category not found"},
    },
)
async def get_resources_by_category(category: str) -> ResourcesResponse:
    resources = resources_catalogue.get_by_category(category)
    if not resources:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "detail": f"Category '{category}' not found",
                "error_code": "CATEGORY_NOT_FOUND",
            },
        )

    return ResourcesResponse(
        resources=resources,
        total=len(resources),
        categories=resources_catalogue.get_categories(),
    )
