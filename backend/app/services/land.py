"""Land registration service (E4): plots, boundaries, area, home locations.

Authorization reuses FarmService's deny-by-default membership checks
(non-members get 404; VIEWER is read-only; plot writes require MEMBER or
OWNER). Polygon validation and geodesic area live in
``app.services.geometry`` — map-measured areas are always server-computed;
manual entries are stored as ``user_reported`` and never silently upgraded
to map-measured.
"""

from datetime import UTC, datetime

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.audit import AuditEventType
from app.db.models.land import (
    FarmAreaMeasurement,
    FarmBoundary,
    FarmPlot,
    HomeLocation,
)
from app.db.repositories import AuditRepository
from app.services.farm import FarmNotFoundError, FarmPermissionError, FarmService
from app.services.geometry import area_in_all_units, polygon_area_sq_m, validate_polygon

__all__ = [
    "FarmNotFoundError",
    "FarmPermissionError",
    "InvalidPolygonError",
    "LandService",
]


class InvalidPolygonError(Exception):
    """Polygon failed geometric validation (self-intersection, zero area...)."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


class LandService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._farms = FarmService(session)
        self._audit = AuditRepository(session)

    async def _authorized_farm(
        self,
        user_id: str,
        farm_id: str,
        *,
        write: bool = False,
    ) -> None:
        if write:
            await self._farms._authorized_farm(user_id, farm_id)  # noqa: SLF001
        else:
            await self._farms.get_farm(user_id, farm_id)  # OWNER/MEMBER/VIEWER

    async def _get_plot(self, farm_id: str, plot_id: str) -> FarmPlot:
        stmt = (
            select(FarmPlot)
            .options(selectinload(FarmPlot.boundary))
            .where(FarmPlot.id == plot_id, FarmPlot.farm_id == farm_id)
        )
        plot = (await self._session.execute(stmt)).scalar_one_or_none()
        if plot is None:
            raise FarmNotFoundError(plot_id)
        return plot

    async def _audit_log(self, description: str, actor_id: str, plot: FarmPlot) -> None:
        await self._audit.log(
            event_type=AuditEventType.FARM_UPDATED,
            event_category="farm",
            description=description,
            actor_id=uuid.UUID(actor_id),
            subject_id=plot.id,
            subject_type="farm_plot",
        )

    # ---------------------------------------------------------------- plots

    async def create_plot(self, user_id: str, farm_id: str, **kwargs: object) -> FarmPlot:
        await self._authorized_farm(user_id, farm_id, write=True)
        plot = FarmPlot(farm_id=farm_id, **kwargs)
        self._session.add(plot)
        await self._session.flush()
        plot.boundary = None  # explicit: avoids a lazy load in async context
        await self._audit_log("plot created", user_id, plot)
        return plot

    async def list_plots(self, user_id: str, farm_id: str) -> list[FarmPlot]:
        await self._authorized_farm(user_id, farm_id)
        stmt = (
            select(FarmPlot)
            .options(selectinload(FarmPlot.boundary))
            .where(FarmPlot.farm_id == farm_id)
            .order_by(FarmPlot.created_at)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_plot(self, user_id: str, farm_id: str, plot_id: str) -> FarmPlot:
        await self._authorized_farm(user_id, farm_id)
        return await self._get_plot(farm_id, plot_id)

    async def update_plot(self, user_id: str, farm_id: str, plot_id: str, **kwargs: object) -> FarmPlot:
        await self._authorized_farm(user_id, farm_id, write=True)
        plot = await self._get_plot(farm_id, plot_id)
        for key, value in kwargs.items():
            setattr(plot, key, value)
        await self._session.flush()
        await self._audit_log("plot updated", user_id, plot)
        return plot

    async def delete_plot(self, user_id: str, farm_id: str, plot_id: str) -> None:
        await self._authorized_farm(user_id, farm_id, write=True)
        plot = await self._get_plot(farm_id, plot_id)
        await self._session.delete(plot)
        await self._session.flush()
        await self._audit_log("plot deleted", user_id, plot)

    # ------------------------------------------------------------- boundary

    async def save_boundary(
        self, user_id: str, farm_id: str, plot_id: str, polygon: list[tuple[float, float]], source: str
    ) -> tuple[FarmBoundary, FarmAreaMeasurement]:
        """Replace the plot's boundary and record a fresh area measurement.

        ``source='map_drawn'`` areas are server-computed (map_measured).
        The polygon is still stored for ``manual_entry`` coordinates, but
        the resulting measurement is marked user_reported: manually typed
        coordinates are not map measurements.
        """
        await self._authorized_farm(user_id, farm_id, write=True)
        plot = await self._get_plot(farm_id, plot_id)

        errors = validate_polygon(polygon)
        if errors:
            raise InvalidPolygonError(errors)

        measured_source = "map_measured" if source == "map_drawn" else "user_reported"
        area_sq_m = polygon_area_sq_m(polygon)

        boundary = plot.boundary
        if boundary is None:
            boundary = FarmBoundary(
                plot_id=plot.id,
                polygon=[{"lat": lat, "lon": lon} for lat, lon in polygon],
                source=source,
                point_count=len(polygon),
            )
            self._session.add(boundary)
            plot.boundary = boundary
        else:
            boundary.polygon = [{"lat": lat, "lon": lon} for lat, lon in polygon]
            boundary.source = source
            boundary.point_count = len(polygon)

        measurement = FarmAreaMeasurement(
            plot_id=plot.id,
            area_sq_m=area_sq_m,
            area_unit="sq_m",
            source=measured_source,
            calculated_at=datetime.now(UTC),
        )
        self._session.add(measurement)
        await self._session.flush()
        await self._audit_log(f"boundary saved ({source})", user_id, plot)
        return boundary, measurement

    # ----------------------------------------------------------- area (manual)

    async def add_user_reported_area(
        self, user_id: str, farm_id: str, plot_id: str, area_sq_m: float, unit: str, confirm: bool
    ) -> FarmAreaMeasurement:
        await self._authorized_farm(user_id, farm_id, write=True)
        plot = await self._get_plot(farm_id, plot_id)
        measurement = FarmAreaMeasurement(
            plot_id=plot.id,
            area_sq_m=area_sq_m,
            area_unit=unit,
            source="user_reported",
            user_confirmed=confirm,
            calculated_at=datetime.now(UTC),
        )
        self._session.add(measurement)
        await self._session.flush()
        await self._audit_log("area reported by user", user_id, plot)
        return measurement

    async def latest_measurement(self, farm_id: str, plot_id: str) -> FarmAreaMeasurement | None:
        stmt = (
            select(FarmAreaMeasurement)
            .where(FarmAreaMeasurement.plot_id == plot_id)
            .order_by(FarmAreaMeasurement.created_at.desc())
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    # -------------------------------------------------------- home location

    async def get_home_location(self, user_id: str) -> HomeLocation | None:
        stmt = select(HomeLocation).where(HomeLocation.user_id == user_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def save_home_location(self, user_id: str, **kwargs: object) -> HomeLocation:
        """Upsert (user_id is unique — one home location per farmer)."""
        home = await self.get_home_location(user_id)
        if home is None:
            home = HomeLocation(user_id=user_id, **kwargs)
            self._session.add(home)
        else:
            for key, value in kwargs.items():
                setattr(home, key, value)
        await self._session.flush()
        return home
