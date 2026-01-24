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
# 1) Recovery fraction vs period
# ======================================================
recovery_by_period = (
    inj.groupby("P_true")["Recovered"]
    .mean()
    .reset_index(name="RecoveryRate")
)

plt.figure()
plt.plot(recovery_by_period["P_true"], recovery_by_period["RecoveryRate"])
plt.xlabel("Injected Period (days)")
plt.ylabel("Recovery Fraction")
plt.title("Injection–Recovery: Recovery vs Period")
plt.ylim(0, 1)
plt.savefig(OUTDIR / "recovery_vs_period.png", dpi=200)
plt.close()

# ======================================================
# 2) Harmonic confusion vs period
# ======================================================
harmonic_by_period = (
    inj.groupby("P_true")["Harmonic_FP"]
    .mean()
    .reset_index(name="HarmonicRate")
)

plt.figure()
plt.plot(harmonic_by_period["P_true"], harmonic_by_period["HarmonicRate"])
plt.xlabel("Injected Period (days)")
plt.ylabel("Harmonic Confusion Fraction")
plt.title("Injection–Recovery: Harmonic Confusion vs Period")
plt.ylim(0, 1)
plt.savefig(OUTDIR / "harmonic_confusion_vs_period.png", dpi=200)
plt.close()

# ======================================================
# 3) Period distributions split by flag (publication-ready)
# ======================================================

# Use global, shared bins for all flags
bins = np.linspace(0, 15, 25)  # 0–15 days, 24 bins

for flag, sub in inj.groupby("Flag"):
    plt.figure(figsize=(6, 4))

    plt.hist(
        sub["P_final"],
        bins=bins,
        histtype="bar",
        edgecolor="black",
        linewidth=0.6,
        alpha=0.85,
    )

    plt.xlabel("Recovered Period (days)")
    plt.ylabel("Count")
    plt.title(f"Recovered Period Distribution — {flag}")
    plt.xlim(0, 15)

    fname = f"period_distribution_{flag}.png".replace(" ", "_")
    plt.tight_layout()
    plt.savefig(OUTDIR / fname, dpi=300)
    plt.close()
# ======================================================
# 4) Fraction of flags vs period bins
# ======================================================
bins = [0.5, 3, 6, 9, 12, 15]
inj_bins = inj.copy()
inj_bins["Pbin"] = pd.cut(inj_bins["P_true"], bins=bins, include_lowest=True)

for pbin in inj_bins["Pbin"].cat.categories:
    sub = inj_bins[inj_bins["Pbin"] == pbin]
    if len(sub) == 0:
        continue

    frac = sub["Flag"].value_counts(normalize=True)

    plt.figure()
    plt.bar(frac.index, frac.values)
    plt.xlabel("Flag")
    plt.ylabel("Fraction")
    plt.title(f"Flag Fractions for P in {pbin}")
    fname = f"flag_fraction_{str(pbin).replace(' ', '').replace(',', '_')}.png"
    plt.savefig(OUTDIR / fname, dpi=200)
    plt.close()

# ======================================================
# 5) Confusion-matrix style figure
# ======================================================
inj_cm = inj.copy()
inj_cm["Outcome"] = np.where(inj_cm["Recovered"], "Recovered", "NotRecovered")

conf = pd.crosstab(inj_cm["Flag"], inj_cm["Outcome"], normalize="index")

plt.figure()
plt.imshow(conf.values)
plt.xticks(range(len(conf.columns)), conf.columns)
plt.yticks(range(len(conf.index)), conf.index)
plt.xlabel("Outcome")
plt.ylabel("Flag")
plt.title("Outcome by Diagnostic Flag (Row-normalized)")
plt.colorbar()
plt.savefig(OUTDIR / "confusion_matrix_style.png", dpi=200)
plt.close()

print("All validation figures generated.")
