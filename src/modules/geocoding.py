from __future__ import annotations

import logging
import random
import time

import requests

logger = logging.getLogger(__name__)

class GeocodingError(RuntimeError):
    pass

def geocode_locations(
    locations: list[str],
    api_key: str | None = None,
    provider: str = "mock",
) -> dict[str, tuple[float, float]]:
    """
    Given a list of location strings, return a mapping of location -> (latitude, longitude).
    If provider is 'locationiq' and api_key is provided, uses LocationIQ Geocoding API.
    Otherwise, uses a mock fallback that returns random coordinates near Delhi, India (for the demo).
    """
    unique_locations = list(set(loc for loc in locations if loc and loc.strip()))
    results = {}

    if provider.lower() == "locationiq" and api_key:
        for loc in unique_locations:
            try:
                lat, lng = _geocode_locationiq(loc, api_key)
                if lat is not None and lng is not None:
                    results[loc] = (lat, lng)
            except Exception as e:
                logger.warning(f"Failed to geocode '{loc}' with LocationIQ: {e}")
                results[loc] = _mock_geocode(loc)
            time.sleep(0.4) # Small delay to respect LocationIQ 2 requests/sec free limit
    else:
        for loc in unique_locations:
            results[loc] = _mock_geocode(loc)

    return results

def _geocode_locationiq(address: str, api_key: str) -> tuple[float | None, float | None]:
    url = "https://us1.locationiq.com/v1/search"
    params = {
        "key": api_key,
        "q": address,
        "format": "json"
    }
    response = requests.get(url, params=params, timeout=10)
    
    if not response.ok:
        raise GeocodingError(f"HTTP Error: {response.status_code}")
        
    data = response.json()
    if data and isinstance(data, list) and len(data) > 0:
        location = data[0]
        return float(location["lat"]), float(location["lon"])
    return None, None

def _mock_geocode(address: str) -> tuple[float, float]:
    """Returns random coordinates near New Delhi, India for demo purposes."""
    # Base coordinates roughly around central Delhi
    base_lat = 28.6139
    base_lng = 77.2090
    
    # Add some random jitter (roughly within a 5-10km radius)
    jitter_lat = random.uniform(-0.05, 0.05)
    jitter_lng = random.uniform(-0.05, 0.05)
    
    return base_lat + jitter_lat, base_lng + jitter_lng
