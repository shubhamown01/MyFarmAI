"""Land registration API endpoints (E4): plots, boundaries, areas, home location.

All endpoints require an authenticated user whose verification_status is
'active' (``require_verified_user`` — the E3 gate, first wired here).
Polygon area is always computed server-side (directive §7.4: no degree
arithmetic, no client-trusted area). Map-measured areas are labelled
map_measured; manual entries stay user_reported.
"""

import uuid

from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.v1.auth import require_verified_user
from app.core.config import Settings
from app.services.geometry import area_in_all_units, to_sq_m

from app.db.models.land import FarmAreaMeasurement, FarmBoundary, FarmPlot, HomeLocation
from app.db.session import db_manager
from app.schemas.land import (
    AreaMeasurementResponse,
    BoundaryResponse,
    BoundarySave,
    HomeLocationResponse,
    HomeLocationSave,
    PlotCreate,
    PlotResponse,
    PlotUpdate,
    PolygonPoint,
    UserReportedArea,
)
from app.services.farm import FarmNotFoundError, FarmPermissionError
from app.services.land import InvalidPolygonError, LandService

router = APIRouter(tags=["Land"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings  # type: ignore[no-any-return]


async def get_land_service() -> AsyncIterator[LandService]:
    async with db_manager.session() as session:
        yield LandService(session)


def _http_404() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"detail": "farm or plot not found", "error_code": "NOT_FOUND"},
    )


def _http_403() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"detail": "insufficient farm role", "error_code": "FARM_FORBIDDEN"},
    )


def _boundary_response(b: FarmBoundary) -> BoundaryResponse:
    return BoundaryResponse(
        polygon=[PolygonPoint(lat=p["lat"], lon=p["lon"]) for p in b.polygon],
        source=b.source,
        point_count=b.point_count,
        created_at=b.created_at,
    )


def _measurement_response(m: FarmAreaMeasurement) -> AreaMeasurementResponse:
    return AreaMeasurementResponse(
        id=m.id,
        plot_id=m.plot_id,
        area_sq_m=m.area_sq_m,
        area_unit=m.area_unit,
        source=m.source,
        user_confirmed=m.user_confirmed,
        calculated_at=m.calculated_at,
        conversions=area_in_all_units(m.area_sq_m),
    )


def _plot_response(plot: FarmPlot, measurement: FarmAreaMeasurement | None) -> PlotResponse:
    return PlotResponse(
        id=plot.id,
        farm_id=plot.farm_id,
        name=plot.name,
        land_type=plot.land_type,
        notes=plot.notes,
        boundary=_boundary_response(plot.boundary) if plot.boundary else None,
        latest_measurement=_measurement_response(measurement) if measurement else None,
        created_at=plot.created_at,
        updated_at=plot.updated_at,
    )


@router.post("/farms/{farm_id}/plots", response_model=PlotResponse, status_code=status.HTTP_201_CREATED)
async def create_plot(
    farm_id: uuid.UUID,
    data: PlotCreate,
    service: LandService = Depends(get_land_service),
    user_id: uuid.UUID = Depends(require_verified_user),
) -> PlotResponse:
    try:
        plot = await service.create_plot(str(user_id), str(farm_id), **data.model_dump())
    except FarmNotFoundError:
        raise _http_404() from None
    except FarmPermissionError:
        raise _http_403() from None
    return _plot_response(plot, None)


@router.get("/farms/{farm_id}/plots", response_model=list[PlotResponse])
async def list_plots(
    farm_id: uuid.UUID,
    service: LandService = Depends(get_land_service),
    user_id: uuid.UUID = Depends(require_verified_user),
) -> list[PlotResponse]:
    try:
        plots = await service.list_plots(str(user_id), str(farm_id))
    except FarmNotFoundError:
        raise _http_404() from None
    result = []
    for plot in plots:
        m = await service.latest_measurement(str(farm_id), str(plot.id))
        result.append(_plot_response(plot, m))
    return result


@router.get("/farms/{farm_id}/plots/{plot_id}", response_model=PlotResponse)
async def get_plot(
    farm_id: uuid.UUID,
    plot_id: uuid.UUID,
    service: LandService = Depends(get_land_service),
    user_id: uuid.UUID = Depends(require_verified_user),
) -> PlotResponse:
    try:
        plot = await service.get_plot(str(user_id), str(farm_id), str(plot_id))
    except FarmNotFoundError:
        raise _http_404() from None
    m = await service.latest_measurement(str(farm_id), str(plot.id))
    return _plot_response(plot, m)


@router.patch("/farms/{farm_id}/plots/{plot_id}", response_model=PlotResponse)
async def update_plot(
    farm_id: uuid.UUID,
    plot_id: uuid.UUID,
    data: PlotUpdate,
    service: LandService = Depends(get_land_service),
    user_id: uuid.UUID = Depends(require_verified_user),
) -> PlotResponse:
    try:
        plot = await service.update_plot(
            str(user_id), str(farm_id), str(plot_id), **data.model_dump(exclude_unset=True)
        )
    except FarmNotFoundError:
        raise _http_404() from None
    except FarmPermissionError:
        raise _http_403() from None
    m = await service.latest_measurement(str(farm_id), str(plot.id))
    return _plot_response(plot, m)


@router.delete("/farms/{farm_id}/plots/{plot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plot(
    farm_id: uuid.UUID,
    plot_id: uuid.UUID,
    service: LandService = Depends(get_land_service),
    user_id: uuid.UUID = Depends(require_verified_user),
) -> None:
    try:
        await service.delete_plot(str(user_id), str(farm_id), str(plot_id))
    except FarmNotFoundError:
        raise _http_404() from None
    except FarmPermissionError:
        raise _http_403() from None


@router.put("/farms/{farm_id}/plots/{plot_id}/boundary", response_model=PlotResponse)
async def save_boundary(
    farm_id: uuid.UUID,
    plot_id: uuid.UUID,
    data: BoundarySave,
    service: LandService = Depends(get_land_service),
    user_id: uuid.UUID = Depends(require_verified_user),
) -> PlotResponse:
    try:
        plot = await service.get_plot(str(user_id), str(farm_id), str(plot_id))
        await service.save_boundary(
            str(user_id),
            str(farm_id),
            str(plot_id),
            polygon=[(p.lat, p.lon) for p in data.polygon],
            source=data.source,
        )
    except InvalidPolygonError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"detail": "invalid polygon", "error_code": "INVALID_POLYGON", "errors": e.errors},
        ) from None
    except FarmNotFoundError:
        raise _http_404() from None
    except FarmPermissionError:
        raise _http_403() from None
    m = await service.latest_measurement(str(farm_id), str(plot.id))
    return _plot_response(plot, m)


@router.post(
    "/farms/{farm_id}/plots/{plot_id}/area",
    response_model=AreaMeasurementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def report_area(
    farm_id: uuid.UUID,
    plot_id: uuid.UUID,
    data: UserReportedArea,
    service: LandService = Depends(get_land_service),
    user_id: uuid.UUID = Depends(require_verified_user),
) -> AreaMeasurementResponse:
    """Manual area entry (user_reported — never presented as map-measured)."""
    try:
        m = await service.add_user_reported_area(
            str(user_id),
            str(farm_id),
            str(plot_id),
            area_sq_m=to_sq_m(data.area_value, data.area_unit),
            unit=data.area_unit,
            confirm=data.confirm,
        )
    except (FarmNotFoundError, ValueError):
        raise _http_404() from None
    except FarmPermissionError:
        raise _http_403() from None
    return _measurement_response(m)


@router.get("/me/home-location", response_model=HomeLocationResponse)
async def get_home_location(
    service: LandService = Depends(get_land_service),
    user_id: uuid.UUID = Depends(require_verified_user),
) -> HomeLocationResponse:
    home = await service.get_home_location(str(user_id))
    if home is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "home location not set", "error_code": "HOME_LOCATION_NOT_SET"},
        )
    return HomeLocationResponse.model_validate(home)


@router.put("/me/home-location", response_model=HomeLocationResponse)
async def save_home_location(
    data: HomeLocationSave,
    service: LandService = Depends(get_land_service),
    user_id: uuid.UUID = Depends(require_verified_user),
) -> HomeLocationResponse:
    home = await service.save_home_location(str(user_id), **data.model_dump())
    return HomeLocationResponse.model_validate(home)
