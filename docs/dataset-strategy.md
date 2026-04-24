# ResQMap AI Dataset Strategy

This project will not use the full 33.97 GB Kaggle mirror locally during initial development.

## Locked Decisions

- imagery source for development: `qianlanzz/xbd-dataset`
- working subset: `xbd/tier3`
- frontend: Streamlit
- image inference path: Roboflow hosted inference
- SOS demo geography: India-based sample locations

## Why We Are Using Only `tier3`

The Kaggle mirror exposes five top-level directories:

- `hold`
- `test`
- `tier1`
- `tier3`
- `train`

For this hackathon, we should not attempt to download and process the full dataset.
The visible Kaggle file explorer shows that `tier3` already contains:

- `images`
- `labels`
- `masks`

That makes it the correct working subset for quick iteration.

## Recommendation: Do Not Download The Entire Dataset First

The full Kaggle mirror is too large for efficient local iteration.
Our goal is to extract only a small development subset from `tier3`.

## Recommended Workflow

### Option A: Kaggle Notebook Subset Export

This is the safest path if the Kaggle CLI does not expose `tier3` as one downloadable archive.

Steps:

1. create a Kaggle notebook
2. attach the dataset `qianlanzz/xbd-dataset`
3. inspect `/kaggle/input/.../xbd/tier3`
4. copy only a small subset of files from:
   - `images`
   - `labels`
   - optionally `masks`
5. write them into `/kaggle/working/resqmap-tier3-subset`
6. zip that smaller folder
7. download the zip locally

Target subset size for development:

- `100` to `300` image-label pairs for UI and loader development
- `500` to `1000` pairs only if you later attempt quick fine-tuning

### Option B: Kaggle CLI Or API

Use this only if the Kaggle API shows `tier3` as a separately downloadable file or archive.

Useful checks:

```powershell
kaggle datasets files -d qianlanzz/xbd-dataset
```

If that command shows a single file such as a `tier3` archive, download only that archive.
If it lists thousands of nested files instead, do not try to script a full selective local pull as the first step.
Use the notebook-export workflow instead.

## Kaggle Authentication On Windows

Expected token location:

```text
C:\Users\himanshu\.kaggle\kaggle.json
```

Then verify:

```powershell
kaggle --version
kaggle datasets files -d qianlanzz/xbd-dataset
```

If the command works, authentication is correct.

## What We Need From `tier3`

For the first working version:

- post-disaster image files
- corresponding labels

Optional for later:

- masks

We do not need the entire benchmark during initial dashboard development.

## Confirmed Tier3 Annotation Format

A real `tier3` sample has now been inspected locally.

Confirmed facts:

- image files are `.png`
- label files are `.json`
- label records contain polygon annotations in `WKT`
- feature classes are stored in `properties.subtype`
- the file includes both geospatial polygons and image-space polygons

Normalized class mapping used in this repo:

- `destroyed` -> `destroyed`
- `major-damage` -> `damaged`
- `minor-damage` -> `damaged`
- `no-damage` -> `intact`
- `un-classified` -> `unknown`

This means the dataset can be used immediately for dashboard ingestion, but it is not directly in YOLO text format.
If YOLO training is attempted later, a conversion step from polygons to boxes will still be required.

## Local Environment Values

Use these local environment values for development:

```text
XBD_DATASET_ROOT=C:\datasets\resqmap\xbd
XBD_WORKING_SPLIT=tier3
XBD_IMAGE_STAGE=post_disaster
XBD_MAX_RECORDS=100
```

## Model Strategy

For this hackathon, do not train a full custom model locally from scratch.

Use this order:

1. build the app with mock detections
2. wire the image input flow
3. normalize label and detection schema
4. use Roboflow as the inference-facing path
5. only attempt a small fine-tune later if time remains

## Practical Recommendation

The correct balance of speed and credibility is:

- demo the full product workflow using a small `tier3` subset
- keep the app architecture ready for Roboflow inference
- avoid spending the early hackathon hours on full dataset download and heavy training
