# ResQMap AI Execution Checklist

This checklist is the operational sequence for the 14-hour hackathon build.

## Phase 0: Lock Decisions Before Coding More

Complete these decisions first:

- frontend: Streamlit
- image detection runtime: Roboflow Hosted API
- image model family: YOLO-based detector
- map rendering: Pydeck
- SOS extraction: Gemini
- geocoding: Google Maps Geocoding API
- SMS dispatch: Twilio
- primary imagery dataset: xBD or xView2-derived subset
- SOS demo data: curated CSV built by the team

Do not change these during the hackathon unless a blocker appears.

## Phase 1: Foundation Baseline

Goal:
Make the app runnable and stable with mock data before connecting external APIs.

Tasks:

1. create the Streamlit shell
2. keep shared config in one place
3. define stable data contracts for detections, SOS events, and logistics outputs
4. keep mock damage and SOS data available so the app always has a demo path
5. verify imports and basic app startup

Exit condition:

- the app opens locally
- all dashboard sections render without crashing
- no real API is required to demo the shell

GitHub push:

- push immediately after this phase
- commit message: `chore: bootstrap ResQMap AI streamlit project structure`

## Phase 2: Prepare Dataset Inputs

Goal:
Understand the real dataset structure before wiring inference logic.

Tasks:

1. inspect the downloaded xBD dataset folders
2. confirm whether labels are polygons, masks, json, or bounding boxes
3. confirm whether we are using pre-disaster images, post-disaster images, or both
4. select a small working subset for development
5. document the folder structure inside `docs/`

Expected output:

- final dataset folder naming
- one small subset reserved for local testing
- clear answer on whether YOLO label conversion is needed

Exit condition:

- we know exactly how to load one sample image and its annotation

GitHub push:

- push after dataset inspection notes and loader decisions are written down
- commit message: `docs: define xbd dataset loading strategy`

## Phase 3: Damage Mapping Vertical Slice

Goal:
Get one image through the detection pipeline and show damage counts in the app.

Tasks:

1. add image upload or dataset image selector
2. normalize detection results into one internal schema
3. render severity counts in the UI
4. keep a mock fallback path if the API is unavailable
5. support these labels:
   - destroyed
   - damaged
   - intact

Recommended implementation path:

- first use mock detection JSON
- then replace the source with Roboflow inference

Exit condition:

- one sample image can be processed end-to-end
- the dashboard updates damage totals from the returned detections

GitHub push:

- push after the first end-to-end image inference works
- commit message: `feat: add structural damage mapping pipeline`

## Phase 4: SOS Ingestion And Extraction

Goal:
Convert raw SOS texts into structured location events.

Tasks:

1. define the SOS CSV schema
2. load SOS records from CSV
3. create a Gemini prompt that extracts:
   - location text
   - severity
   - people count if stated
   - urgency
4. save the extracted result in a normalized schema
5. keep a mock extraction fallback

Recommended SOS CSV columns:

- `id`
- `message_text`
- `source`
- `timestamp`
- `priority`
- `location_text`

Exit condition:

- one SOS message becomes a structured event object
- the dashboard can ingest a CSV and show extracted SOS events even when Gemini is unavailable

GitHub push:

- push once the extraction pipeline is stable for a small sample batch
- commit message: `feat: add SOS extraction pipeline`

## Phase 5: Geocoding And Map Fusion

Goal:
Place SOS events on the same map as the damage detections and identify overlaps.

Tasks:

1. geocode the extracted location text
2. store latitude and longitude for each SOS event
3. render damage points or boxes on the map
4. render SOS pins on the same map
5. implement overlap or nearest-hotspot logic
6. flag critical overlap cases for dispatch priority

Exit condition:

- the map shows both structural damage and SOS pins
- at least one overlap score or hotspot ranking is computed

GitHub push:

- push after the map fusion workflow is visible in the UI
- commit message: `feat: fuse SOS intelligence with structural damage map`

## Phase 6: Predictive Logistics

Goal:
Convert fused damage intelligence into supply estimates.

Tasks:

1. count destroyed structures
2. apply household-size assumptions
3. estimate trapped civilians
4. estimate water, cots, and medical kits
5. show results as cards or charts

Rule:

- keep assumptions in config, not in UI code

Exit condition:

- logistics values update from detection totals automatically

GitHub push:

- push after logistics cards are wired to the live summary
- commit message: `feat: add predictive logistics estimator`

## Phase 7: Automated SITREP

Goal:
Generate a formal report from the computed metrics.

Tasks:

1. build a clean SITREP payload from summarized data
2. send only structured metrics to Gemini
3. render the generated report in the dashboard
4. add copy or export support if time allows

Rule:

- never feed raw unfiltered imagery metadata or noisy raw SOS text directly to report generation

Exit condition:

- the app can generate one coherent report from current metrics

GitHub push:

- push after SITREP generation is stable
- commit message: `feat: generate automated disaster sitrep`

## Phase 8: SMS Dispatch

Goal:
Send actionable instructions to field responders.

Tasks:

1. configure Twilio credentials
2. define the dispatch message template
3. choose hotspot-based dispatch targets
4. trigger SMS from the UI
5. show success or failure states

Rule:

- dispatch only from validated hotspot outputs, not from raw unreviewed records

Exit condition:

- one test message can be sent from the dashboard using sandbox credentials

GitHub push:

- push after a test dispatch succeeds
- commit message: `feat: add frontline sms dispatch workflow`

## Phase 9: Hardening For Demo

Goal:
Make the project resilient enough for judging and demos.

Tasks:

1. add empty states
2. add API failure states
3. preserve mock mode if APIs fail
4. clean the wording and layout
5. prepare a short demo script

Exit condition:

- the app can still be demonstrated if one external service fails

GitHub push:

- push after final demo stabilization
- commit message: `chore: harden demo flow and fallback states`

## Non-Negotiable Rules

- do not block UI progress waiting for the final dataset
- do not connect Twilio before hotspot selection exists
- do not connect SITREP before logistics outputs are stable
- do not tightly couple dataset loaders to the UI
- do not remove mock mode

## Current Decisions

These are now fixed unless a blocker appears:

1. use the Kaggle xBD mirror as the source dataset
2. use `tier3` as the working subset
3. prefer Roboflow hosted inference over full local training
4. Gemini and Twilio credentials are available
5. use India-based sample SOS locations for the first demo
