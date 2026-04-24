from __future__ import annotations

from io import BytesIO

import pydeck as pdk
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

from src.modules.damage_mapping import damage_label_color


def render_global_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700;800&display=swap');

        :root {
            --bg-main: #0b1121;
            --bg-secondary: #131c31;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-red: #ef4444;
            --accent-amber: #f59e0b;
            --accent-teal: #14b8a6;
            --accent-blue: #3b82f6;
            --glass-bg: rgba(30, 41, 59, 0.45);
            --glass-border: rgba(255, 255, 255, 0.08);
            --glass-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            --primary-gradient: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
        }

        .stApp {
            background: 
                radial-gradient(circle at top left, rgba(59, 130, 246, 0.15), transparent 35%),
                radial-gradient(circle at top right, rgba(239, 68, 68, 0.1), transparent 35%),
                radial-gradient(circle at bottom, rgba(167, 139, 250, 0.08), transparent 40%),
                var(--bg-main);
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
        }

        [data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.6) !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
            border-right: 1px solid var(--glass-border) !important;
        }

        [data-testid="stSidebar"] * {
            color: var(--text-primary) !important;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2.5rem;
            max-width: 1400px;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Outfit', sans-serif !important;
            color: var(--text-primary) !important;
            letter-spacing: -0.02em;
        }

        .resq-hero {
            position: relative;
            overflow: hidden;
            padding: 2.5rem 3rem;
            margin-bottom: 2rem;
            border-radius: 28px;
            background: rgba(30, 41, 59, 0.4);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            box-shadow: var(--glass-shadow);
            transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.4s ease;
        }

        .resq-hero:hover {
            transform: translateY(-4px);
            box-shadow: 0 20px 40px 0 rgba(0, 0, 0, 0.4);
            border-color: rgba(255, 255, 255, 0.12);
        }

        .resq-hero::after {
            content: "";
            position: absolute;
            inset: auto -40px -55px auto;
            width: 320px;
            height: 320px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(59,130,246,0.2), transparent 70%);
            z-index: 0;
            pointer-events: none;
        }

        .resq-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.4rem 1rem;
            border-radius: 999px;
            background: rgba(59, 130, 246, 0.15);
            color: #93c5fd;
            font-size: 0.85rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-weight: 700;
            position: relative;
            z-index: 1;
            border: 1px solid rgba(147, 197, 253, 0.2);
        }

        .resq-title {
            margin: 1.25rem 0 0.75rem 0;
            font-size: 3.8rem;
            line-height: 1.1;
            font-weight: 800;
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            position: relative;
            z-index: 1;
            text-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }

        .resq-subtitle {
            max-width: 800px;
            margin: 0;
            color: var(--text-secondary);
            font-size: 1.15rem;
            line-height: 1.6;
            position: relative;
            z-index: 1;
        }

        .resq-badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-top: 1.75rem;
            position: relative;
            z-index: 1;
        }

        .resq-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.55rem 1.1rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: var(--text-primary);
            font-size: 0.9rem;
            font-weight: 600;
            backdrop-filter: blur(8px);
            transition: all 0.3s ease;
        }

        .resq-badge:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: translateY(-2px);
            border-color: rgba(255, 255, 255, 0.2);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }

        .resq-card {
            padding: 1.5rem;
            border-radius: 24px;
            border: 1px solid var(--glass-border);
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            box-shadow: var(--glass-shadow);
            min-height: 160px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
        }

        .resq-card::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            opacity: 0;
            transition: opacity 0.4s;
        }

        .resq-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            border-color: rgba(255, 255, 255, 0.15);
            background: rgba(40, 53, 75, 0.5);
        }

        .resq-card:hover::before {
            opacity: 1;
        }

        .resq-card-top {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
        }

        .resq-icon {
            width: 52px;
            height: 52px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            color: white;
            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
            background-blend-mode: overlay;
        }

        .resq-label {
            margin: 0;
            color: var(--text-secondary);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-weight: 700;
        }

        .resq-value {
            margin: 0.5rem 0 0 0;
            font-size: 2.8rem;
            line-height: 1;
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            color: var(--text-primary);
            text-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }

        .resq-foot {
            margin-top: 1.25rem;
            color: #64748b;
            font-size: 0.85rem;
            line-height: 1.4;
            font-weight: 500;
        }

        .resq-panel {
            padding: 1.75rem;
            border-radius: 24px;
            border: 1px solid var(--glass-border);
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            box-shadow: var(--glass-shadow);
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
        }

        .resq-panel:hover {
            border-color: rgba(255, 255, 255, 0.12);
            box-shadow: 0 12px 32px rgba(0,0,0,0.4);
        }

        .resq-panel-title {
            display: flex;
            align-items: center;
            gap: 0.85rem;
            margin-bottom: 1rem;
            font-size: 1.35rem;
            font-weight: 700;
            font-family: 'Outfit', sans-serif;
            color: var(--text-primary);
        }

        .resq-panel-copy {
            color: var(--text-secondary);
            margin-bottom: 1.25rem;
            line-height: 1.6;
            font-size: 1rem;
        }

        .resq-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.65rem;
            margin: 0.75rem 0 0.5rem 0;
        }

        .resq-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.45rem 0.9rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 600;
            border: 1px solid transparent;
            transition: all 0.2s ease;
            backdrop-filter: blur(4px);
        }

        .resq-chip:hover {
            transform: scale(1.03) translateY(-1px);
            filter: brightness(1.2);
        }

        .resq-kicker {
            margin-bottom: 0.6rem;
            color: #94a3b8;
            font-size: 0.8rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-weight: 700;
        }

        .resq-note {
            padding: 1.5rem;
            border-radius: 20px;
            background: rgba(15, 23, 42, 0.5);
            color: var(--text-secondary);
            border: 1px solid var(--glass-border);
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
            line-height: 1.6;
            transition: border-color 0.3s;
        }
        
        .resq-note:hover {
            border-color: rgba(255,255,255,0.1);
        }

        .resq-divider {
            height: 1px;
            margin: 1rem 0;
            background: linear-gradient(90deg, rgba(255,255,255,0.1), rgba(255,255,255,0.02));
        }
        
        /* Custom scrollbar for dark theme */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: var(--bg-main);
        }
        ::-webkit-scrollbar-thumb {
            background: #334155;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #475569;
        }
        
        /* Streamlit specific overrides for dark theme */
        .stDataFrame {
            background-color: transparent;
        }
        [data-testid="stDataFrame"] > div > div > div > div {
            background-color: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
        }
        
        /* Plotly charts text color adjustment */
        .js-plotly-plot .plotly text {
            fill: var(--text-secondary) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(title: str, subtitle: str, badges: list[str]) -> None:
    badge_markup = "".join(f"<span class='resq-badge'>{badge}</span>" for badge in badges)
    st.markdown(
        f"""
        <section class="resq-hero">
            <span class="resq-eyebrow">🚨 Emergency Command Console</span>
            <h1 class="resq-title">{title}</h1>
            <p class="resq-subtitle">{subtitle}</p>
            <div class="resq-badge-row">{badge_markup}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(
    label: str,
    value: str,
    icon: str = "●",
    tone: str = "#315f9f",
    footnote: str = "",
) -> None:
    st.markdown(
        f"""
        <section class="resq-card">
            <div class="resq-card-top">
                <div>
                    <p class="resq-label">{label}</p>
                    <p class="resq-value">{value}</p>
                </div>
                <div class="resq-icon" style="background:{tone};">{icon}</div>
            </div>
            <div class="resq-foot">{footnote}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_panel_header(title: str, icon: str, copy: str) -> None:
    st.markdown(
        f"""
        <section class="resq-panel">
            <div class="resq-panel-title">{icon} <span>{title}</span></div>
            <div class="resq-panel-copy">{copy}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_status_chips(items: list[tuple[str, str, str]]) -> None:
    chip_markup = "".join(
        f"<span class='resq-chip' style='background:{background}; color:{color}; border-color:{color}22;'>{label}</span>"
        for label, background, color in items
    )
    st.markdown(f"<div class='resq-chip-row'>{chip_markup}</div>", unsafe_allow_html=True)


def render_side_note(title: str, body: str) -> None:
    st.markdown(
        f"""
        <section class="resq-note">
            <div class="resq-kicker">{title}</div>
            <div>{body}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_architecture_note() -> None:
    render_side_note(
        "Operational Logic",
        "Damage detections define the search grid, SOS messages validate human distress, "
        "logistics are derived from validated damage totals, and SITREP plus dispatch should "
        "consume structured summaries rather than raw inputs.",
    )


def render_damage_figure(
    image_bytes: bytes,
    detections: list[dict],
    title: str,
    max_shapes: int = 250,
) -> None:
    image = Image.open(BytesIO(image_bytes))
    width, height = image.size
    figure = go.Figure()

    figure.add_layout_image(
        dict(
            source=image,
            x=0,
            y=0,
            sizex=width,
            sizey=height,
            xref="x",
            yref="y",
            sizing="stretch",
            layer="below",
        )
    )

    for detection in detections[:max_shapes]:
        bbox = detection.get("bbox")
        if not bbox:
            continue

        x0, y0, x1, y1 = bbox
        color = damage_label_color(detection["label"])
        figure.add_shape(
            type="rect",
            x0=x0,
            y0=y0,
            x1=x1,
            y1=y1,
            line={"color": color, "width": 2.5},
            fillcolor="rgba(0,0,0,0)",
        )
        figure.add_annotation(
            x=x0,
            y=max(y0 - 12, 0),
            text=f"{detection['label']}",
            showarrow=False,
            font={"color": color, "size": 11},
            bgcolor="rgba(255,252,247,0.86)",
            bordercolor=color,
            borderwidth=1,
        )

    figure.update_layout(
        title=title,
        height=700,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 10, "r": 10, "t": 54, "b": 10},
        xaxis={"range": [0, width], "visible": False},
        yaxis={"range": [height, 0], "visible": False, "scaleanchor": "x"},
    )
    st.plotly_chart(figure, use_container_width=True)


def render_detection_table(detections: list[dict], max_rows: int = 20) -> None:
    rows = []
    for detection in detections[:max_rows]:
        bbox = detection.get("bbox")
        rows.append(
            {
                "id": detection["id"],
                "label": detection["label"],
                "raw_label": detection.get("raw_label"),
                "confidence": round(detection.get("confidence", 0), 3),
                "bbox": [round(value, 1) for value in bbox] if bbox else None,
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_damage_breakdown_chart(class_breakdown: dict[str, int]) -> None:
    if not class_breakdown:
        st.info("No damage classes available yet.")
        return

    ordered_labels = list(class_breakdown.keys())
    values = [class_breakdown[label] for label in ordered_labels]
    colors = [damage_label_color(label if "-" not in label else _normalize_chart_label(label)) for label in ordered_labels]

    figure = go.Figure(
        data=[
            go.Bar(
                x=values,
                y=ordered_labels,
                orientation="h",
                marker={"color": colors, "line": {"width": 0}},
                text=values,
                textposition="outside",
            )
        ]
    )
    figure.update_layout(
        height=300,
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False},
        yaxis={"title": None},
    )
    st.plotly_chart(figure, use_container_width=True)


def render_sos_priority_chart(events: list[dict]) -> None:
    priority_counts: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for event in events:
        priority = str(event.get("urgency", "low")).lower()
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

    figure = go.Figure(
        data=[
            go.Bar(
                x=list(priority_counts.keys()),
                y=list(priority_counts.values()),
                marker={
                    "color": ["#cf3b2f", "#d48d1f", "#1e7f72"],
                    "line": {"width": 0},
                },
            )
        ]
    )
    figure.update_layout(
        height=280,
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis={"title": None},
        xaxis={"title": None},
    )
    st.plotly_chart(figure, use_container_width=True)


def _normalize_chart_label(raw_label: str) -> str:
    if raw_label in {"major-damage", "minor-damage"}:
        return "damaged"
    if raw_label == "no-damage":
        return "intact"
    if raw_label == "un-classified":
        return "unknown"
    return raw_label


def render_fused_map(damage_detections: list[dict], hotspots: list[dict]) -> None:
    damage_data = []
    for d in damage_detections:
        if "latitude" in d and "longitude" in d:
            lbl = d.get("label", "")
            if lbl == "destroyed":
                color = [239, 68, 68, 200]
            elif lbl == "damaged":
                color = [245, 158, 11, 200]
            else:
                color = [20, 184, 166, 150]
            damage_data.append({
                "latitude": d["latitude"],
                "longitude": d["longitude"],
                "label": lbl,
                "color": color
            })
    
    damage_layer = pdk.Layer(
        "ScatterplotLayer",
        data=damage_data,
        get_position="[longitude, latitude]",
        get_color="color",
        get_radius=40,
        pickable=True,
    )
    
    hotspot_data = []
    for h in hotspots:
        color = [239, 68, 68, 255] if h.get("needs_dispatch") else [245, 158, 11, 255]
        hotspot_data.append({
            "position": [h["longitude"], h["latitude"]],
            "color": color,
            "text": h["location_text"],
            "urgency": h["urgency"]
        })
        
    sos_layer = pdk.Layer(
        "ScatterplotLayer",
        data=hotspot_data,
        get_position="position",
        get_color="color",
        get_radius=150,
        pickable=True,
    )
    
    view_state = pdk.ViewState(
        latitude=28.6139, # Default center Delhi
        longitude=77.2090,
        zoom=12,
        pitch=45,
    )
    
    if damage_data or hotspots:
        valid_lats = [d["latitude"] for d in damage_data] + [h["latitude"] for h in hotspots]
        valid_lngs = [d["longitude"] for d in damage_data] + [h["longitude"] for h in hotspots]
        if valid_lats:
            view_state.latitude = sum(valid_lats) / len(valid_lats)
            view_state.longitude = sum(valid_lngs) / len(valid_lngs)

    r = pdk.Deck(
        layers=[damage_layer, sos_layer],
        initial_view_state=view_state,
        map_style="dark",
        tooltip={"text": "{label}{text} - {urgency}"}
    )
    st.pydeck_chart(r)

def render_hotspot_table(hotspots: list[dict], max_rows: int = 15) -> None:
    if not hotspots:
        st.info("No hotspots generated yet.")
        return
    st.dataframe(hotspots[:max_rows], use_container_width=True, hide_index=True)
