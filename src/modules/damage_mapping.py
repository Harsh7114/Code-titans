from collections import Counter


def normalize_damage_label(raw_label: str) -> str:
    # Keys cover the xView2-xBD Roboflow model class names as well as the
    # original xBD polygon annotation subtypes and common colour-code aliases.
    normalized_map = {
        # xView2-xBD Roboflow model classes (hyphen-separated)
        "no-damage": "intact",
        "minor-damage": "damaged",
        "major-damage": "damaged",
        "destroyed": "destroyed",
        # underscore variants (YOLO label files)
        "no_damage": "intact",
        "minor_damage": "damaged",
        "major_damage": "damaged",
        # space-separated variants (some export pipelines)
        "no damage": "intact",
        "minor damage": "damaged",
        "major damage": "damaged",
        # original xBD annotation subtypes
        "damaged": "damaged",
        "severe-damage": "damaged",
        "severe_damage": "damaged",
        "intact": "intact",
        # colour-code shorthands
        "green": "intact",
        "yellow": "damaged",
        "red": "destroyed",
        # unclassified / fallback
        "un-classified": "unknown",
        "unclassified": "unknown",
    }
    return normalized_map.get(raw_label.strip().lower(), "unknown")


def damage_label_color(label: str) -> str:
    colors = {
        "destroyed": "#d62828",
        "damaged": "#f4a261",
        "intact": "#2a9d8f",
        "unknown": "#6c757d",
    }
    return colors.get(label, "#6c757d")


def bbox_to_polygon(bbox: list[float] | None) -> list[tuple[float, float]]:
    if not bbox:
        return []

    x0, y0, x1, y1 = bbox
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]


def build_bbox_from_center(
    center_x: float,
    center_y: float,
    width: float,
    height: float,
) -> list[float]:
    half_width = width / 2
    half_height = height / 2
    return [
        center_x - half_width,
        center_y - half_height,
        center_x + half_width,
        center_y + half_height,
    ]


def normalize_roboflow_predictions(payload: dict) -> list[dict]:
    detections: list[dict] = []
    for index, prediction in enumerate(payload.get("predictions", [])):
        raw_label = prediction.get("class", "unknown")
        bbox = build_bbox_from_center(
            center_x=float(prediction.get("x", 0)),
            center_y=float(prediction.get("y", 0)),
            width=float(prediction.get("width", 0)),
            height=float(prediction.get("height", 0)),
        )
        detections.append(
            {
                "id": f"rf-{index}",
                "feature_type": "building",
                "raw_label": raw_label,
                "label": normalize_damage_label(raw_label),
                "confidence": float(prediction.get("confidence", 0)),
                "bbox": bbox,
                "polygon_px": bbox_to_polygon(bbox),
                "polygon_geo": [],
                "longitude": None,
                "latitude": None,
            }
        )
    return detections


def build_demo_uploaded_detections(image_width: int, image_height: int) -> list[dict]:
    templates = [
        ("destroyed", 0.18, 0.16, 0.27, 0.28, 0.89),
        ("damaged", 0.55, 0.22, 0.74, 0.40, 0.81),
        ("intact", 0.36, 0.58, 0.60, 0.79, 0.76),
    ]
    detections: list[dict] = []
    for index, (raw_label, x0_ratio, y0_ratio, x1_ratio, y1_ratio, confidence) in enumerate(
        templates
    ):
        bbox = [
            image_width * x0_ratio,
            image_height * y0_ratio,
            image_width * x1_ratio,
            image_height * y1_ratio,
        ]
        detections.append(
            {
                "id": f"demo-{index}",
                "feature_type": "building",
                "raw_label": raw_label,
                "label": normalize_damage_label(raw_label),
                "confidence": confidence,
                "bbox": bbox,
                "polygon_px": bbox_to_polygon(bbox),
                "polygon_geo": [],
                "longitude": None,
                "latitude": None,
            }
        )
    return detections


def summarize_damage(detections: list[dict]) -> dict:
    counts = Counter(item["label"] for item in detections)
    raw_counts = Counter(item.get("raw_label", item["label"]) for item in detections)
    return {
        "total": len(detections),
        "destroyed": counts.get("destroyed", 0),
        "damaged": counts.get("damaged", 0),
        "intact": counts.get("intact", 0),
        "unknown": counts.get("unknown", 0),
        "class_breakdown": dict(sorted(raw_counts.items())),
    }
