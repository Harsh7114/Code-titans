import json
import requests

class SITREPExtractionError(RuntimeError):
    pass

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

def generate_sitrep_with_gemini(payload: dict, api_key: str, model: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    
    prompt = (
        "You are an emergency command official generating a formal Situation Report (SITREP) "
        "based on real-time disaster metrics. Please draft a concise, professional, action-oriented "
        "report suitable for government and relief organizations.\n\n"
        f"Here are the current metrics:\n{json.dumps(payload, indent=2)}\n\n"
        "Ensure the output includes sections for Structural Damage, Incident Urgency, "
        "and Logistics Requirements. Do not invent any new statistics outside of the payload."
    )

    request_payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
        },
    }
    
    response = requests.post(
        url,
        params={"key": api_key},
        json=request_payload,
        timeout=60,
    )
    if not response.ok:
        raise SITREPExtractionError(
            f"Gemini SITREP generation failed with status {response.status_code}: {response.text[:200]}"
        )

    response_json = response.json()
    text = (
        response_json.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text")
    )
    if not text:
        raise SITREPExtractionError("Gemini returned no text output.")

    return text
