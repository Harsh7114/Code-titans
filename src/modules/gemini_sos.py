from __future__ import annotations

import json

import requests


class GeminiExtractionError(RuntimeError):
    pass


def extract_sos_with_gemini(
    records: list[dict],
    api_key: str,
    model: str,
) -> list[dict]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    prompt = build_sos_prompt(records)
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt,
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": build_sos_response_schema(),
        },
    }
    response = requests.post(
        url,
        params={"key": api_key},
        json=payload,
        timeout=60,
    )
    if not response.ok:
        raise GeminiExtractionError(
            f"Gemini extraction failed with status {response.status_code}: {response.text[:200]}"
        )

    response_json = response.json()
    text = (
        response_json.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text")
    )
    if not text:
        raise GeminiExtractionError("Gemini returned no structured text output.")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise GeminiExtractionError("Gemini returned invalid JSON for SOS extraction.") from error

    if not isinstance(data, list):
        raise GeminiExtractionError("Gemini structured output did not return a list.")

    normalized_rows = []
    for item in data:
        normalized_rows.append(
            {
                "id": item.get("id"),
                "extracted_location": item.get("extracted_location"),
                "severity": item.get("severity", "medium"),
                "people_count": item.get("people_count"),
                "urgency": item.get("urgency", "medium"),
                "incident_type": item.get("incident_type", "general-distress"),
                "summary": item.get("summary", ""),
                "confidence": item.get("confidence", 0.75),
                "extraction_method": "gemini",
            }
        )
    return normalized_rows


def build_sos_prompt(records: list[dict]) -> str:
    lines = [
        "Extract structured disaster-response information from each SOS message.",
        "Return one JSON object per input record.",
        "Preserve the input id exactly.",
        "If location is unclear, set extracted_location to null.",
        "Severity and urgency must be one of: high, medium, low.",
        "Incident type should be a short operational label like building-collapse, medical, flood, fire, access-blocked, supply-shortage, or general-distress.",
        "People count should be an integer or null.",
        "",
        "Input records:",
    ]
    for record in records:
        lines.append(
            json.dumps(
                {
                    "id": record["id"],
                    "raw_text": record["raw_text"],
                    "location_text": record.get("location_text"),
                    "priority": record.get("priority"),
                },
                ensure_ascii=True,
            )
        )
    return "\n".join(lines)


def build_sos_response_schema() -> dict:
    return {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "extracted_location": {"type": ["string", "null"]},
                "severity": {"type": "string"},
                "people_count": {"type": ["integer", "null"]},
                "urgency": {"type": "string"},
                "incident_type": {"type": "string"},
                "summary": {"type": "string"},
                "confidence": {"type": "number"},
            },
            "required": [
                "id",
                "extracted_location",
                "severity",
                "people_count",
                "urgency",
                "incident_type",
                "summary",
                "confidence",
            ],
            "additionalProperties": False,
        },
    }
