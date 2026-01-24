import lightkurve as lk
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from pathlib import Path

# ======================================================
# PROJECT ROOT & OUTPUT
# ======================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]

TIC_ID = "TIC 445493624"
SECTOR = 18

OUTDIR = (
    PROJECT_ROOT
    / "results"
    / "validation_single_star"
    / TIC_ID.replace(" ", "")
)
OUTDIR.mkdir(parents=True, exist_ok=True)

print(f"\n--- SINGLE-STAR VALIDATION: {TIC_ID} (Sector {SECTOR}) ---\n")
print(f"Saving plots to: {OUTDIR}")

# ======================================================
# DOWNLOAD & PREPROCESS
# ======================================================
lc_file = lk.search_lightcurvefile(
    TIC_ID,
    mission="TESS",
    sector=SECTOR,
    author="SPOC"
).download()

lc = lc_file.PDCSAP_FLUX
lc = lc.remove_nans().normalize()
lc_binned = lc.bin(time_bin_size=2/24)

# ======================================================
# LOMB–SCARGLE
# ======================================================
pg = lc_binned.to_periodogram(
    method="lombscargle",
    minimum_period=0.5,
    maximum_period=15
)
ls_period = pg.period_at_max_power.value
ls_power = pg.max_power.value

print(f"[LS] Period = {ls_period:.4f} d | Power = {ls_power:.5f}")

# ======================================================
# ACF
# ======================================================
flux = np.array(lc_binned.flux.value, dtype=float)
time = np.array(lc_binned.time.value, dtype=float)

if np.any(np.isnan(flux)):
    flux = np.nan_to_num(flux, nan=np.nanmedian(flux))

cadence = np.median(np.diff(time))

acf = np.correlate(flux - flux.mean(), flux - flux.mean(), mode="full")
acf = acf[len(acf)//2:]
acf /= np.max(acf)

lags = np.arange(len(acf)) * cadence
peaks, _ = find_peaks(acf, height=0.2, distance=10)
acf_period = lags[peaks[0]] if len(peaks) else np.nan

print(f"[ACF] Period = {acf_period:.4f} d")

# ======================================================
# PLOT 1: CONSISTENT WITH PHASE-2 VALIDATION
# ======================================================
fig, axes = plt.subplots(
    1, 2, figsize=(12, 5), constrained_layout=True
)

lc_binned.fold(ls_period).scatter(ax=axes[0], s=2, alpha=0.5)
axes[0].set_title(f"Folded at P = {ls_period:.3f} d")
axes[0].set_xlabel("Phase")
axes[0].set_ylabel("Normalized Flux")

lc_binned.fold(ls_period / 2).scatter(ax=axes[1], s=2, alpha=0.5, color="red")
axes[1].set_title(f"Folded at P/2 = {ls_period/2:.3f} d")
axes[1].set_xlabel("Phase")

plt.savefig(OUTDIR / "folded_P_and_P2.png", dpi=200)
plt.close()

# ======================================================
# PLOT 2: LIGHT CURVE + PERIODOGRAM (DIAGNOSTIC)
# ======================================================
fig, axes = plt.subplots(
    2, 1, figsize=(10, 8), constrained_layout=True
)

lc_binned.scatter(ax=axes[0], s=2)
axes[0].set_title("Normalized PDCSAP Light Curve")
axes[0].set_ylabel("Flux")

pg.plot(ax=axes[1])
axes[1].axvline(ls_period, color="red", ls="--", label="LS peak")
axes[1].legend()
axes[1].set_title("Lomb–Scargle Periodogram")

plt.savefig(OUTDIR / "lc_and_periodogram.png", dpi=200)
plt.close()

# ======================================================
# PLOT 3: HALF-PERIOD DIAGNOSTIC (BINNED, MANUAL)
# ======================================================
fig, ax = plt.subplots(figsize=(8, 4), constrained_layout=True)

fold_half = lc_binned.fold(ls_period / 2)

phase = fold_half.phase.value
flux  = np.array(fold_half.flux.value, dtype=float)

# Manual phase binning (robust against masked-array issues)
bins = np.linspace(-0.5, 0.5, 51)
digitized = np.digitize(phase, bins)
binned_flux = [np.nanmean(flux[digitized == i]) for i in range(1, len(bins))]
bin_centers = 0.5 * (bins[:-1] + bins[1:])

ax.scatter(phase, flux, s=3, alpha=0.4, label="Data")
ax.plot(bin_centers, binned_flux, color="red", lw=2, label="Binned mean")

ax.set_title(f"Half-period diagnostic (P/2 = {ls_period/2:.3f} d)")
ax.set_xlabel("Phase")
ax.set_ylabel("Normalized Flux")
ax.legend()

plt.savefig(OUTDIR / "half_period_diagnostic.png", dpi=200)
plt.close()
