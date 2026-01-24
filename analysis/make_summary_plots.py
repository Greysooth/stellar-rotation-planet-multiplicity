from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ======================================================
# PATH SETUP
# ======================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "sector18_rotation_results_full.csv"
FIG_DIR = PROJECT_ROOT / "results" / "summary_plots"
FIG_DIR.mkdir(parents=True, exist_ok=True)

print(f"Reading data from : {INPUT_CSV}")
print(f"Saving figures to : {FIG_DIR}")

# ======================================================
# LOAD DATA
# ======================================================
df = pd.read_csv(INPUT_CSV)

# Basic sanity check
required_cols = {"Final_Period", "Flag"}
missing = required_cols - set(df.columns)
if missing:
    raise RuntimeError(f"Missing required columns: {missing}")

# ======================================================
# 1. FLAG FRACTION PLOT (CONSOLIDATED)
# ======================================================
# Group any subharmonic-labeled data into the main Harmonic_Corrected category
df["Flag"] = df["Flag"].replace("Subharmonic_Corrected", "Harmonic_Corrected")

# Explicitly define the three standard categories
target_flags = ["Match", "Harmonic_Corrected", "LS_only"]
flag_frac = df["Flag"].value_counts(normalize=True).reindex(target_flags).fillna(0)
plt.figure(figsize=(6, 4))
bars = plt.bar(flag_frac.index, flag_frac.values)
plt.xlabel("Rotation-period classification")
plt.ylabel("Fraction of stars")
plt.title("Rotation Period Classification Fractions")
plt.ylim(0, 0.7)
plt.xticks(rotation=0)

for bar in bars:
    h = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        h + 0.02,
        f"{h:.2f}",
        ha="center",
        va="bottom",
        fontsize=9
    )

plt.tight_layout()
plt.savefig(FIG_DIR / "flag_fractions.png", dpi=300)
plt.close()

# ======================================================
# 2. PERIOD DISTRIBUTION BY FLAG (SHAPE COMPARISON)
# ======================================================
bins = np.linspace(0.5, 15, 30)

plt.figure(figsize=(7, 4))

for flag, color in zip(
    ["Match", "Harmonic_Corrected", "LS_only"],
    ["tab:blue", "tab:orange", "tab:green"]
):
    subset = df[df["Flag"] == flag]["Final_Period"].dropna()
    plt.hist(
        subset,
        bins=bins,
        density=True,
        histtype="step",
        linewidth=2,
        label=flag,
        color=color
    )

plt.xlabel("Rotation period (days)")
plt.ylabel("Probability density")
plt.title("Rotation Period Distributions by Classification Flag")
plt.legend()
plt.xlim(0.5, 15)

plt.tight_layout()
plt.savefig(FIG_DIR / "period_by_flag.png", dpi=300)
plt.close()

# ======================================================
# 3. OVERALL PERIOD HISTOGRAM
# ======================================================
plt.figure(figsize=(6, 4))

plt.hist(
    df["Final_Period"].dropna(),
    bins=np.linspace(0.5, 15, 25),
    edgecolor="black",
    linewidth=0.8
)

plt.xlabel("Rotation period (days)")
plt.ylabel("Number of stars")
plt.title("Distribution of Stellar Rotation Periods")
plt.xlim(0.5, 15)

plt.tight_layout()
plt.savefig(FIG_DIR / "period_histogram.png", dpi=300)
plt.close()

print("All summary plots generated successfully.")
