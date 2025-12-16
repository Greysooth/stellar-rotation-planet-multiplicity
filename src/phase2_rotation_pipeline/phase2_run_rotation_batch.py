import lightkurve as lk
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import os

# ======================================================
# CONFIGURATION
# ======================================================
SECTOR = 18
INPUT_SAMPLE = "sector18_mdwarf_sample.csv"   # From Phase 1
OUTPUT_FILE = "phase2_rotation_results.csv"
PLOT_DIR = "phase2_plots"

MAX_STARS = 100              # Process first 100, select 50 later
VARIABILITY_CUT = 0.0015     # Save plots only if variability > this

os.makedirs(PLOT_DIR, exist_ok=True)

print("\n--- PHASE 2: ROTATION PERIOD ANALYSIS ---")
print(f"Sector            : {SECTOR}")
print(f"Max stars         : {MAX_STARS}")
print(f"Variability cut   : {VARIABILITY_CUT}\n")

# ======================================================
# LOAD SAMPLE
# ======================================================
sample = pd.read_csv(INPUT_SAMPLE)

# ---- Detect TIC column automatically ----
possible_tic_cols = ["TIC_ID", "ticid", "TIC", "ID"]
tic_col = None
for col in possible_tic_cols:
    if col in sample.columns:
        tic_col = col
        break

if tic_col is None:
    raise RuntimeError(f"No TIC ID column found. Columns: {sample.columns.tolist()}")

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
processed = 0

for _, row in sample.iterrows():
    if processed >= MAX_STARS:
        break

    tic_id = int(row[tic_col])

    try:
        print(f"[{processed+1}/{MAX_STARS}] TIC {tic_id}")

        # --- DOWNLOAD ---
        search = lk.search_lightcurve(
            f"TIC {tic_id}",
            mission="TESS",
            sector=SECTOR,
            author="SPOC"
        )

        if len(search) == 0:
            print("  No SPOC data — skipping.")
            continue

        lc = search[0].download()

        # --- PREPROCESS ---
        lc = lc.remove_nans().normalize()
        lc_binned = lc.bin(time_bin_size=2/24)

        variability = np.nanstd(lc_binned.flux.value)

        # --- LOMB–SCARGLE ---
        ls = lc_binned.to_periodogram(
            method="lombscargle",
            minimum_period=0.5,
            maximum_period=15
        )

        ls_period = ls.period_at_max_power.value
        ls_power = ls.max_power.value

        # --- ACF ---
        flux = np.array(lc_binned.flux.value, dtype=float)
        time = np.array(lc_binned.time.value, dtype=float)

        if np.any(np.isnan(flux)):
            flux = np.nan_to_num(flux, nan=np.nanmedian(flux))

        cadence = np.median(np.diff(time))
        acf = np.correlate(flux - np.mean(flux), flux - np.mean(flux), mode="full")
        acf = acf[len(acf)//2:]
        acf /= np.max(acf)

        lags = np.arange(len(acf)) * cadence
        peaks, _ = find_peaks(acf, height=0.2, distance=10)
        valid_peaks = [lags[p] for p in peaks if lags[p] > 0.5]

        acf_period = valid_peaks[0] if len(valid_peaks) > 0 else np.nan

        # --- DECISION ---
        final_period, flag = choose_rotation_period(ls_period, acf_period)

        # --- SAVE RESULT ---
        results.append({
        "TIC_ID": int(tic_id),
        "Teff": float(row["Teff"]) if "Teff" in row and not pd.isna(row["Teff"]) else np.nan,
        "logg": float(row["logg"]) if "logg" in row and not pd.isna(row["logg"]) else np.nan,
        "Tmag": float(row["Tmag"]) if "Tmag" in row and not pd.isna(row["Tmag"]) else np.nan,
        "LS_Period": round(float(ls_period), 4),
        "LS_Power": round(float(ls_power), 6),
        "ACF_Period": round(float(acf_period), 4) if not np.isnan(acf_period) else np.nan,
        "Final_Period": round(float(final_period), 4),
        "Flag": flag,
        "Variability": round(float(variability), 6)
        })


        # --- SAVE PLOT (ONLY IF VARIABLE) ---
        if variability >= VARIABILITY_CUT:
            fig, ax = plt.subplots(figsize=(6, 4))
            folded = lc_binned.fold(period=final_period)
            folded.scatter(ax=ax, s=2, alpha=0.6)
            ax.set_title(f"TIC {tic_id} | P={final_period:.2f} d | {flag}")
            plt.tight_layout()
            plt.savefig(f"{PLOT_DIR}/TIC{tic_id}_fold.png", dpi=120)
            plt.close(fig)

        processed += 1

    except Exception as e:
        print(f"  ERROR: {e}")
        continue

# ======================================================
# EXPORT RESULTS
# ======================================================
df = pd.DataFrame(results)
df.to_csv(OUTPUT_FILE, index=False)

print("\n--- PHASE 2 COMPLETE ---")
print(f"Stars processed : {len(df)}")
print(f"Results saved   : {OUTPUT_FILE}")
print(f"Plots directory : {PLOT_DIR}/")
print("\nFlag summary:")
print(df["Flag"].value_counts())
