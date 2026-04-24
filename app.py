from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import Image

from src.config import AppConfig
from src.data.loaders import list_xbd_records, load_csv_bytes, load_xbd_record
from src.modules.damage_mapping import (
    build_demo_uploaded_detections,
    normalize_roboflow_predictions,
    summarize_damage,
)
from src.modules.dispatch import build_dispatch_message
from src.modules.gemini_sos import GeminiExtractionError, extract_sos_with_gemini
from src.modules.geocoding import geocode_locations
from src.modules.logistics import estimate_logistics
from src.modules.map_fusion import compute_hotspots
from src.modules.roboflow_inference import RoboflowInferenceError, run_roboflow_inference
from src.modules.sitrep import build_sitrep_payload, generate_sitrep_preview
from src.modules.sos_fusion import (
    build_sample_sos_dataframe,
    extract_sos_events_with_fallback,
    normalize_sos_records,
    summarize_sos,
)
from src.ui.sections import (
    render_architecture_note,
    render_damage_breakdown_chart,
    render_damage_figure,
    render_detection_table,
    render_fused_map,
    render_global_styles,
    render_hero,
    render_hotspot_table,
    render_metric_card,
    render_panel_header,
    render_side_note,
    render_sos_priority_chart,
    render_status_chips,
)


st.set_page_config(
    page_title="ResQMap AI",
    page_icon="🚨",
    layout="wide",
)


def resolve_damage_context(config: AppConfig) -> tuple[list[dict], dict]:
    st.sidebar.markdown("### Damage Feed")
    selected_source = st.sidebar.radio(
        "Damage Data Source",
        options=["Mock", "Local xBD tier3", "Upload Image"],
        index=1 if config.xbd_dataset_root else 0,
    )

    if selected_source == "Local xBD tier3":
        return _resolve_xbd_context(config)

    if selected_source == "Upload Image":
        return _resolve_uploaded_context(config)

    return config.mock_damage_detections, {
        "source": "Mock",
        "record_id": "mock-detections",
        "status": "Using built-in mock detections.",
        "metadata": {},
        "image_bytes": None,
        "image_name": None,
        "detections": config.mock_damage_detections,
    }


def _resolve_xbd_context(config: AppConfig) -> tuple[list[dict], dict]:
    if not config.xbd_dataset_root:
        st.sidebar.warning("Set XBD_DATASET_ROOT in your local .env to use real tier3 records.")
        return [], _empty_damage_context("Local xBD tier3", "No dataset root configured.")

    records = list_xbd_records(
        dataset_root=config.xbd_dataset_root,
        split=config.xbd_working_split,
        stage=config.xbd_image_stage,
        limit=config.xbd_max_records,
    )
    if not records:
        st.sidebar.warning("No matching tier3 image-label pairs were found under XBD_DATASET_ROOT.")
        return [], _empty_damage_context("Local xBD tier3", "No usable image-label pairs found.")

    selected_record_id = st.sidebar.selectbox(
        "Local xBD Record",
        options=[record["id"] for record in records],
    )
    selected_record = next(record for record in records if record["id"] == selected_record_id)
    context = load_xbd_record(
        image_path=selected_record["image_path"],
        label_path=selected_record["label_path"],
    )
    context["source"] = "Local xBD tier3"
    context["status"] = "Loaded polygon annotations from xBD tier3."
    context["image_bytes"] = Path(selected_record["image_path"]).read_bytes()
    context["image_name"] = Path(selected_record["image_path"]).name
    return context["detections"], context


def _resolve_uploaded_context(config: AppConfig) -> tuple[list[dict], dict]:
    uploaded_file = st.sidebar.file_uploader(
        "Upload Satellite or Aerial Image",
        type=["png", "jpg", "jpeg"],
    )
    if uploaded_file is None:
        return [], _empty_damage_context("Upload Image", "Upload an image to run the damage pipeline.")

    image_bytes = uploaded_file.getvalue()
    cache_key = hashlib.sha256(image_bytes).hexdigest()
    cached_context = st.session_state.get("uploaded_damage_cache", {}).get(cache_key)
    if cached_context:
        return cached_context["detections"], cached_context

    image = Image.open(BytesIO(image_bytes))
    image_width, image_height = image.size
    metadata = {
        "width": image_width,
        "height": image_height,
        "img_name": uploaded_file.name,
        "source": "uploaded-image",
    }

    if config.roboflow_configured:
        try:
            payload = run_roboflow_inference(
                image_bytes=image_bytes,
                api_key=config.roboflow_api_key or "",
                model_id=config.roboflow_model_id or "",
                model_version=config.roboflow_model_version or "",
                confidence=config.roboflow_confidence,
                overlap=config.roboflow_overlap,
            )
            detections = normalize_roboflow_predictions(payload)
            metadata.update(payload.get("image", {}))
            status = "Roboflow inference completed successfully."
            source = "Upload Image -> Roboflow"
        except RoboflowInferenceError as error:
            detections = build_demo_uploaded_detections(image_width, image_height)
            status = f"Roboflow inference failed. Demo fallback used. {error}"
            source = "Upload Image -> Demo Fallback"
    else:
        detections = build_demo_uploaded_detections(image_width, image_height)
        status = "Roboflow credentials are missing. Demo fallback detections were generated."
        source = "Upload Image -> Demo Fallback"

    context = {
        "source": source,
        "record_id": Path(uploaded_file.name).stem,
        "status": status,
        "metadata": metadata,
        "image_bytes": image_bytes,
        "image_name": uploaded_file.name,
        "image_path": None,
        "detections": detections,
    }
    cache = st.session_state.setdefault("uploaded_damage_cache", {})
    cache[cache_key] = context
    return detections, context


def _empty_damage_context(source: str, status: str) -> dict:
    return {
        "source": source,
        "record_id": "none",
        "status": status,
        "metadata": {},
        "image_bytes": None,
        "image_name": None,
        "image_path": None,
        "detections": [],
    }


def resolve_sos_context(config: AppConfig) -> tuple[list[dict], dict]:
    st.sidebar.markdown("### SOS Feed")
    selected_source = st.sidebar.radio(
        "SOS Data Source",
        options=["Mock", "Sample SOS CSV", "Upload SOS CSV"],
        index=1,
    )

    if selected_source == "Sample SOS CSV":
        dataframe = build_sample_sos_dataframe()
        return _extract_sos_context(dataframe, config, "Sample SOS CSV")

    if selected_source == "Upload SOS CSV":
        uploaded_file = st.sidebar.file_uploader("Upload SOS CSV", type=["csv"])
        if uploaded_file is None:
            return config.mock_sos_events, {
                "source": "Upload SOS CSV",
                "status": "Upload a CSV to start SOS extraction.",
                "record_count": 0,
                "extraction_mode": "none",
                "dataframe_preview": [],
            }
        dataframe = load_csv_bytes(uploaded_file.getvalue())
        return _extract_sos_context(dataframe, config, "Upload SOS CSV")

    return config.mock_sos_events, {
        "source": "Mock",
        "status": "Using built-in mock SOS events.",
        "record_count": len(config.mock_sos_events),
        "extraction_mode": "mock",
        "dataframe_preview": config.mock_sos_events[:5],
    }


def _extract_sos_context(dataframe, config: AppConfig, source_name: str) -> tuple[list[dict], dict]:
    records = normalize_sos_records(dataframe)
    if not records:
        return [], {
            "source": source_name,
            "status": "No usable SOS messages were found in the selected CSV.",
            "record_count": 0,
            "extraction_mode": "empty",
            "dataframe_preview": [],
        }

    extraction_mode = st.sidebar.selectbox(
        "SOS Extraction Mode",
        options=["Gemini", "Heuristic Fallback"],
        index=0 if config.gemini_configured else 1,
    )

    if extraction_mode == "Gemini" and config.gemini_configured:
        try:
            extracted_rows = extract_sos_with_gemini(
                records=records,
                api_key=config.gemini_api_key or "",
                model=config.gemini_model,
            )
            events = extract_sos_events_with_fallback(records, extracted_rows)
            status = "Gemini extraction completed successfully."
            mode = "gemini"
        except GeminiExtractionError as error:
            events = extract_sos_events_with_fallback(records)
            status = f"Gemini extraction failed. Heuristic fallback used. {error}"
            mode = "heuristic-fallback"
    else:
        events = extract_sos_events_with_fallback(records)
        status = (
            "Gemini API key is missing. Heuristic fallback was used."
            if extraction_mode == "Gemini"
            else "Heuristic fallback extraction was used."
        )
        mode = "heuristic-fallback"

    return events, {
        "source": source_name,
        "status": status,
        "record_count": len(events),
        "extraction_mode": mode,
        "dataframe_preview": events[:10],
    }


def main() -> None:
    config = AppConfig.from_env()
    render_global_styles()

    st.sidebar.title("ResQMap AI")
    st.sidebar.caption("Command-center workflow for post-disaster response")
    selected_mode = st.sidebar.selectbox(
        "Workspace",
        options=["Overview", "Damage Mapping", "SOS Fusion", "Logistics", "SITREP", "Dispatch"],
    )

    detections, damage_context = resolve_damage_context(config)
    sos_events, sos_context = resolve_sos_context(config)

    # Geocode SOS Events
    locations_to_geocode = [
        e.get("extracted_location") for e in sos_events 
        if e.get("extracted_location") and "latitude" not in e
    ]
    geocoded = geocode_locations(locations_to_geocode, config.geocoding_api_key, config.geocoding_provider)
    for event in sos_events:
        loc = event.get("extracted_location")
        if loc in geocoded and "latitude" not in event:
            event["latitude"], event["longitude"] = geocoded[loc]

    # Compute Hotspots
    hotspots = compute_hotspots(detections, sos_events)

    damage_summary = summarize_damage(detections)
    sos_summary = summarize_sos(sos_events)
    logistics_summary = estimate_logistics(
        destroyed_structures=damage_summary["destroyed"],
        avg_household_size=config.avg_household_size,
        water_per_person_liters=config.water_per_person_liters,
        medical_kits_per_10_people=config.medical_kits_per_10_people,
    )
    sitrep_payload = build_sitrep_payload(damage_summary, sos_summary, logistics_summary)
    dispatch_preview = build_dispatch_message(
        hotspot_name="Sector Alpha",
        coordinates="28.6139, 77.2090",
        logistics_summary=logistics_summary,
    )

    render_hero(
        "ResQMap AI",
        "A disaster-response control room that merges structural damage intelligence, SOS extraction, logistics forecasting, and field dispatch into one readable operating surface.",
        badges=[
            "🛰️ Damage Mapping Online",
            "📍 SOS Extraction Active",
            "🚑 Logistics Forecast Ready",
            "📡 Dispatch Workflow Staged",
        ],
    )

    card_columns = st.columns(4)
    with card_columns[0]:
        render_metric_card(
            "Destroyed Structures",
            str(damage_summary["destroyed"]),
            icon="🚨",
            tone="linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)",
            footnote="Highest-priority structural collapse zones",
        )
    with card_columns[1]:
        render_metric_card(
            "Damaged Structures",
            str(damage_summary["damaged"]),
            icon="🛰️",
            tone="linear-gradient(135deg, #f59e0b 0%, #b45309 100%)",
            footnote="Potentially unstable areas requiring verification",
        )
    with card_columns[2]:
        render_metric_card(
            "SOS Alerts",
            str(sos_summary["total"]),
            icon="📍",
            tone="linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)",
            footnote="Ground-up distress signals from citizens",
        )
    with card_columns[3]:
        render_metric_card(
            "Estimated Trapped",
            str(logistics_summary["estimated_people_trapped"]),
            icon="🚑",
            tone="linear-gradient(135deg, #14b8a6 0%, #0f766e 100%)",
            footnote="Heuristic forecast derived from destroyed buildings",
        )

    render_status_chips(
        [
            (f"Damage Feed: {damage_context['source']}", "rgba(239,68,68,0.15)", "#fca5a5"),
            (f"SOS Feed: {sos_context['source']}", "rgba(59,130,246,0.15)", "#93c5fd"),
            (f"SOS Mode: {sos_context['extraction_mode']}", "rgba(20,184,166,0.15)", "#5eead4"),
            (f"Geocoding: {config.geocoding_provider}", "rgba(167, 139, 250, 0.15)", "#c4b5fd"),
        ]
    )

    if selected_mode == "Overview":
        left_column, right_column = st.columns([1.35, 1])
        with left_column:
            render_panel_header(
                "Mission Snapshot",
                "🧭",
                "The platform is operational for damage analysis and SOS extraction. The next build step is geocoding and map fusion, but the command surface is already ready for demo review.",
            )
            render_architecture_note()
        with right_column:
            render_side_note(
                "Live Feed Status",
                f"Damage source: {damage_context['source']}. SOS source: {sos_context['source']}. "
                f"Current record: {damage_context['record_id']}. Extraction mode: {sos_context['extraction_mode']}.",
            )

        insight_cols = st.columns(2)
        with insight_cols[0]:
            render_panel_header(
                "Damage Intelligence",
                "🏚️",
                "The structural stream supports local xBD tier3 records, uploaded imagery, and Roboflow-ready inference with a controlled fallback path.",
            )
            render_damage_breakdown_chart(damage_summary["class_breakdown"])
        with insight_cols[1]:
            render_panel_header(
                "SOS Intelligence",
                "📨",
                "The SOS stream supports sample or uploaded CSV files, structured extraction through Gemini, and heuristic fallback when external extraction is unavailable.",
            )
            render_sos_priority_chart(sos_events)

    if selected_mode == "Damage Mapping":
        render_panel_header(
            "Structural Damage Mapping",
            "🛰️",
            "Review the selected image, inspect predicted structure classes, and validate whether the image stream is coming from xBD, uploaded imagery, or the mock fallback.",
        )

        left_column, right_column = st.columns([1.7, 1])
        with left_column:
            if damage_context.get("image_bytes"):
                render_damage_figure(
                    image_bytes=damage_context["image_bytes"],
                    detections=detections,
                    title=f"Damage Overlay: {damage_context['record_id']}",
                )
            else:
                render_side_note(
                    "Waiting For Imagery",
                    "Select a tier3 record or upload a satellite image to activate the structural overlay canvas.",
                )

        with right_column:
            render_side_note("Pipeline Status", damage_context["status"])
            metadata = damage_context.get("metadata", {})
            render_status_chips(
                [
                    (damage_context["source"], "rgba(59,130,246,0.15)", "#93c5fd"),
                    (f"Record: {damage_context['record_id']}", "rgba(255,255,255,0.1)", "#f8fafc"),
                ]
            )
            if metadata:
                st.markdown("**Scene Metadata**")
                st.json(
                    {
                        "image_name": damage_context.get("image_name"),
                        "disaster": metadata.get("disaster"),
                        "disaster_type": metadata.get("disaster_type"),
                        "capture_date": metadata.get("capture_date"),
                        "sensor": metadata.get("sensor"),
                        "image_size": [metadata.get("width"), metadata.get("height")],
                    }
                )

        bottom_cols = st.columns([1.05, 1.15])
        with bottom_cols[0]:
            render_panel_header(
                "Damage Breakdown",
                "📊",
                "Severity counts are normalized into destroyed, damaged, intact, and unknown so downstream phases can consume a stable schema.",
            )
            render_damage_breakdown_chart(damage_summary["class_breakdown"])
        with bottom_cols[1]:
            render_panel_header(
                "Detection Preview",
                "🔎",
                "The table below shows the first set of normalized detections that later phases will use for fusion, logistics, and reporting.",
            )
            render_detection_table(detections)

    if selected_mode == "SOS Fusion":
        render_panel_header(
            "Crowdsourced SOS Extraction",
            "📍",
            "Convert raw emergency messages into structured, actionable event objects with location, urgency, incident type, and people-count signals.",
        )

        left_column, right_column = st.columns([1.3, 1])
        with left_column:
            render_side_note("Extraction Status", sos_context["status"])
            render_status_chips(
                [
                    (sos_context["source"], "rgba(59,130,246,0.15)", "#93c5fd"),
                    (f"Mode: {sos_context['extraction_mode']}", "rgba(20,184,166,0.15)", "#5eead4"),
                    (f"Geocoding: {config.geocoding_provider}", "rgba(167, 139, 250, 0.15)", "#c4b5fd"),
                    (f"Records: {sos_context['record_count']}", "rgba(245,158,11,0.15)", "#fcd34d"),
                ]
            )
            st.markdown("**Structured SOS Events**")
            st.dataframe(sos_context["dataframe_preview"], use_container_width=True, hide_index=True)
        with right_column:
            render_panel_header(
                "Urgency Mix",
                "📨",
                "This view helps command staff understand whether the feed is dominated by life-threatening collapses or medium-priority infrastructure needs.",
            )
            render_sos_priority_chart(sos_events)
            render_side_note(
                "Map Fusion Staged",
                "Coordinates acquired. Scroll down to see the fused geographic overview.",
            )

        st.markdown("<div style='height: 2rem'></div>", unsafe_allow_html=True)
        render_panel_header(
            "Geocoding & Map Fusion",
            "🗺️",
            "SOS events and structural damage points fused on the same geographical plane to isolate overlapping hotspots for immediate dispatch."
        )
        map_cols = st.columns([1.5, 1])
        with map_cols[0]:
            render_fused_map(detections, hotspots)
        with map_cols[1]:
            render_hotspot_table(hotspots)

    if selected_mode == "Logistics":
        render_panel_header(
            "Predictive Logistics",
            "🚑",
            "These estimates are derived from the live damage summary and convert structural loss into practical ground requirements.",
        )
        logistics_cards = st.columns(4)
        with logistics_cards[0]:
            render_metric_card("Destroyed Input", str(logistics_summary["destroyed_structures"]), "🏚️", "linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)", "Primary input for all downstream supply estimates")
        with logistics_cards[1]:
            render_metric_card("Water Needed", f"{logistics_summary['water_liters']} L", "💧", "linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)", "Rapid relief estimate for initial field deployment")
        with logistics_cards[2]:
            render_metric_card("Emergency Cots", str(logistics_summary["emergency_cots"]), "🛏️", "linear-gradient(135deg, #f59e0b 0%, #b45309 100%)", "Immediate shelter capacity placeholder")
        with logistics_cards[3]:
            render_metric_card("Medical Kits", str(logistics_summary["medical_kits"]), "🩺", "linear-gradient(135deg, #14b8a6 0%, #0f766e 100%)", "Baseline trauma and first-aid projection")

    if selected_mode == "SITREP":
        render_panel_header(
            "Automated Situation Report",
            "📝",
            "The SITREP view converts clean, structured metrics into a fast-release narrative for emergency officials and funding decisions.",
        )
        render_side_note("Draft Output", generate_sitrep_preview(sitrep_payload))

    if selected_mode == "Dispatch":
        render_panel_header(
            "Field Dispatch Preview",
            "📡",
            "This module will bridge the dashboard and low-connectivity responders through concise hotspot-specific SMS instructions.",
        )
        render_side_note("Dispatch Draft", dispatch_preview)


if __name__ == "__main__":
    main()
