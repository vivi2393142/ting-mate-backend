import math


def to_rad(degrees: float) -> float:
    """Convert degrees to radians."""
    return degrees * math.pi / 180


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two points on Earth using the Haversine formula.

    Args:
        lat1: Latitude of first point in degrees
        lon1: Longitude of first point in degrees
        lat2: Latitude of second point in degrees
        lon2: Longitude of second point in degrees

    Returns:
        Distance in kilometers
    """
    r = 6371  # Earth's radius in kilometers
    d_lat = to_rad(lat2 - lat1)
    d_lon = to_rad(lon2 - lon1)
    a = math.sin(d_lat / 2) * math.sin(d_lat / 2) + math.cos(to_rad(lat1)) * math.cos(
        to_rad(lat2)
    ) * math.sin(d_lon / 2) * math.sin(d_lon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = r * c  # Distance in kilometers
    return d


def is_within_safe_zone(
    user_lat: float,
    user_lon: float,
    safe_zone_lat: float,
    safe_zone_lon: float,
    safe_zone_radius_meters: int,
) -> bool:
    """
    Check if a user's location is within their safe zone.

    Args:
        user_lat: User's current latitude
        user_lon: User's current longitude
        safe_zone_lat: Safe zone center latitude
        safe_zone_lon: Safe zone center longitude
        safe_zone_radius_meters: Safe zone radius in meters

    Returns:
        True if user is within safe zone, False otherwise
    """
    distance_km = calculate_distance(user_lat, user_lon, safe_zone_lat, safe_zone_lon)
    safe_zone_radius_km = safe_zone_radius_meters / 1000
    return distance_km <= safe_zone_radius_km
