from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import pandas as pd

from src.modules.damage_mapping import normalize_damage_label


def load_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)


def load_csv_bytes(raw_bytes: bytes) -> pd.DataFrame:
    return pd.read_csv(BytesIO(raw_bytes))


def list_xbd_records(
    dataset_root: str | Path,
    split: str = "tier3",
    stage: str = "post_disaster",
    limit: int | None = None,
) -> list[dict]:
    root = Path(dataset_root)
    image_dir = root / split / "images"
    label_dir = root / split / "labels"

    if not image_dir.exists() or not label_dir.exists():
        return []

    records: list[dict] = []
    for image_path in sorted(image_dir.glob(f"*_{stage}.png")):
        label_path = label_dir / f"{image_path.stem}.json"
        if not label_path.exists():
            continue

        records.append(
            {
                "id": image_path.stem,
                "image_path": str(image_path),
                "label_path": str(label_path),
            }
        )
        if limit is not None and len(records) >= limit:
            break

    return records


def load_xbd_record(image_path: str | Path, label_path: str | Path) -> dict:
    image_path = Path(image_path)
    label_path = Path(label_path)
    annotation = load_xbd_annotation(label_path)
    return {
        "record_id": image_path.stem,
        "image_path": str(image_path),
        "label_path": str(label_path),
        "metadata": annotation["metadata"],
        "detections": annotation["detections"],
    }


def load_xbd_annotation(label_path: str | Path) -> dict:
    payload = json.loads(Path(label_path).read_text(encoding="utf-8"))
    features = payload.get("features", {})

    xy_by_uid = _index_features_by_uid(features.get("xy", []))
    geo_by_uid = _index_features_by_uid(features.get("lng_lat", []))

    detections: list[dict] = []
    for uid in sorted(set(xy_by_uid) | set(geo_by_uid)):
        xy_feature = xy_by_uid.get(uid, {})
        geo_feature = geo_by_uid.get(uid, {})
        source_feature = xy_feature or geo_feature
        properties = source_feature.get("properties", {})
        raw_label = properties.get("subtype", "un-classified")
        xy_polygon = _parse_wkt_polygon(xy_feature.get("wkt", ""))
        geo_polygon = _parse_wkt_polygon(geo_feature.get("wkt", ""))
        geo_center = _centroid(geo_polygon)

        detections.append(
            {
                "id": uid,
                "feature_type": properties.get("feature_type", "building"),
                "raw_label": raw_label,
                "label": normalize_damage_label(raw_label),
                "bbox": _bounds(xy_polygon),
                "polygon_px": xy_polygon,
                "polygon_geo": geo_polygon,
                "longitude": geo_center[0] if geo_center else None,
                "latitude": geo_center[1] if geo_center else None,
            }
        )

    return {
        "metadata": payload.get("metadata", {}),
        "detections": detections,
    }


def _index_features_by_uid(features: list[dict]) -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for index, feature in enumerate(features):
        properties = feature.get("properties", {})
        uid = properties.get("uid", f"feature-{index}")
        indexed[uid] = feature
    return indexed


def _parse_wkt_polygon(wkt: str) -> list[tuple[float, float]]:
    if "((" not in wkt or "))" not in wkt:
        return []

    raw_points = wkt.split("((", maxsplit=1)[1].rsplit("))", maxsplit=1)[0]
    first_ring = raw_points.split("),(", maxsplit=1)[0]
    points: list[tuple[float, float]] = []

    for pair in first_ring.split(","):
        values = pair.strip().split()
        if len(values) < 2:
            continue
        points.append((float(values[0]), float(values[1])))

    return points


def _bounds(points: list[tuple[float, float]]) -> list[float] | None:
    if not points:
        return None

    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return [min(xs), min(ys), max(xs), max(ys)]


def _centroid(points: list[tuple[float, float]]) -> tuple[float, float] | None:
    if not points:
        return None

    x_total = sum(point[0] for point in points)
    y_total = sum(point[1] for point in points)
    return (x_total / len(points), y_total / len(points))
