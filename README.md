# Reliability-Aware Stellar Rotation from Single-Sector TESS Data

This repository contains a complete, reproducible analysis pipeline for
inferring stellar rotation periods from *single-sector* TESS photometry,
with an explicit focus on **diagnostic transparency and reliability**.

The project develops and validates a hybrid Lomb–Scargle + autocorrelation
framework that:

* Detects rotation periods in late-type dwarf stars,
* Identifies and resolves harmonic ambiguities,
* Encodes diagnostic behavior explicitly, and
* Assigns each star a *quantitative, empirically calibrated reliability score*.

Rather than producing a flat catalog of periods, the pipeline yields a
**reliability-aware rotation catalog** in which every measurement carries
a principled estimate of how likely it is to be correct under realistic
single-sector conditions.

This work is designed for the most failure-prone regime of TESS rotation
science: a ∼27-day baseline, evolving starspot signals, and frequent
diagnostic disagreement. Injection–recovery experiments on real light curves
are used to map diagnostic outcomes to true performance.

---

## Project Scope

* Data source: TESS SPOC PDCSAP 2-minute cadence light curves
* Target stars: Late-K and M dwarfs (TESS Sector 18)
* Core methods:

  * Lomb–Scargle periodogram
  * Autocorrelation function (ACF)
  * Harmonic-aware decision logic
  * Injection–recovery validation
  * Quantitative reliability scoring
* Scientific goal:

  * Build and validate a **reliability-aware stellar rotation catalog**
    for single-sector TESS data

While the original motivation included stellar–planetary correlations,
this repository now focuses on constructing and validating the
rotation-inference framework itself. Planetary cross-matching is deferred
to future work.

---

## Repository Structure

```
.
├── src/                # Pipeline implementation
│   ├── phase1_build_sample/
│   ├── phase2_rotation_pipeline/
│   └── validation/     # Injection–recovery and diagnostic scripts
│
├── analysis/           # Post-processing and figure generation
│   ├── assign_rotation_reliability.py
│   ├── analyze_R_score_validation.py
│   ├── make_injection_validation_plots.py
│   └── make_summary_plots.py
│
├── data/
│   ├── raw/            # (empty – raw TESS data fetched on demand)
│   └── processed/      # Derived catalogs and validation tables
│
├── results/
│   ├── injection_validation/   # Publication figures from injections
│   ├── phase2_plots/            # Pilot and diagnostic plots
│   ├── summary_plots/
│   └── summary_tables/
│
├── docs/               # Manuscript material and methodology notes
├── environment/        # Reproducible Python environment
│   └── requirements.txt
└── README.md
```

---

## Reproducibility

### 1. Build stellar sample (Sector 18 late-type dwarfs)
python src/phase1_build_sample/phase1_build_sample_sector18.py

### 2. Run rotation inference pipeline (LS + ACF + harmonic logic)
python src/phase2_rotation_pipeline/phase2_run_rotation_full.py

### 3. Assign reliability scores (R = 0–3)
python analysis/assign_rotation_reliability.py

### 4. Perform injection–recovery validation
python src/validation/injection_recovery.py

### 5. Generate figures used in the manuscript
python analysis/make_injection_validation_plots.py
python analysis/make_summary_plots.py


All analyses were performed using Python 3.10+.
Exact package versions are listed in `environment/requirements.txt`.

The pipeline is fully deterministic given:

* A fixed TESS sector,
* The same preprocessing steps,
* The same threshold values,
* And the same injection parameter grid.

Injection–recovery experiments are end-to-end: synthetic signals are
embedded directly into real light curves and processed by the *unmodified*
pipeline.

---

## Project Status

* Phase 1 — Sample Construction: **Complete**
* Phase 2 — Rotation Pipeline: **Complete**
* Injection–Recovery Validation: **Complete**
* Reliability Scoring Layer: **Complete**
* Manuscript Draft: **complete**

This repository reflects the exact state of the analysis described in the
paper: a reliability-aware rotation inference framework for single-sector
TESS data.

## System Architecture

```mermaid
graph TD

    %% =========================
    %% INPUT DATA
    %% =========================
    TESS["TESS Sector 18<br>PDCSAP Light Curves"]:::input

    %% =========================
    %% PHASE 1: SAMPLE
    %% =========================
    subgraph P1["PHASE 1: Sample Construction"]
        Filters["Late-Type Dwarf Filters<br>(2500K ≤ Teff ≤ 4000K,<br>log g ≥ 4.0)"]
        Sample["sector18_mdwarf_sample.csv"]:::output
        TESS --> Filters --> Sample
    end

    %% =========================
    %% PHASE 2: ROTATION PIPELINE
    %% =========================
    subgraph P2["PHASE 2: Rotation Inference Pipeline"]
        Preproc["Preprocessing<br>(NaN removal, median norm,<br>no aggressive detrending)"]
        LS["Lomb–Scargle<br>(0.5–15 d, FAP < 1%)"]
        ACF["Autocorrelation<br>(lag > 0.5 d)"]
        Logic{"Harmonic-Aware<br>Decision Logic"}:::decision
        Diag["Phase-Fold Diagnostics<br>(P and P/2)"]
        Catalog["Rotation Output<br>(P_final, Flag)"]:::output

        Preproc --> LS
        Preproc --> ACF
        LS --> Logic
        ACF --> Logic
        Logic --> Diag --> Catalog
    end

    Sample --> Preproc

    %% =========================
    %% PHASE 3: INJECTION–RECOVERY
    %% =========================
    subgraph P3["PHASE 3: Injection–Recovery Experiment"]
        Inject["Inject Synthetic<br>Rotation Signals"]
        RunPipe["Run Same Rotation<br>Pipeline"]
        Metrics["Recovery & Harmonic<br>Statistics"]:::output

        TESS --> Inject --> RunPipe --> Metrics
    end

    %% Reuse the same pipeline conceptually
    RunPipe -.-> P2

    %% =========================
    %% PHASE 4: RELIABILITY MODEL
    %% =========================
    subgraph P4["PHASE 4: Reliability Calibration"]
        Rscore["Calibrate Reliability Score R"]:::output
    end

    Metrics --> Rscore
    Catalog --> Rscore

    %% =========================
    %% FINAL PRODUCT
    %% =========================
    Final["Final Rotation Catalog<br>(P_final, Flag, R)"]:::output
    Rscore --> Final


    %% =========================
    %% STYLES
    %% =========================
    classDef input fill:#FFD54F,stroke:#F57F17,stroke-width:2px;
    classDef decision fill:#E57373,stroke:#B71C1C,stroke-width:2px;
    classDef output fill:#66BB6A,stroke:#1B5E20,stroke-width:2px;
 