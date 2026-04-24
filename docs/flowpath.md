# ResQMap AI Flowpath

## 1. System Goal

Build a command-center dashboard that reduces disaster-response latency by combining aerial damage detection, SOS extraction, predictive logistics, formal reporting, and SMS dispatch in one operational view.

## 2. Product Logic

The system should behave in this order:

1. ingest post-disaster imagery
2. detect building damage levels
3. ingest crowdsourced SOS messages
4. extract locations and convert them to coordinates
5. fuse damage detections and SOS points on a map
6. estimate impacted population and required supplies
7. generate a formal situation report
8. dispatch field instructions by SMS

This order matters because the map is the central operational object. All later decisions should derive from validated map intelligence.

## 3. Recommended Build Order

### Phase 1: Foundation

Goal:
Create the Streamlit shell, shared config, mock data loaders, and module boundaries.

Deliverables:

- sidebar navigation
- dashboard summary cards
- placeholder map section
- environment variable handling
- docs for setup and delivery order

GitHub push point:
Push after the app runs locally and the repo structure is stable.

Suggested commit:
`chore: bootstrap ResQMap AI streamlit project structure`

### Phase 2: Damage Mapping

Goal:
Integrate the imagery inference pipeline first, because it produces the primary rescue grid.

Deliverables:

- image upload or dataset loader
- Roboflow request adapter
- normalized detection schema
- damage counts by severity
- map overlay for damaged structures

Questions to settle before coding:

- input format for imagery
- expected Roboflow model response schema
- whether detections arrive as bounding boxes only or include polygons

GitHub push point:
Push once the app can process one sample image end-to-end and render detections on the dashboard.

Suggested commit:
`feat: add structural damage mapping pipeline`

### Phase 3: SOS Fusion

Goal:
Build the secondary signal that confirms human distress on the ground.

Deliverables:

- SOS text ingestion from CSV, JSON, or form input
- Gemini extraction prompt template
- geocoding adapter
- normalized SOS event schema
- flashing or highlighted SOS map pins
- overlap logic between SOS points and red-zone structures

Key rule:
Do not hard-couple extraction, geocoding, and fusion. Keep them as separate functions so they can be tested with mock data.

GitHub push point:
Push after overlap between damage zones and SOS pins is visible and measurable.

Suggested commit:
`feat: fuse SOS intelligence with structural damage map`

### Phase 4: Predictive Logistics

Goal:
Turn detected damage into action-ready supply estimates.

Deliverables:

- destroyed-structure counts
- configurable demographic assumptions
- formulas for trapped population, water, cots, medical kits, and rescue teams
- dashboard cards and charts for logistics output

Design note:
Keep all heuristics in config, not inline in the UI, because these assumptions will change by region and disaster type.

GitHub push point:
Push once logistics numbers update automatically from live detection totals.

Suggested commit:
`feat: add predictive logistics estimator`

### Phase 5: SITREP Generation

Goal:
Generate a formal report from already-computed facts, not from raw data.

Deliverables:

- structured SITREP input payload
- Gemini report generation adapter
- preview panel
- copy or download action

Key rule:
Feed Gemini clean summarized metrics, not raw imagery or unfiltered SOS texts.

GitHub push point:
Push when a stable SITREP draft is generated from dashboard metrics.

Suggested commit:
`feat: generate automated disaster sitrep`

### Phase 6: SMS Dispatch

Goal:
Close the loop from insight to field execution.

Deliverables:

- Twilio configuration
- contact group input
- dispatch message builder
- send status logging

Operational rule:
Only dispatch from already-ranked hotspots. The SMS feature should consume validated outputs from the map and logistics modules.

GitHub push point:
Push when a test dispatch can be triggered from a selected hotspot using sandbox credentials.

Suggested commit:
`feat: add frontline sms dispatch workflow`

### Phase 7: Hardening and Demo Readiness

Goal:
Prepare the project for judging, demos, and future extension.

Deliverables:

- error states and empty states
- basic tests for pure logic
- mock mode when APIs are unavailable
- cleaner visuals
- deployment checklist

GitHub push point:
Push after demo mode works without external dependencies.

Suggested commit:
`chore: harden demo flow and fallback states`

## 4. Architecture

### Frontend Layer

Streamlit should orchestrate inputs, outputs, and operator workflows:

- dataset selection
- map view
- analytics cards
- report generation
- dispatch controls

### Domain Modules

- `damage_mapping.py`: inference call, response normalization, severity aggregation
- `sos_fusion.py`: text extraction, geocoding, hotspot overlap
- `logistics.py`: heuristic calculations
- `sitrep.py`: report payload construction and text generation
- `dispatch.py`: outbound SMS

### Shared Layer

- `config.py`: env vars and heuristic constants
- `loaders.py`: imagery and SOS dataset ingestion

## 5. Data Contracts To Keep Stable

Define these early and avoid breaking them:

### Detection record

```python
{
    "id": "det-001",
    "label": "destroyed",
    "confidence": 0.93,
    "latitude": 28.6139,
    "longitude": 77.2090,
    "bbox": [xmin, ymin, xmax, ymax]
}
```

### SOS record

```python
{
    "id": "sos-001",
    "raw_text": "Help, roof collapsed near MG Road",
    "extracted_location": "MG Road",
    "latitude": 28.6121,
    "longitude": 77.2295,
    "priority": "high"
}
```

### Logistics summary

```python
{
    "destroyed_structures": 25,
    "estimated_people_trapped": 100,
    "water_liters": 500,
    "emergency_cots": 100,
    "medical_kits": 30
}
```

## 6. Immediate Next Steps

1. keep this scaffold as the baseline
2. integrate mock data so the whole UI can be demoed before real APIs
3. add the damage mapping module first
4. wait to wire Gemini and Twilio until the upstream data objects are stable

## 7. Practical Git Rhythm

Use short branches or direct commits if you are working alone, but push at the end of each completed phase above.

Minimum rule:

- push after every stable feature boundary
- push before introducing a new external API
- push before any major refactor
- tag or note the commit used for the final demo
