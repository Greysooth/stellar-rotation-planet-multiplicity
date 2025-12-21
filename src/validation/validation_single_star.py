import lightkurve as lk
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# -----------------------------
# VALIDATION: Minimalist SPOC run
# -----------------------------
TIC_ID = "TIC 445493624"
SECTOR = 18

print(f"\n--- MINIMALIST VALIDATION RUN FOR {TIC_ID} (SECTOR {SECTOR}) ---\n")

# --- DOWNLOAD (direct, avoids discovery portal issues) ---
lc_file = lk.search_lightcurvefile(TIC_ID, mission="TESS", sector=SECTOR, author="SPOC").download()
# Use PDCSAP flux (NASA corrected)
lc = lc_file.PDCSAP_FLUX

print(f"Downloaded: Author={lc.author}, Sector={getattr(lc, 'sector', SECTOR)}")

# --- PREPROCESSING (GENTLE) ---
# Remove NaNs and normalize only. DO NOT flatten here.
lc_clean = lc.remove_nans().normalize()

# Optional small binning to reduce scatter (keeps signal)
lc_binned = lc_clean.bin(time_bin_size=2/24)  # 2 hours

print("Minimal preprocessing done (flatten skipped).")

# --- LOMB-SCARGLE PERIODOGRAM ---
periodogram = lc_binned.to_periodogram(method="lombscargle", minimum_period=0.5, maximum_period=15)
ls_period = periodogram.period_at_max_power.value
ls_power = periodogram.max_power.value

print("\n[Lomb-Scargle]")
print(f"  Detected period : {ls_period:.4f} days")
print(f"  Peak power      : {ls_power:.6f}")
print("  (Literature ref: ~3.638 days)")

# --- ACF (on un-flattened, binned data) ---
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
if len(valid_peaks) > 0:
    acf_period = valid_peaks[0]
    print(f"[ACF] Estimated period: {acf_period:.4f} days")
else:
    acf_period = np.nan
    print("[ACF] No clear ACF peak found.")

# --- PLOTS: periodogram + standard fold ---
fig, axes = plt.subplots(3, 1, figsize=(10, 15))

lc_binned.scatter(ax=axes[0], s=2)
axes[0].set_title(f"TESS Sector {SECTOR} — Normalized PDCSAP (no flatten)")
axes[0].set_ylabel("Normalized flux")

periodogram.plot(ax=axes[1])
axes[1].axvline(3.638, color="green", linestyle="--", label="Literature 3.638 d")
axes[1].legend()
axes[1].set_title(f"Periodogram (peak: {ls_period:.4f} d)")

folded = lc_binned.fold(period=ls_period)
folded.scatter(ax=axes[2], s=2, alpha=0.6)
axes[2].set_title(f"Phase Folded at {ls_period:.4f} days")

plt.tight_layout()
plt.savefig(f"Validation_minimal_Sector{SECTOR}_PDCSAP.png", dpi=200)
plt.show()

# --- HARMONIC CHECK: fold at half-period ---
half_period = ls_period / 2.0
print(f"\n[HARMONIC CHECK] Half period = {half_period:.4f} days (folding to test double-dip)")

folded_half = lc_binned.fold(period=half_period)

fig, ax = plt.subplots(figsize=(9,5))
folded_half.scatter(ax=ax, s=4, alpha=0.5, label="Data")
binned_fold = folded_half.bin(bins=50)
binned_fold.plot(ax=ax, lw=2, color="red", label="Binned mean")
ax.set_title(f"Phase Folded at {half_period:.4f} d (Half-Period Diagnostic)")
ax.set_xlabel("Phase")
ax.set_ylabel("Normalized flux")
ax.legend()
plt.tight_layout()
plt.savefig(f"Validation_halffold_Sector{SECTOR}_PDCSAP.png", dpi=200)
plt.show()

print("\nDone. Saved plots:")
print(f" - Validation_minimal_Sector{SECTOR}_PDCSAP.png")
print(f" - Validation_halffold_Sector{SECTOR}_PDCSAP.png")
