import math
from statistics import median

from .models import LatLon

EARTH_RADIUS_M = 6_371_000


def dist_m(a: LatLon, b: LatLon) -> float:
    """Great-circle (haversine) distance in metres."""
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dp, dl = p2 - p1, math.radians(b.lon - a.lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


def median_point(points: list[LatLon]) -> LatLon:
    return LatLon(lat=median(p.lat for p in points), lon=median(p.lon for p in points))


def filter_outliers(points: list[LatLon], max_m: float) -> list[LatLon]:
    """Drop points further than max_m from the median of all points."""
    if len(points) < 3:
        return points
    centre = median_point(points)
    return [p for p in points if dist_m(p, centre) <= max_m]
