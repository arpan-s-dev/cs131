# CS 131 Final Project — Big Data with Gaia DR3

**Course:** CS 131 · **Format:** Pairs · **In-class presentation:** Aug 3

## Team
- Arpanjeet Singh — [@arpan-s-dev](https://github.com/arpan-s-dev)
- _Partner name / GitHub handle_ — **TODO**

## Question
**What do the motions of ~50M+ stars reveal about the Milky Way — the dark matter
binding it, and the stars fast enough to escape it?**
- **Dark matter:** build the galactic **rotation curve** (orbital speed vs. distance
  from the galactic center). A *flat* curve — instead of the falling, Keplerian one
  predicted by visible matter alone — is the classic fingerprint of dark matter, and
  it sets the galaxy's escape velocity.
- **Escaping stars:** rank stars by space velocity and count those above the escape
  speed (~500–550 km/s); map whether the runaways trace back to the galactic center
  (black-hole slingshots) or the disk (supernova kicks).

One computed velocity per star powers both: the rotation curve sets the galaxy's
"speed limit," and the runaway search finds the stars breaking it.

## Dataset
ESA **Gaia DR3 `gaia_source`** — the full-sky star catalog: **1.81 billion stars**,
**~613 GB gzipped CSV**, split into **3,386 HEALPix files** (`GaiaSource_*.csv.gz`).
We use a ~100–120 file slice (**>50M rows, >5 GB**) kept in a GCS bucket and read
from Spark via `gs://`. **Raw data is never committed** (see repo `.gitignore` → `data/`).

## Tools
Command-line pipelines (Phase 1) · Excel + pandas — to break them (Phase 2) ·
PySpark on **Google Cloud Dataproc** reading from GCS (Phase 3) · matplotlib (Phase 4).

## Repo layout
| Path | Phase | Deliverable |
|------|-------|-------------|
| [`1_profile/profiling.txt`](1_profile/profiling.txt) | 1 — Profiling | exact CLI commands + `time` results |
| [`2_breaking/`](2_breaking/) | 2 — Breaking | `breaking.txt` + Excel/pandas failure screenshots |
| [`3_scaling/`](3_scaling/) | 3 — Scaling | PySpark code, `scaling.txt` (1/2/4-worker runtimes), results |
| [`4_poster/`](4_poster/) | 4 — Analysis | final poster PDF |

## Status
🚧 **Scaffold only** — analysis not yet run. Each phase file contains a template
with `TODO` markers to fill in as the work is done.
