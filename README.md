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
