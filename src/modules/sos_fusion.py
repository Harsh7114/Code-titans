from __future__ import annotations

import re

import pandas as pd


def normalize_sos_records(dataframe: pd.DataFrame) -> list[dict]:
    records: list[dict] = []
    for index, row in dataframe.fillna("").iterrows():
        raw_text = _pick_first_value(
            row,
            ["message_text", "raw_text", "message", "text", "sos_message"],
        )
        if not raw_text:
            continue

        location_text = _pick_first_value(
            row,
            ["location_text", "location", "area", "place"],
        )
        priority = _pick_first_value(row, ["priority", "urgency", "severity"]).lower()
        if priority not in {"high", "medium", "low"}:
            priority = infer_priority(raw_text)

        records.append(
            {
                "id": _pick_first_value(row, ["id", "message_id"]) or f"sos-{index + 1:03d}",
                "raw_text": raw_text.strip(),
                "source": _pick_first_value(row, ["source", "channel"]) or "uploaded-csv",
                "timestamp": _pick_first_value(row, ["timestamp", "created_at"]),
                "priority": priority,
                "location_text": location_text.strip() if location_text else None,
                "latitude": _parse_float(_pick_first_value(row, ["latitude", "lat"])),
                "longitude": _parse_float(_pick_first_value(row, ["longitude", "lon", "lng"])),
            }
        )

    return records


def extract_sos_events_with_fallback(
    records: list[dict],
    extracted_rows: list[dict] | None = None,
) -> list[dict]:
    extracted_by_id = {
        item["id"]: item
        for item in extracted_rows or []
        if item.get("id")
    }

    normalized_events: list[dict] = []
    for record in records:
        extraction = extracted_by_id.get(record["id"]) or heuristic_extract_sos(record)
        normalized_events.append(
            {
                **record,
                "extracted_location": extraction.get("extracted_location") or record.get("location_text"),
                "incident_type": extraction.get("incident_type", "unknown"),
                "severity": extraction.get("severity", record["priority"]),
                "people_count": extraction.get("people_count"),
                "urgency": extraction.get("urgency", record["priority"]),
                "summary": extraction.get("summary", record["raw_text"]),
                "confidence": extraction.get("confidence", 0.35),
                "extraction_method": extraction.get("extraction_method", "heuristic"),
            }
        )

    return normalized_events


def heuristic_extract_sos(record: dict) -> dict:
    raw_text = record["raw_text"]
    base_location = record.get("location_text")
    extracted_location = base_location or infer_location(raw_text)
    people_count = infer_people_count(raw_text)
    severity = infer_priority(raw_text)
    incident_type = infer_incident_type(raw_text)

    return {
        "id": record["id"],
        "extracted_location": extracted_location,
        "severity": severity,
        "people_count": people_count,
        "urgency": severity,
        "incident_type": incident_type,
        "summary": raw_text,
        "confidence": 0.35,
        "extraction_method": "heuristic",
    }


def summarize_sos(events: list[dict]) -> dict:
    high_priority = [event for event in events if event.get("urgency") == "high"]
    extracted_locations = [event.get("extracted_location") for event in events if event.get("extracted_location")]
    geocoded = [event for event in events if event.get("latitude") is not None and event.get("longitude") is not None]

    return {
        "total": len(events),
        "high_priority": len(high_priority),
        "extracted_locations": len(extracted_locations),
        "pending_geocoding": len(events) - len(geocoded),
        "locations": extracted_locations[:10],
    }


def build_sample_sos_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": "sos-001",
                "message_text": "Help, building collapsed near MG Road Bengaluru. 4 people trapped.",
                "source": "sms",
                "timestamp": "2026-04-24T12:15:00+05:30",
                "priority": "high",
                "location_text": "MG Road, Bengaluru",
            },
            {
                "id": "sos-002",
                "message_text": "Need medical help near Connaught Place New Delhi, elderly injured.",
                "source": "sms",
                "timestamp": "2026-04-24T12:21:00+05:30",
                "priority": "high",
                "location_text": "Connaught Place, New Delhi",
            },
            {
                "id": "sos-003",
                "message_text": "Road blocked and house damaged in BTM Layout 2nd Stage, family safe but needs water.",
                "source": "app",
                "timestamp": "2026-04-24T12:32:00+05:30",
                "priority": "medium",
                "location_text": "BTM Layout 2nd Stage, Bengaluru",
            },
        ]
    )


def infer_priority(text: str) -> str:
    lower = text.lower()
    if any(token in lower for token in ["trapped", "collapsed", "critical", "injured", "bleeding", "urgent"]):
        return "high"
    if any(token in lower for token in ["damaged", "blocked", "need water", "need help"]):
        return "medium"
    return "low"


def infer_location(text: str) -> str | None:
    pattern = re.compile(
        r"(?:near|at|in|around|beside|opposite)\s+([A-Z0-9][A-Za-z0-9,\- ]{3,60})",
        flags=re.IGNORECASE,
    )
    match = pattern.search(text)
    if not match:
        return None
    return match.group(1).strip(" .,!?:;")


def infer_people_count(text: str) -> int | None:
    match = re.search(r"(\d+)\s+(?:people|person|persons|family members|adults|children)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def infer_incident_type(text: str) -> str:
    lower = text.lower()
    if "collapsed" in lower or "rubble" in lower:
        return "building-collapse"
    if "medical" in lower or "injured" in lower:
        return "medical"
    if "water" in lower or "food" in lower:
        return "supply-shortage"
    if "road blocked" in lower or "blocked" in lower:
        return "access-blocked"
    return "general-distress"


def _pick_first_value(row: pd.Series, columns: list[str]) -> str:
    for column in columns:
        if column in row and str(row[column]).strip():
            return str(row[column]).strip()
    return ""


def _parse_float(value: str) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None
