# ResQMap AI

ResQMap AI is a Streamlit-based disaster response dashboard that combines:

- structural damage detection from post-disaster imagery
- SOS text extraction and map fusion
- predictive logistics estimation
- AI-generated situation reports
- SMS dispatch to field responders

This repository is currently scaffolded for staged implementation. The datasets, API keys, and production integrations will be added incrementally.

## Planned Stack

- Frontend: Streamlit
- Mapping: Pydeck
- Data handling: Pandas
- Damage detection: Roboflow-hosted YOLOv8 inference
- NLP and report generation: Gemini
- Geocoding: pluggable service adapter
- Messaging: Twilio

## Project Structure

```text
app.py
graphify/
docs/
  flowpath.md
src/
  config.py
  ui/
    sections.py
  modules/
    damage_mapping.py
    sos_fusion.py
    logistics.py
    sitrep.py
    dispatch.py
  data/
    loaders.py
requirements.txt
.env.example
```

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Current Status

The repository contains:

- a Streamlit dashboard shell
- module placeholders for the full pipeline
- local xBD tier3 dataset ingestion for polygon-based annotations
- SOS CSV ingestion with Gemini-ready structured extraction and fallback logic
- a delivery flow document with Git push checkpoints

Implementation should follow [docs/flowpath.md](/C:/projects/Code-titans/docs/flowpath.md).
