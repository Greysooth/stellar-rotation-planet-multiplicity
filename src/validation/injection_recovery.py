# validation/injection_recovery.py

import numpy as np
import pandas as pd
import lightkurve as lk
from scipy.signal import find_peaks
from pathlib import Path
from tqdm import tqdm

# ======================================================
# PATHS
# ======================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_SAMPLE = PROJECT_ROOT / "data" / "processed" / "sector18_mdwarf_sample.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "injection_recovery_results.csv"

SECTOR = 18

# ======================================================
# EXPERIMENT GRID
# ======================================================
PERIOD_GRID = [0.5, 1, 2, 3, 5, 7, 10, 12, 14]  # days
AMPLITUDES = [0.002, 0.005, 0.01, 0.02]
N_BASE_STARS = 100
RECOVERY_TOL = 0.10  # 10% relative tolerance

# ======================================================
# HARMONIC-AWARE DECISION (same as pipeline)
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
# ACF + LS RUNNER (faithful to Phase 2)
# ======================================================
def run_pipeline_on_flux(time, flux):
    # Lomb–Scargle
    lc = lk.LightCurve(time=time, flux=flux)
    lc = lc.remove_nans().normalize()
    lc_binned = lc.bin(time_bin_size=2/24)

    ls = lc_binned.to_periodogram(
        method="lombscargle",
        minimum_period=0.5,
        maximum_period=15
    )

    P_ls = float(ls.period_at_max_power.value)
    LS_power = float(ls.max_power.value)

    # ACF
    f = np.array(lc_binned.flux.value, dtype=float)
    t = np.array(lc_binned.time.value, dtype=float)

    if np.any(np.isnan(f)):
        f = np.nan_to_num(f, nan=np.nanmedian(f))

    cadence = np.median(np.diff(t))
    acf = np.correlate(f - np.mean(f), f - np.mean(f), mode="full")
    acf = acf[len(acf)//2:]
    acf /= np.max(acf)

    lags = np.arange(len(acf)) * cadence
    peaks, _ = find_peaks(acf, height=0.2, distance=10)
    valid = [lags[p] for p in peaks if lags[p] > 0.5]

    P_acf = valid[0] if len(valid) > 0 else np.nan

    P_final, flag = choose_rotation_period(P_ls, P_acf)

    return P_ls, P_acf, P_final, flag, LS_power

# ======================================================
# MAIN
# ======================================================
print("=== Injection–Recovery Experiment ===")
print(f"Input sample : {INPUT_SAMPLE}")
print(f"Output CSV   : {OUTPUT_CSV}\n")

sample = pd.read_csv(INPUT_SAMPLE)

# Detect TIC column
tic_col = next(c for c in ["TIC_ID", "ticid", "TIC", "ID"] if c in sample.columns)

# Stratified-ish random subset
base_sample = sample.sample(
    n=min(N_BASE_STARS, len(sample)),
    random_state=42
).reset_index(drop=True)

results = []

for _, row in tqdm(base_sample.iterrows(), total=len(base_sample)):
    tic_id = int(row[tic_col])

    try:
        search = lk.search_lightcurve(
            f"TIC {tic_id}",
            mission="TESS",
            sector=SECTOR,
            author="SPOC"
        )

        if len(search) == 0:
            continue

        lc = search[0].download()
        lc = lc.remove_nans().normalize()

        time = lc.time.value
        base_flux = lc.flux.value

        # ---- NULL RUN (false positives) ----
        P_ls, P_acf, P_final, flag, LS_power = run_pipeline_on_flux(time, base_flux)

        results.append({
            "TIC_ID": tic_id,
            "P_true": np.nan,
            "A": 0.0,
            "P_LS": P_ls,
            "P_ACF": P_acf,
            "P_final": P_final,
            "Flag": flag,
            "Recovered": False,
            "Harmonic_FP": False,
            "LS_Power": LS_power,
            "Mode": "null"
        })

        # ---- INJECTION RUNS ----
        for P_true in PERIOD_GRID:
            for A in AMPLITUDES:
                phi = np.random.uniform(0, 2*np.pi)
                inj = 1.0 + A * np.sin(2*np.pi*time/P_true + phi)
                flux_new = base_flux * inj

                P_ls, P_acf, P_final, flag, LS_power = run_pipeline_on_flux(time, flux_new)

                recovered = (
                    abs(P_final - P_true) / P_true <= RECOVERY_TOL
                )

                harmonic_fp = (
                    abs(P_final - 0.5*P_true) / (0.5*P_true) <= RECOVERY_TOL
                    or abs(P_final - 2.0*P_true) / (2.0*P_true) <= RECOVERY_TOL
                )

                results.append({
                    "TIC_ID": tic_id,
                    "P_true": P_true,
                    "A": A,
                    "P_LS": P_ls,
                    "P_ACF": P_acf,
                    "P_final": P_final,
                    "Flag": flag,
                    "Recovered": recovered,
                    "Harmonic_FP": harmonic_fp,
                    "LS_Power": LS_power,
                    "Mode": "injected"
                })

    except Exception as e:
        print(f"TIC {tic_id} failed: {e}")

df = pd.DataFrame(results)
df.to_csv(OUTPUT_CSV, index=False)

print("\n=== Injection–Recovery Complete ===")
print(f"Trials written: {len(df)}")
print(f"Saved to: {OUTPUT_CSV}")
