def build_dispatch_message(hotspot_name: str, coordinates: str, logistics_summary: dict) -> str:
    return (
        f"ALERT: Prioritize {hotspot_name} at {coordinates}. "
        f"Estimated trapped civilians: {logistics_summary['estimated_people_trapped']}. "
        f"Carry water: {logistics_summary['water_liters']}L, cots: "
        f"{logistics_summary['emergency_cots']}, medical kits: "
        f"{logistics_summary['medical_kits']}."
    )
