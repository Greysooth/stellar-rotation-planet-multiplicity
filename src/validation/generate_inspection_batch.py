import pandas as pd
import lightkurve as lk
import matplotlib.pyplot as plt
import os
from pathlib import Path

# =========================================================
# CONFIGURATION (MATCHES YOUR REPO)
# =========================================================
# --------------------------------------------------
# PATH SETUP (ROBUST TO RUN LOCATION)
# --------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "phase2_rotation_results_pilot.csv"
OUTPUT_DIR = (
    PROJECT_ROOT
    / "results"
    / "phase2_plots"
    / "pilot_validation"
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SECTOR = 18
N_MATCH_SAMPLE = 15

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("\n--- GENERATING PILOT INSPECTION BATCH ---\n")

# =========================================================
# LOAD RESULTS TABLE
# =========================================================
df = pd.read_csv(INPUT_CSV)

# =========================================================
# COLUMN NORMALIZATION (CANONICAL SCHEMA)
# =========================================================
rename_map = {}

# TIC ID
if "ID" in df.columns:
    rename_map["ID"] = "TIC_ID"

# Period column
if "Final_Period" in df.columns:
    rename_map["Final_Period"] = "Period"
elif "Pipeline_Period_days" in df.columns:
    rename_map["Pipeline_Period_days"] = "Period"

# Flag column
if "Pipeline_Flag" in df.columns:
    rename_map["Pipeline_Flag"] = "Flag"

df = df.rename(columns=rename_map)

required = {"TIC_ID", "Period", "Flag"}
missing = required - set(df.columns)
if missing:
    raise RuntimeError(f"CSV missing required columns: {missing}")

# =========================================================
# SELECT STARS TO INSPECT
# =========================================================
harmonic = df[df["Flag"].str.contains("Harmonic|Ambiguous", case=False, na=False)]
matches = df[df["Flag"] == "Match"]

matches_sample = matches.sample(
    n=min(len(matches), N_MATCH_SAMPLE),
    random_state=42
)

targets = pd.concat([harmonic, matches_sample]).drop_duplicates("TIC_ID")

print(f"Total inspection targets: {len(targets)}")
print(f"  Harmonic / Ambiguous : {len(harmonic)}")
print(f"  Match (control)      : {len(matches_sample)}\n")

# =========================================================
# PLOT GENERATION
# =========================================================
def make_validation_plot(tic_id, period, flag):
    print(f"Plotting TIC {tic_id} | P={period:.3f} d | {flag}")

    try:
        lc = lk.search_lightcurve(
            f"TIC {tic_id}",
            sector=SECTOR,
            author="SPOC"
        ).download()

        if lc is None:
            print("  -> No data found")
            return

        lc = lc.normalize().remove_nans()

        fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
        fig.suptitle(
            f"TIC {tic_id} | Pipeline Period = {period:.3f} d | Flag: {flag}",
            fontsize=14
        )

        # Fold at P
        lc.fold(period).scatter(
            ax=axes[0], s=2, alpha=0.5, c="black"
        )
        axes[0].set_title("Folded at Pipeline Period (P)")
        axes[0].set_xlabel("Phase")
        axes[0].set_ylabel("Normalized Flux")

        # Fold at P/2
        lc.fold(period / 2).scatter(
            ax=axes[1], s=2, alpha=0.5, c="red"
        )
        axes[1].set_title("Folded at Harmonic (P/2)")
        axes[1].set_xlabel("Phase")

        outname = f"TIC{tic_id}_{flag}.png"
        plt.savefig(os.path.join(OUTPUT_DIR, outname), dpi=120)
        plt.close()

    except Exception as e:
        print(f"  -> ERROR: {e}")

# =========================================================
# RUN
# =========================================================
for _, row in targets.iterrows():
    make_validation_plot(
        tic_id=int(row["TIC_ID"]),
        period=float(row["Period"]),
        flag=row["Flag"]
    )

print("\n--- PILOT VALIDATION PLOTS GENERATED ---")
print(f"Saved to: {OUTPUT_DIR}")
