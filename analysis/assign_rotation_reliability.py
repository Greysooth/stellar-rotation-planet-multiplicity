# analysis/assign_rotation_reliability.py

import pandas as pd
import numpy as np
from pathlib import Path

# ======================================================
# PATHS
# ======================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "sector18_rotation_results_full.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "sector18_rotation_with_reliability.csv"

print("\n--- ASSIGNING ROTATION RELIABILITY TIERS ---")
print(f"Input catalog : {INPUT_CSV}")
print(f"Output catalog: {OUTPUT_CSV}\n")

# ======================================================
# LOAD DATA
# ======================================================
df = pd.read_csv(INPUT_CSV)

required_cols = {"Flag", "LS_Power", "Variability"}
missing = required_cols - set(df.columns)
if missing:
    raise RuntimeError(f"Missing required columns: {missing}")

# ======================================================
# COMPUTE THRESHOLDS (distribution-based)
# ======================================================
ls_power_median = df["LS_Power"].median()
ls_power_p75 = df["LS_Power"].quantile(0.75)
variability_median = df["Variability"].median()

print("Thresholds used:")
print(f"  LS_Power median : {ls_power_median:.4f}")
print(f"  LS_Power 75%    : {ls_power_p75:.4f}")
print(f"  Variability med : {variability_median:.4e}\n")

# ======================================================
# RELIABILITY ASSIGNMENT FUNCTION
# ======================================================
# ======================================================
# UPDATED RELIABILITY LOGIC
# ======================================================

def compute_reliability_score(row, ls_power_thresh):
    R = 0
    # (1) Frequency-domain strength
    if row["LS_Power"] >= ls_power_thresh:
        R += 1
    # (2) Time-domain coherence
    if not np.isnan(row["ACF_Period"]):
        R += 1
    # (3) Diagnostic agreement
    if not np.isnan(row["ACF_Period"]):
        frac_diff = abs(row["LS_Period"] - row["ACF_Period"]) / row["LS_Period"]
        if frac_diff <= 0.10:
            R += 1
    return R

def assign_tier_from_R(R):
    mapping = {
        3: "High",
        2: "Medium",
        1: "Low",
        0: "Very_Low"
    }
    return mapping.get(R, "Very_Low")

# ======================================================
# REVISED APPLY SEQUENCE
# ======================================================

# 1. Define the threshold globally to fix the previous NameError
ls_power_thresh = ls_power_p75

# 2. Compute the raw integer score (0-3)
df["R_score"] = df.apply(
    lambda r: compute_reliability_score(r, ls_power_thresh),
    axis=1
)

# 3. Derive the human-readable tier from the score
df["rotation_reliability"] = df["R_score"].map(assign_tier_from_R)
# ======================================================
# SAVE
# ======================================================
df.to_csv(OUTPUT_CSV, index=False)

# ======================================================
# SUMMARY
# ======================================================
print("--- RELIABILITY SUMMARY ---")
print(df["rotation_reliability"].value_counts())
print("\nSaved catalog with reliability tiers.")
