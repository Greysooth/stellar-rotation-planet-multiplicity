# Stellar Rotation and Planetary Multiplicity using TESS

This repository contains the data analysis pipeline developed to study the
relationship between stellar rotation periods and planetary system multiplicity
for late-type dwarf stars observed by TESS.

## Project Overview
- Data source: TESS SPOC PDCSAP light curves
- Target stars: Late-K and M dwarfs
- Methods: Lomb–Scargle periodogram, autocorrelation function (ACF),
  harmonic-aware period selection
- Goal: Compare rotation period distributions of single-planet and multi-planet systems

## Repository Structure
- docs/        : Methodology, figures, related work
- src/         : Analysis scripts (Phase 1 & Phase 2)
- data/        : Derived catalogs (raw TESS data not included)
- results/     : Plots and summary tables
- environment/ : Reproducible Python environment files

## Reproducibility
All analyses were performed using Python 3.10+.
Exact package versions are listed in `environment/requirements.txt`.

## Status
- Phase 1 (Sample Selection): Completed
- Phase 2 (Rotation Analysis): Pilot run in progress

## System Architecture

```mermaid
graph TD
    %% --- STYLING (UPDATED FOR HIGH CONTRAST) ---
    %% Core: Stronger Blue for the main pipeline
    classDef core fill:#90CAF9,stroke:#1565C0,stroke-width:3px;
    %% Input: Deeper Gold/Amber to stand out against white
    classDef input fill:#FFF59D,stroke:#FBC02D,stroke-width:2px;
    %% Decision: Distinct Red/Pink for logic gates
    classDef decision fill:#EF9A9A,stroke:#C62828,stroke-width:2px;
    %% Output: Solid Green for results
    classDef output fill:#A5D6A7,stroke:#2E7D32,stroke-width:2px;

    %% --- BLOCK 0: VALIDATION ---
    subgraph B0 [BLOCK 0: Validation Layer]
        direction TB
        InputVal[/"Inputs: TESS Sector 18 <br> & Lit. Period (Paudel et al. 2025)"/]:::input
        ProcessVal["Benchmark Validation <br> (TIC 445493624)"]
        MethodVal["Lomb-Scargle + ACF + Phase Folding"]
        OutputVal[/"Output: Verified Harmonic Behavior <br> & Parameter Calibration"/]:::output

        InputVal --> ProcessVal
        ProcessVal --> MethodVal
        MethodVal --> OutputVal
    end

    %% --- BLOCK 1: SAMPLE CONSTRUCTION ---
    subgraph B1 [PHASE 1: Sample Construction]
        direction TB
        Archive[("TESS MAST Archive <br> (SPOC Products)")]:::input
        Filters["Apply Dwarf Filters: <br> 2500K ≤ Teff ≤ 4000K <br> log g ≥ 4.0"]
        Clean["Remove Giants/Subgiants <br> Prioritize by Brightness (Tmag)"]
        SampleCSV[/"Output: sector18_mdwarf_sample.csv"/]:::output

        Archive --> Filters
        Filters --> Clean
        Clean --> SampleCSV
    end

    OutputVal -.-> B1

    %% --- BLOCK 2: CORE PIPELINE ---
    subgraph B2 [PHASE 2: Harmonic-Aware Rotation Pipeline]
        direction TB
        %% Sub-block 2.1
        Preproc["Preprocessing: <br> NaN Removal, Median Norm, <br> NO Aggressive Detrending"]
        
        %% Sub-block 2.2
        LS["Lomb-Scargle (LS) <br> (0.5–15 days, FAP < 1%)"]
        ACF["Autocorrelation (ACF) <br> (Lag > 0.5 days)"]

        %% Sub-block 2.3 - The Logic Engine
        Logic{"Harmonic Decision Engine"}:::decision
        
        %% Logic Outcomes
        HarmonicCorrect["Apply Harmonic Correction <br> (Use ACF Period)"]
        FundCorrect["Apply Fundamental Correction <br> (Use ACF Period)"]
        RetainLS["Retain LS Period"]
        FlagLS["Flagged: LS Only"]

        %% Sub-block 2.4
        Diag["Diagnostic Validation: <br> Phase Folding @ P and P/2"]

        SampleCSV --> Preproc
        Preproc --> LS & ACF
        LS & ACF --> Logic

        Logic -- "P_ACF ≈ 2 * P_LS" --> HarmonicCorrect
        Logic -- "P_ACF ≈ 0.5 * P_LS" --> FundCorrect
        Logic -- "Agreement" --> RetainLS
        Logic -- "ACF Fail" --> FlagLS

        HarmonicCorrect & FundCorrect & RetainLS & FlagLS --> Diag
        
        FinalCat[/"Output: Final Rotation Catalog <br> Flags: Match, Corrected, Ambiguous"/]:::output
        Diag --> FinalCat
    end

    class B2 core

    %% --- BLOCK 3: STATISTICAL ANALYSIS ---
    subgraph B3 [PHASE 3: Statistical Analysis Layer]
        direction TB
        Split["Sample Splitting: <br> Single-Planet vs Multi-Planet"]
        Tests["Non-Parametric Tests: <br> Kolmogorov-Smirnov (K-S) <br> Anderson-Darling (A-D)"]
        Hypothesis[/"Output: Hypothesis Test Results <br> & Bias-Aware Interpretation"/]:::output

        FinalCat --> Split
        Split --> Tests
        Tests --> Hypothesis
    end