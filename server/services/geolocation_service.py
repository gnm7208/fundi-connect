"""Geolocation and distance calculation service."""

import math


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth (in km).

    Uses Haversine formula.
    """
    if None in (lat1, lon1, lat2, lon2):
        return float("inf")

    # Earth radius in kilometers
    r = 6371.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return round(r * c, 2)


def bounding_box(lat: float, lng: float, radius_km: float) -> tuple[float, float, float, float]:
    """Return (min_lat, max_lat, min_lng, max_lng) enclosing a radius around a point.

    Lets the database discard far-away rows before Haversine refines the result in
    Python, instead of loading every profile on the platform for each search.
    """
    lat_delta = radius_km / 111.0
    # Degrees of longitude shrink towards the poles; guard the equator-adjacent cos.
    lng_delta = radius_km / max(1.0, 111.0 * math.cos(math.radians(lat)))
    return (lat - lat_delta, lat + lat_delta, lng - lng_delta, lng + lng_delta)


def is_within_radius(
    origin_lat: float, origin_lng: float, target_lat: float, target_lng: float, radius_km: float
) -> bool:
    """Determine if target coordinates are within radius_km from origin."""
    dist = calculate_haversine_distance(origin_lat, origin_lng, target_lat, target_lng)
    return dist <= radius_km
