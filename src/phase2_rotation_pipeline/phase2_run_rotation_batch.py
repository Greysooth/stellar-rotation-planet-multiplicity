import lightkurve as lk
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from pathlib import Path

# ======================================================
# PROJECT ROOT
# ======================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ======================================================
# CONFIGURATION
# ======================================================
SECTOR = 18

INPUT_SAMPLE = PROJECT_ROOT / "data" / "processed" / "sector18_mdwarf_sample.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "phase2_rotation_results_pilot.csv"

MAX_STARS = 100   # Pilot batch size

print("\n--- PHASE 2: ROTATION PERIOD ANALYSIS (PILOT) ---")
print(f"Sector            : {SECTOR}")
print(f"Input sample      : {INPUT_SAMPLE}")
print(f"Output CSV        : {OUTPUT_CSV}")
print(f"Max stars         : {MAX_STARS}\n")

# ======================================================
# LOAD SAMPLE
# ======================================================
sample = pd.read_csv(INPUT_SAMPLE)

possible_tic_cols = ["TIC_ID", "ticid", "TIC", "ID"]
tic_col = next((c for c in possible_tic_cols if c in sample.columns), None)

if tic_col is None:
    raise RuntimeError("No TIC ID column found in input sample.")

print(f"Using TIC column: {tic_col}")

# ======================================================
# HELPER: Harmonic-aware decision
# ======================================================
def choose_rotation_period(P_ls, P_acf):
    if np.isnan(P_acf):
        return P_ls, "LS_only"

    ratio = P_acf / P_ls

    if 1.8 < ratio < 2.2:
        return P_acf, "Harmonic_Corrected"

    if 0.45 < ratio < 0.55:
        return P_acf, "Subharmonic_Corrected"

    return P_ls, "Match"

# ======================================================
# MAIN LOOP
# ======================================================
results = []

for i, row in sample.iterrows():
    if i >= MAX_STARS:
        break

    tic_id = int(row[tic_col])

    try:
        print(f"[{i+1}/{MAX_STARS}] TIC {tic_id}")

        search = lk.search_lightcurve(
            f"TIC {tic_id}",
            mission="TESS",
            sector=SECTOR,
            author="SPOC"
        )

        if len(search) == 0:
            print("  -> No SPOC data")
            continue

        lc = search[0].download()
        lc = lc.remove_nans().normalize().bin(time_bin_size=2/24)

        # -----------------------------
        # Variability (diagnostic only)
        # -----------------------------
        variability = np.nanstd(lc.flux.value)

        # -----------------------------
        # Lomb–Scargle
        # -----------------------------
        ls = lc.to_periodogram(
            method="lombscargle",
            minimum_period=0.5,
            maximum_period=15
        )

        ls_period = ls.period_at_max_power.value
        ls_power = ls.max_power.value

        # -----------------------------
        # ACF
        # -----------------------------
        flux = np.nan_to_num(
            lc.flux.value,
            nan=np.nanmedian(lc.flux.value)
        )
        time = lc.time.value
        cadence = np.median(np.diff(time))

        acf = np.correlate(
            flux - flux.mean(),
            flux - flux.mean(),
            mode="full"
        )
        acf = acf[len(acf)//2:]
        acf /= np.max(acf)

        lags = np.arange(len(acf)) * cadence
        peaks, _ = find_peaks(acf, height=0.2, distance=10)
        valid_peaks = [lags[p] for p in peaks if lags[p] > 0.5]

        acf_period = valid_peaks[0] if valid_peaks else np.nan

        # -----------------------------
        # Final decision
        # -----------------------------
        final_period, flag = choose_rotation_period(ls_period, acf_period)

        results.append({
            "TIC_ID": tic_id,
            "Teff": float(row["Teff"]) if "Teff" in row and not pd.isna(row["Teff"]) else np.nan,
            "logg": float(row["logg"]) if "logg" in row and not pd.isna(row["logg"]) else np.nan,
            "Tmag": float(row["Tmag"]) if "Tmag" in row and not pd.isna(row["Tmag"]) else np.nan,
            "LS_Period": round(ls_period, 4),
            "LS_Power": round(ls_power, 6),
            "ACF_Period": round(acf_period, 4) if not np.isnan(acf_period) else np.nan,
            "Final_Period": round(final_period, 4),
            "Flag": flag,
            "Variability": round(variability, 6)
        })

    except Exception as e:
        print(f"  ERROR: {e}")

# ======================================================
# EXPORT RESULTS
# ======================================================
df = pd.DataFrame(results)
df.to_csv(OUTPUT_CSV, index=False)

print("\n--- PHASE 2 PILOT COMPLETE ---")
print(f"Stars processed : {len(df)}")
print(f"Results saved   : {OUTPUT_CSV}")
print("\nFlag summary:")
print(df["Flag"].value_counts())
