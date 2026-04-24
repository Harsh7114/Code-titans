def build_sitrep_payload(
    damage_summary: dict,
    sos_summary: dict,
    logistics_summary: dict,
) -> dict:
    return {
        "damage_summary": damage_summary,
        "sos_summary": sos_summary,
        "logistics_summary": logistics_summary,
    }


def generate_sitrep_preview(payload: dict) -> str:
    damage = payload["damage_summary"]
    sos = payload["sos_summary"]
    logistics = payload["logistics_summary"]
    return (
        "Initial assessment indicates "
        f"{damage['destroyed']} destroyed structures and {damage['damaged']} damaged structures. "
        f"A total of {sos['total']} SOS reports have been identified, including "
        f"{sos['high_priority']} high-priority alerts. "
        f"Current logistics estimate indicates support for "
        f"{logistics['estimated_people_trapped']} potentially trapped civilians, requiring "
        f"{logistics['water_liters']} liters of water, {logistics['emergency_cots']} emergency cots, "
        f"and {logistics['medical_kits']} medical kits."
    )
