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
* Manuscript Draft: **In Progress**

This repository reflects the exact state of the analysis described in the
paper: a reliability-aware rotation inference framework for single-sector
TESS data.

## System Architecture

```mermaid
graph TD
    %% --- STYLING ---
    classDef core fill:#64B5F6,stroke:#0D47A1,stroke-width:3px;
    classDef input fill:#FFD54F,stroke:#F57F17,stroke-width:2px;
    classDef decision fill:#E57373,stroke:#B71C1C,stroke-width:2px;
    classDef output fill:#66BB6A,stroke:#1B5E20,stroke-width:2px;
    classDef validate fill:#CE93D8,stroke:#4A148C,stroke-width:2px;

    %% --- BLOCK 0: SINGLE-STAR VALIDATION ---
    subgraph B0 [BLOCK 0: Diagnostic Validation]
        direction TB
        VIn[/"Input: Known TESS Targets <br> (Single Stars)"/]:::input
        VProc["Single-Star Pipeline Run <br> (LS + ACF + Folding)"]
        VCheck["Visual Inspection <br> (P vs P/2 Morphology)"]
        VOut[/"Output: Sanity-Checked Logic <br> & Fixed Thresholds"/]:::validate

        VIn --> VProc --> VCheck --> VOut
    end

    %% --- BLOCK 1: SAMPLE CONSTRUCTION ---
    subgraph B1 [PHASE 1: Sample Construction]
        direction TB
        Archive[("TESS MAST Archive <br> (SPOC PDCSAP)")]:::input
        Filters["Apply Dwarf Filters: <br> 2500 K ≤ Teff ≤ 4000 K <br> log g ≥ 4.0"]
        SampleCSV[/"Output: sector18_mdwarf_sample.csv"/]:::output

        Archive --> Filters --> SampleCSV
    end

    VOut -.-> B1

    %% --- BLOCK 2: CORE ROTATION PIPELINE ---
    subgraph B2 [PHASE 2: Harmonic-Aware Rotation Pipeline]
        direction TB

        Preproc["Preprocessing: <br> NaN Removal, Median Norm, <br> Optional 2-hr Binning"]

        LS["Lomb–Scargle <br> (0.5–15 d, FAP < 1%)"]
        ACF["Autocorrelation <br> (Lag > 0.5 d)"]

        Logic{"Harmonic-Aware <br> Decision Engine"}:::decision

        H1["LS ≈ P/2 → Use ACF"]
        H2["LS ≈ 2P → Use ACF"]
        Agree["LS ≈ ACF → Use LS"]
        LSOnly["ACF Fail → LS Only"]

        Diag["Phase-Fold Diagnostics <br> (P and P/2)"]

        FinalCat[/"Output: Rotation Catalog <br> (P_final + Flag)"/]:::output

        SampleCSV --> Preproc
        Preproc --> LS & ACF
        LS & ACF --> Logic

        Logic -- "P_ACF ≈ 2·P_LS" --> H1
        Logic -- "P_ACF ≈ 0.5·P_LS" --> H2
        Logic -- "Agreement" --> Agree
        Logic -- "No ACF" --> LSOnly

        H1 & H2 & Agree & LSOnly --> Diag --> FinalCat
    end

    class B2 core

    %% --- BLOCK 3: INJECTION–RECOVERY ---
    subgraph B3 [PHASE 3: Injection–Recovery Validation]
        direction TB
        RealLC[/"Real Sector 18 Light Curves"/]:::input
        Inject["Inject Synthetic Signals <br> (P_true, Amplitude, Phase)"]
        RunPipe["Run Unmodified Pipeline"]
        Compare["Compare P_final vs P_true"]
        Metrics[/"Output: Recovery & Harmonic Rates"/]:::validate

        RealLC --> Inject --> RunPipe --> Compare --> Metrics
    end

    %% --- BLOCK 4: RELIABILITY LAYER ---
    subgraph B4 [PHASE 4: Reliability Calibration]
        direction TB
        Features["Extract Diagnostics: <br> LS Power, ACF Peak, Agreement"]
        Score["Compute R = 0–3"]
        Calib["Map R → Recovery Probability"]
        FinalOut[/"Output: Reliability-Aware Catalog <br> (P, Flag, R)"/]:::output

        FinalCat --> Features --> Score
        Metrics --> Calib
        Score --> Calib --> FinalOut
    end
