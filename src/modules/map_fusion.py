from __future__ import annotations

import math

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two lat/lng coordinates using Haversine formula."""
    R = 6371000 # Radius of earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def compute_hotspots(
    damage_detections: list[dict],
    sos_events: list[dict],
    radius_meters: float = 1000.0,
) -> list[dict]:
    """
    Fuses damage detections with SOS events.
    For each SOS event, counts the number of severe damage detections (destroyed/damaged)
    within the given radius to compute a hotspot priority score.
    """
    hotspots = []
    
    # Filter for severe damage only
    severe_damage = [d for d in damage_detections if d.get("label") in ["destroyed", "damaged"] and "latitude" in d and "longitude" in d]

    for event in sos_events:
        event_lat = event.get("latitude")
        event_lng = event.get("longitude")
        
        if event_lat is None or event_lng is None:
            continue

        overlap_count = 0
        destroyed_count = 0

        for damage in severe_damage:
            dist = calculate_distance(event_lat, event_lng, damage["latitude"], damage["longitude"])
            if dist <= radius_meters:
                overlap_count += 1
                if damage.get("label") == "destroyed":
                    destroyed_count += 1
        
        # Base score on urgency + overlapping damage
        urgency_multiplier = {"high": 3, "medium": 2, "low": 1}.get(event.get("urgency", "low").lower(), 1)
        priority_score = (urgency_multiplier * 10) + (destroyed_count * 5) + (overlap_count * 2)

        hotspots.append({
            "sos_id": event.get("id"),
            "location_text": event.get("extracted_location", "Unknown Location"),
            "latitude": event_lat,
            "longitude": event_lng,
            "urgency": event.get("urgency"),
            "overlap_damage_count": overlap_count,
            "destroyed_structures_nearby": destroyed_count,
            "priority_score": priority_score,
            "needs_dispatch": priority_score >= 30, # Arbitrary threshold for flagging critical cases
        })

    # Sort by priority descending
    hotspots.sort(key=lambda x: x["priority_score"], reverse=True)
    return hotspots
