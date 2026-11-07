"""Geodesic geometry helpers for land registration (E4, no dependencies).

Owner-approved approach: NO PostGIS — polygons are lists of {lat, lon}
points and area is computed in Python with the spherical-excess formula
(same as turf.js `area`): for each edge,

    dLon = radians(lon2 - lon1)
    p1 = radians(lat1), p2 = radians(lat2)
    total += dLon * (2 + sin(p1) + sin(p2))
    area = abs(total) * R^2 / 2

R = 6371008.8 m (IAU mean Earth radius, same constant turf.js uses).

Limitations (documented per owner approval):
- Self-intersection and bbox-span checks use a simple PLANAR approximation
  on raw degrees. This is acceptable at farm scales (small bounding boxes,
  far from polar regions) but would misbehave for polygons spanning the
  antimeridian or near the poles.
- Area ignores ellipsoidal flattening; expect ~0.1-0.5% deviation from
  professional geodesic tooling.
"""

import math

from typing import Final

# Point as (lat, lon) in decimal degrees.
Point = tuple[float, float]

EARTH_RADIUS_M: Final[float] = 6371008.8  # IAU mean radius, matches turf.js

# Exact test constants (documented in docs/backend/API.md).
SQ_M_PER_SQ_KM: Final[float] = 1_000_000.0
SQ_M_PER_HECTARE: Final[float] = 10_000.0
SQ_M_PER_ACRE: Final[float] = 4046.8564224
SQ_M_PER_SQ_FT: Final[float] = 0.09290304
SQ_M_PER_SQ_YD: Final[float] = 0.83612736

# A polygon whose bounding box spans more than this many degrees is
# rejected as unrealistic for a farm plot.
MAX_BBOX_SPAN_DEGREES: Final[float] = 5.0

# Minimum plausible measured area in m^2 (below this = degenerate polygon).
MIN_AREA_SQ_M: Final[float] = 1.0

_VALID_AREA_UNITS: Final[dict[str, float]] = {
    "sq_m": 1.0,
    "sq_km": SQ_M_PER_SQ_KM,
    "hectare": SQ_M_PER_HECTARE,
    "acre": SQ_M_PER_ACRE,
    "sq_ft": SQ_M_PER_SQ_FT,
    "sq_yd": SQ_M_PER_SQ_YD,
}


def polygon_area_sq_m(polygon: list[Point]) -> float:
    """Geodesic area of a polygon of (lat, lon) points, in square metres.

    Spherical-excess formula (turf.js-style, see module docstring). The
    polygon may be open or closed; the edge from the last point back to
    the first is always included.
    """
    if len(polygon) < 3:
        return 0.0
    total = 0.0
    for i in range(len(polygon)):
        lat1, lon1 = polygon[i]
        lat2, lon2 = polygon[(i + 1) % len(polygon)]
        total += math.radians(lon2 - lon1) * (
            2 + math.sin(math.radians(lat1)) + math.sin(math.radians(lat2))
        )
    return abs(total) * EARTH_RADIUS_M * EARTH_RADIUS_M / 2.0


def _segments_intersect(a1: Point, a2: Point, b1: Point, b2: Point) -> bool:
    """Planar segment intersection on raw degrees (see module docstring)."""
    d = (a2[0] - a1[0], a2[1] - a1[1])
    e = (b2[0] - b1[0], b2[1] - b1[1])
    denom = d[0] * e[1] - d[1] * e[0]
    if denom == 0:
        return False  # parallel/collinear: not a bowtie, skip
    t = ((b1[0] - a1[0]) * e[1] - (b1[1] - a1[1]) * e[0]) / denom
    u = ((b1[0] - a1[0]) * d[1] - (b1[1] - a1[1]) * d[0]) / denom
    return 0 < t < 1 and 0 < u < 1


def validate_polygon(polygon: list[Point]) -> list[str]:
    """Validate a polygon; returns a list of error strings (empty = valid)."""
    errors: list[str] = []
    if len(polygon) < 3:
        return ["polygon must contain at least 3 points"]

    for i, (lat, lon) in enumerate(polygon):
        if not (-90.0 <= lat <= 90.0):
            errors.append(f"point {i}: latitude {lat} out of range [-90, 90]")
        if not (-180.0 <= lon <= 180.0):
            errors.append(f"point {i}: longitude {lon} out of range [-180, 180]")

    # Duplicate consecutive vertices (including wraparound last==first is
    # NOT an error for our area formula, so only check sequential pairs).
    for i in range(len(polygon) - 1):
        if polygon[i] == polygon[i + 1]:
            errors.append(f"point {i} and point {i + 1} are identical")

    unique = set(polygon)
    if len(unique) < 3:
        errors.append("polygon must contain at least 3 unique points")

    if not errors:
        lats = [p[0] for p in polygon]
        lons = [p[1] for p in polygon]
        span = max(lats) - min(lats)
        span_lon = max(lons) - min(lons)
        if max(span, span_lon) > MAX_BBOX_SPAN_DEGREES:
            errors.append(
                f"polygon bounding box spans more than {MAX_BBOX_SPAN_DEGREES} degrees"
            )

        area = polygon_area_sq_m(polygon)
        if area < MIN_AREA_SQ_M:
            errors.append("polygon has negligible (near-zero) area")

        n = len(polygon)
        for i in range(n):
            a1, a2 = polygon[i], polygon[(i + 1) % n]
            for j in range(i + 1, n):
                if j == i or (j + 1) % n == i or (i + 1) % n == j:
                    continue  # adjacent edges share a vertex
                if _segments_intersect(a1, a2, polygon[j], polygon[(j + 1) % n]):
                    errors.append("polygon is self-intersecting")
                    break
            if errors and errors[-1] == "polygon is self-intersecting":
                break

    return errors


def convert_sq_m(value_sq_m: float, unit: str) -> float:
    """Convert a square-metre value to the given area unit."""
    try:
        factor = _VALID_AREA_UNITS[unit]
    except KeyError:
        raise ValueError(f"unknown area unit: {unit}") from None
    return value_sq_m / factor


def to_sq_m(value: float, unit: str) -> float:
    """Convert a value in the given area unit to square metres (inverse)."""
    try:
        factor = _VALID_AREA_UNITS[unit]
    except KeyError:
        raise ValueError(f"unknown area unit: {unit}") from None
    return value * factor


def area_in_all_units(value_sq_m: float) -> dict[str, float]:
    """Convert a square-metre value to every supported area unit."""
    return {unit: convert_sq_m(value_sq_m, unit) for unit in _VALID_AREA_UNITS}
