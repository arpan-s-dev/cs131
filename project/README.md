# CS 131 Final Project - Big Data with Gaia DR3

**Course:** CS 131 · **Student:** Arpanjeet Singh ([@arpan-s-dev](https://github.com/arpan-s-dev)),
Group 17 · **Presented:** Aug 3

> Full project overview, results, and reproduction steps are in the
> [repository README](../README.md). This file is the deliverable index.

## Question
What do the motions of 100M+ stars reveal about the **dark matter** binding the Milky Way?
We build the Galactic **rotation curve** (orbital speed vs. distance from the centre). A *flat*
curve, instead of the falling Keplerian one predicted by visible matter alone, is the classic
fingerprint of dark matter.

## Answer (from 129,016,649 rows -> 1,839,385 quality stars)
The curve is **flat at ~215 km/s out to 15 kpc**. Visible matter alone predicts a fall to
~159 km/s. Roughly **two-thirds of the mass inside 15 kpc emits no light**. The pipeline
self-validates by recovering the Sun's own speed (220.9 km/s) with no tuning.

## Dataset
ESA **Gaia DR3 `gaia_source`** - 1.81 billion stars, ~613 GB gzipped CSV, 3,386 HEALPix files.
We use an all-sky slice of **242 files (53.7 GB, >50M rows)** in a GCS bucket, read from Spark
via `gs://`. Raw data is never committed (`.gitignore` -> `data/`).

## Tools
Command-line pipelines (Phase 1) · Excel + pandas, to break them (Phase 2) ·
PySpark on **Google Cloud Dataproc** reading from GCS (Phase 3) · matplotlib + astropy (Phase 4).

## Deliverables by phase
| Path | Phase | Deliverable | Result |
|------|-------|-------------|--------|
| [`1_profile/profiling.txt`](1_profile/profiling.txt) | 1 - Profiling | CLI commands + `time` | 64.7M rows, 26 GB, flat memory |
| [`2_breaking/`](2_breaking/) | 2 - Breaking | `breaking.txt` + screenshots + `try_pandas.py` | Excel cap; pandas OOM at 29.3 GB |
| [`3_scaling/`](3_scaling/) | 3 - Scaling | `rotation_curve.py`, `scaling.txt`, `results/` | 1/2/4 machines: 1471/685/364 s (4.05x) |
| [`4_poster/`](4_poster/) | 4 - Analysis | `poster_final.pdf`, `analysis.ipynb`, `figures/` | flat curve = dark matter |
