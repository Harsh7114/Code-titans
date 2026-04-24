from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import pandas as pd

from src.modules.damage_mapping import normalize_damage_label

# Default xView2-xBD class names in YOLO class-index order.
# Roboflow writes the mapping into data.yaml; we fall back to this list when
# the file is absent so the loader works even with a partial download.
_XBD_DEFAULT_CLASSES = ["no-damage", "minor-damage", "major-damage", "destroyed"]


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


# ---------------------------------------------------------------------------
# YOLOv8 / Roboflow dataset loader
# ---------------------------------------------------------------------------

def list_roboflow_yolo_records(
    dataset_root: str | Path,
    split: str = "train",
    limit: int | None = None,
) -> list[dict]:
    """Return paired image / label records from a Roboflow YOLOv8-format download.

    Expected layout (produced by the Roboflow "Download Dataset → YOLOv8" button)::

        <dataset_root>/
            data.yaml
            train/
                images/  *.jpg  (or .png)
                labels/  *.txt
            valid/
                images/
                labels/
            test/
                images/
                labels/
    """
    root = Path(dataset_root)
    image_dir = root / split / "images"
    label_dir = root / split / "labels"

    if not image_dir.exists() or not label_dir.exists():
        return []

    records: list[dict] = []
    for image_path in sorted(image_dir.glob("*")):
        if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        label_path = label_dir / f"{image_path.stem}.txt"
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


def load_roboflow_yolo_record(image_path: str | Path, label_path: str | Path) -> dict:
    """Parse one YOLOv8 image + label pair into the common detection dict format."""
    from PIL import Image as _PILImage  # local import to avoid top-level dep in tests

    image_path = Path(image_path)
    label_path = Path(label_path)

    # Read class names from data.yaml two levels up (dataset root).
    data_yaml_path = image_path.parent.parent.parent / "data.yaml"
    class_names = _load_yolo_class_names(data_yaml_path)

    with _PILImage.open(image_path) as img:
        image_width, image_height = img.size

    detections = _parse_yolo_label(
        label_path=label_path,
        class_names=class_names,
        image_width=image_width,
        image_height=image_height,
    )

    return {
        "record_id": image_path.stem,
        "image_path": str(image_path),
        "label_path": str(label_path),
        "metadata": {
            "width": image_width,
            "height": image_height,
            "img_name": image_path.name,
            "source": "roboflow-yolov8",
        },
        "detections": detections,
    }


def _load_yolo_class_names(data_yaml_path: Path) -> list[str]:
    """Read the 'names' list from a Roboflow data.yaml; fall back to xBD defaults."""
    if not data_yaml_path.exists():
        return _XBD_DEFAULT_CLASSES

    try:
        # Use PyYAML if available, otherwise do a simple line-based parse.
        try:
            import yaml  # type: ignore[import-untyped]
            payload = yaml.safe_load(data_yaml_path.read_text(encoding="utf-8"))
            names = payload.get("names", [])
        except ImportError:
            names = _parse_yaml_names_simple(data_yaml_path)

        if isinstance(names, list) and names:
            return [str(n) for n in names]
        if isinstance(names, dict):
            # Some Roboflow exports use {0: "no-damage", 1: "minor-damage", ...}
            return [names[k] for k in sorted(names)]
    except Exception:
        pass

    return _XBD_DEFAULT_CLASSES


def _parse_yaml_names_simple(yaml_path: Path) -> list[str]:
    """Minimal YAML names-list parser that avoids a PyYAML dependency."""
    names: list[str] = []
    in_names = False
    for line in yaml_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("names:"):
            after_colon = stripped[len("names:"):].strip()
            if after_colon.startswith("["):
                # Inline list: names: [no-damage, minor-damage, ...]
                items = after_colon.strip("[]").split(",")
                return [i.strip().strip("'\"") for i in items if i.strip()]
            in_names = True
            continue
        if in_names:
            if stripped.startswith("-"):
                names.append(stripped.lstrip("- ").strip().strip("'\""))
            elif stripped and not stripped.startswith("#"):
                break
    return names


def _parse_yolo_label(
    label_path: Path,
    class_names: list[str],
    image_width: int,
    image_height: int,
) -> list[dict]:
    """Convert a YOLO .txt annotation file to the common detections format.

    Each line: ``class_id  cx  cy  w  h``  (all values normalised 0–1).
    """
    detections: list[dict] = []
    raw_lines = label_path.read_text(encoding="utf-8").splitlines()

    for index, line in enumerate(raw_lines):
        parts = line.strip().split()
        if len(parts) < 5:
            continue

        class_id = int(parts[0])
        cx_norm = float(parts[1])
        cy_norm = float(parts[2])
        w_norm = float(parts[3])
        h_norm = float(parts[4])

        # De-normalise to pixel coordinates.
        cx_px = cx_norm * image_width
        cy_px = cy_norm * image_height
        w_px = w_norm * image_width
        h_px = h_norm * image_height
        x0, y0 = cx_px - w_px / 2, cy_px - h_px / 2
        x1, y1 = cx_px + w_px / 2, cy_px + h_px / 2
        bbox = [x0, y0, x1, y1]
        polygon = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]

        raw_label = class_names[class_id] if class_id < len(class_names) else "unknown"

        detections.append(
            {
                "id": f"yolo-{index}",
                "feature_type": "building",
                "raw_label": raw_label,
                "label": normalize_damage_label(raw_label),
                "confidence": None,
                "bbox": bbox,
                "polygon_px": polygon,
                "polygon_geo": [],
                "longitude": None,
                "latitude": None,
            }
        )

    return detections
