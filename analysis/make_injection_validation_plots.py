# analysis/make_injection_validation_plots.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ======================================================
# PATHS
# ======================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "injection_recovery_results.csv"
OUTDIR = PROJECT_ROOT / "results" / "injection_validation"
OUTDIR.mkdir(parents=True, exist_ok=True)

print(f"Reading: {INPUT_CSV}")
print(f"Saving figures to: {OUTDIR}")

# ======================================================
# LOAD & PREP
# ======================================================
df = pd.read_csv(INPUT_CSV)

# Merge subharmonic into harmonic
df["Flag"] = df["Flag"].replace({"Subharmonic_Corrected": "Harmonic_Corrected"})

inj = df[df["Mode"] == "injected"].copy()

# ======================================================
# COMPOSITE FIGURE 1:
# Recovery vs Period  |  Harmonic Confusion vs Period
# ======================================================
recovery_by_period = (
    inj.groupby("P_true")["Recovered"]
    .mean()
    .reset_index(name="RecoveryRate")
)

harmonic_by_period = (
    inj.groupby("P_true")["Harmonic_FP"]
    .mean()
    .reset_index(name="HarmonicRate")
)

fig, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)

axes[0].plot(
    recovery_by_period["P_true"],
    recovery_by_period["RecoveryRate"],
    marker="o",
)
axes[0].set_xlabel("Injected Period (days)")
axes[0].set_ylabel("Recovery Fraction")
axes[0].set_title("Recovery vs Period")
axes[0].set_ylim(0, 1)

axes[1].plot(
    harmonic_by_period["P_true"],
    harmonic_by_period["HarmonicRate"],
    marker="o",
)
axes[1].set_xlabel("Injected Period (days)")
axes[1].set_ylabel("Harmonic Confusion Fraction")
axes[1].set_title("Harmonic Confusion vs Period")
axes[1].set_ylim(0, 1)

plt.savefig(OUTDIR / "fig_injection_performance.png", dpi=300)
plt.close()

# ======================================================
# FIGURE 2:
# Outcome by Diagnostic Flag (confusion-style matrix)
# ======================================================
inj_cm = inj.copy()
inj_cm["Outcome"] = np.where(inj_cm["Recovered"], "Recovered", "NotRecovered")

conf = pd.crosstab(inj_cm["Flag"], inj_cm["Outcome"], normalize="index")

plt.figure(figsize=(5, 4))
im = plt.imshow(conf.values)
plt.xticks(range(len(conf.columns)), conf.columns)
plt.yticks(range(len(conf.index)), conf.index)
plt.xlabel("Outcome")
plt.ylabel("Flag")
plt.title("Outcome by Diagnostic Flag")
plt.colorbar(im, fraction=0.046, pad=0.04)

plt.tight_layout()
plt.savefig(OUTDIR / "fig_diagnostic_meaning.png", dpi=300)
plt.close()

# ======================================================
# FIGURE 3:
# Outcome fractions vs injected period (stacked bars)
# ======================================================

flag_frac = (
    inj.groupby(["P_true", "Flag"])
       .size()
       .unstack(fill_value=0)
)

# Normalize to get fractions (0 to 1)
flag_frac = flag_frac.div(flag_frac.sum(axis=1), axis=0)

# Ensure consistent column order and existence
expected_cols = ["Match", "Harmonic_Corrected", "LS_only"]
for col in expected_cols:
    if col not in flag_frac.columns:
        flag_frac[col] = 0.0

flag_frac = flag_frac[expected_cols].sort_index()

plt.figure(figsize=(10, 5))

bottom = np.zeros(len(flag_frac))
x_pos = np.arange(len(flag_frac))
x_labels = [f"{val:.1f}" for val in flag_frac.index]

for label in flag_frac.columns:
    vals = flag_frac[label].values
    plt.bar(x_pos, vals, bottom=bottom, label=label, width=0.8)
    bottom += vals

plt.xticks(x_pos, x_labels, rotation=45)
plt.xlabel("Injected Period (days)")
plt.ylabel("Fraction of Outcomes")
plt.title("Diagnostic Outcomes vs Injected Period")
plt.ylim(0, 1)

plt.legend(title="Flag", bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0)
plt.tight_layout()
plt.savefig(OUTDIR / "outcome_fractions_vs_period.png", dpi=300)
plt.close()

print("All validation figures generated.")
