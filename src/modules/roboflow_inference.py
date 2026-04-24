from __future__ import annotations

import base64

import requests


class RoboflowInferenceError(RuntimeError):
    pass


def run_roboflow_inference(
    image_bytes: bytes,
    api_key: str,
    model_id: str,
    model_version: str,
    confidence: int = 40,
    overlap: int = 30,
) -> dict:
    url = f"https://detect.roboflow.com/{model_id}/{model_version}"
    params = {
        "api_key": api_key,
        "confidence": confidence,
        "overlap": overlap,
        "format": "json",
    }
    payload = base64.b64encode(image_bytes)
    response = requests.post(url, params=params, data=payload, timeout=60)

    if not response.ok:
        raise RoboflowInferenceError(
            f"Roboflow inference failed with status {response.status_code}: {response.text[:200]}"
        )

    return response.json()
