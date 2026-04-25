def estimate_logistics(
    damage_detections: list[dict],
    avg_household_size: int,
    water_per_person_liters: int,
    medical_kits_per_10_people: int,
) -> dict:
    
    destroyed_count = 0
    estimated_people_trapped = 0
    
    # Base heuristic: Let's assume a standard 50x50 pixel building holds the 'avg_household_size' (e.g., 4 people).
    # That is an area of 2500 pixels.
    # Therefore, Density Factor = avg_household_size / 2500
    density_factor = avg_household_size / 2500.0

    for detection in damage_detections:
        # We only calculate trapped civilians for fully 'destroyed' structures
        if detection.get("label") == "destroyed":
            destroyed_count += 1
            bbox = detection.get("bbox")
            if bbox and len(bbox) == 4:
                x0, y0, x1, y1 = bbox
                width = abs(x1 - x0)
                height = abs(y1 - y0)
                area = width * height
                
                # Minimum of 1 person for any destroyed structure to be safe, scaled by area
                building_occupancy = max(1, int(area * density_factor))
                estimated_people_trapped += building_occupancy
            else:
                # Fallback if no bbox is provided
                estimated_people_trapped += avg_household_size

    medical_kits = max(
        1,
        (estimated_people_trapped * medical_kits_per_10_people + 9) // 10,
    )
    return {
        "destroyed_structures": destroyed_count,
        "estimated_people_trapped": estimated_people_trapped,
        "water_liters": estimated_people_trapped * water_per_person_liters,
        "emergency_cots": estimated_people_trapped,
        "medical_kits": medical_kits,
    }
