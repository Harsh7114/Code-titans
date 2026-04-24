def estimate_logistics(
    destroyed_structures: int,
    avg_household_size: int,
    water_per_person_liters: int,
    medical_kits_per_10_people: int,
) -> dict:
    estimated_people_trapped = destroyed_structures * avg_household_size
    medical_kits = max(
        1,
        (estimated_people_trapped * medical_kits_per_10_people + 9) // 10,
    )
    return {
        "destroyed_structures": destroyed_structures,
        "estimated_people_trapped": estimated_people_trapped,
        "water_liters": estimated_people_trapped * water_per_person_liters,
        "emergency_cots": estimated_people_trapped,
        "medical_kits": medical_kits,
    }
