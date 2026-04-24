from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class AppConfig:
    avg_household_size: int
    water_per_person_liters: int
    medical_kits_per_10_people: int
    gemini_api_key: str | None
    gemini_model: str
    roboflow_api_key: str | None
    roboflow_model_id: str | None
    roboflow_model_version: str | None
    roboflow_confidence: int
    roboflow_overlap: int
    geocoding_provider: str
    geocoding_api_key: str | None
    xbd_dataset_root: str | None
    xbd_working_split: str
    xbd_image_stage: str
    xbd_max_records: int
    twilio_account_sid: str | None
    twilio_auth_token: str | None
    twilio_from_number: str | None
    twilio_to_number: str | None
    mock_damage_detections: list[dict]
    mock_sos_events: list[dict]

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            avg_household_size=int(os.getenv("AVG_HOUSEHOLD_SIZE", "4")),
            water_per_person_liters=int(os.getenv("WATER_PER_PERSON_LITERS", "5")),
            medical_kits_per_10_people=int(os.getenv("MEDICAL_KITS_PER_10_PEOPLE", "3")),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            roboflow_api_key=os.getenv("ROBOFLOW_API_KEY"),
            roboflow_model_id=os.getenv("ROBOFLOW_MODEL_ID"),
            roboflow_model_version=os.getenv("ROBOFLOW_MODEL_VERSION"),
            roboflow_confidence=int(os.getenv("ROBOFLOW_CONFIDENCE", "40")),
            roboflow_overlap=int(os.getenv("ROBOFLOW_OVERLAP", "30")),
            geocoding_provider=os.getenv("GEOCODING_PROVIDER", "mock"),
            geocoding_api_key=os.getenv("GEOCODING_API_KEY"),
            xbd_dataset_root=os.getenv("XBD_DATASET_ROOT"),
            xbd_working_split=os.getenv("XBD_WORKING_SPLIT", "tier3"),
            xbd_image_stage=os.getenv("XBD_IMAGE_STAGE", "post_disaster"),
            xbd_max_records=int(os.getenv("XBD_MAX_RECORDS", "100")),
            twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
            twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
            twilio_from_number=os.getenv("TWILIO_FROM_NUMBER"),
            twilio_to_number=os.getenv("TWILIO_TO_NUMBER"),
            mock_damage_detections=_default_damage_detections(),
            mock_sos_events=_default_sos_events(),
        )

    @property
    def roboflow_configured(self) -> bool:
        return bool(
            self.roboflow_api_key and self.roboflow_model_id and self.roboflow_model_version
        )

    @property
    def gemini_configured(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def twilio_configured(self) -> bool:
        return bool(self.twilio_account_sid and self.twilio_auth_token and self.twilio_from_number and self.twilio_to_number)


def _default_damage_detections() -> list[dict]:
    return [
        {"id": "det-001", "label": "destroyed", "confidence": 0.94, "latitude": 28.6139, "longitude": 77.2090},
        {"id": "det-002", "label": "damaged", "confidence": 0.83, "latitude": 28.6123, "longitude": 77.2211},
        {"id": "det-003", "label": "destroyed", "confidence": 0.91, "latitude": 28.6151, "longitude": 77.2154},
        {"id": "det-004", "label": "intact", "confidence": 0.88, "latitude": 28.6178, "longitude": 77.2180},
    ]


def _default_sos_events() -> list[dict]:
    return [
        {
            "id": "sos-001",
            "raw_text": "Help needed near MG Road, building collapsed",
            "extracted_location": "MG Road",
            "latitude": 28.6137,
            "longitude": 77.2092,
            "priority": "high",
        },
        {
            "id": "sos-002",
            "raw_text": "Family trapped near central block",
            "extracted_location": "Central Block",
            "latitude": 28.6150,
            "longitude": 77.2156,
            "priority": "high",
        },
    ]
