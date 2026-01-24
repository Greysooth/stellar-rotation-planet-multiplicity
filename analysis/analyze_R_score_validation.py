import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT = PROJECT_ROOT / "data" / "processed" / "injection_recovery_results.csv"

df = pd.read_csv(INPUT)

# Merge subharmonic into harmonic
df["Flag"] = df["Flag"].replace({"Subharmonic_Corrected": "Harmonic_Corrected"})

inj = df[df["Mode"] == "injected"].copy()

# Recompute R_score using the same logic
ls_power_thresh = inj["LS_Power"].quantile(0.75)

def compute_R(row):
    R = 0
    if row["LS_Power"] >= ls_power_thresh:
        R += 1
    if not np.isnan(row["P_ACF"]):
        R += 1
    if not np.isnan(row["P_ACF"]):
        frac = abs(row["P_LS"] - row["P_ACF"]) / row["P_LS"]
        if frac <= 0.10:
            R += 1
    return R

inj["R_score"] = inj.apply(compute_R, axis=1)

# Calibration table
calib = inj.groupby("R_score")["Recovered"].mean().reset_index()
print("\nRecovery fraction by R_score:")
print(calib.to_string(index=False))

OUTDIR = PROJECT_ROOT / "results" / "injection_validation"
OUTDIR.mkdir(parents=True, exist_ok=True)

out_csv = OUTDIR / "R_score_calibration.csv"
calib.to_csv(out_csv, index=False)

print(f"\nSaved R-score calibration to: {out_csv}")