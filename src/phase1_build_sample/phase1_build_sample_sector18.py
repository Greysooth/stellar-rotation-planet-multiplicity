import os
import re
import pandas as pd
from astroquery.mast import Observations, Catalogs
from tqdm import tqdm

# ============================================================
# CONFIG
# ============================================================
SECTOR = 18
CACHE_FILE = "tic_sector18_cache.csv"
OUTPUT_FILE = "sector18_mdwarf_sample.csv"

TEFF_MIN = 2500
TEFF_MAX = 4000
LOGG_MIN = 4.0

print("\n--- PHASE 1: BUILDING M-DWARF SAMPLE (CACHED, FIXED) ---\n")

# ============================================================
# STEP 1: LOAD CACHE IF EXISTS
# ============================================================
if os.path.exists(CACHE_FILE):
    print("Cache found. Loading TIC catalog cache...")
    tic_df = pd.read_csv(CACHE_FILE)

else:
    print("No cache found. Querying MAST Observations (one-time)...")

    # --------------------------------------------------------
    # STEP 1A: QUERY SPOC TIME-SERIES PRODUCTS
    # --------------------------------------------------------
    obs = Observations.query_criteria(
        obs_collection="TESS",
        dataproduct_type="timeseries",
        provenance_name="SPOC",
        sequence_number=SECTOR
    )

    print(f"Retrieved {len(obs)} observation entries.")

    # --------------------------------------------------------
    # STEP 1B: EXTRACT TIC IDs FROM obs_id (CORRECT METHOD)
    # --------------------------------------------------------
    tic_ids = set()
    tic_pattern = re.compile(r"-([0-9]{16})-")

    for oid in obs["obs_id"]:
        if isinstance(oid, str):
            match = tic_pattern.search(oid)
            if match:
                tic_ids.add(int(match.group(1)))

    tic_ids = sorted(tic_ids)
    print(f"Unique TIC IDs extracted: {len(tic_ids)}")

    if len(tic_ids) == 0:
        raise RuntimeError("No TIC IDs extracted — stopping.")

    # --------------------------------------------------------
    # STEP 1C: QUERY TIC CATALOG (CHUNKED)
    # --------------------------------------------------------
    records = []
    CHUNK = 1000

    for i in tqdm(range(0, len(tic_ids), CHUNK), desc="Querying TIC catalog"):
        chunk = tic_ids[i:i + CHUNK]
        try:
            r = Catalogs.query_criteria(
                catalog="Tic",
                ID=chunk
            )
            records.append(r.to_pandas())
        except Exception as e:
            print(f"Chunk {i} failed: {e}")

    tic_df = pd.concat(records, ignore_index=True)

    # Cache
    tic_df.to_csv(CACHE_FILE, index=False)
    print(f"TIC catalog cache saved to {CACHE_FILE}")

# ============================================================
# STEP 2: APPLY STELLAR FILTERS
# ============================================================
print("\nApplying late-type dwarf filters...")

required = {"ID", "Teff", "logg"}
missing = required - set(tic_df.columns)
if missing:
    raise RuntimeError(f"Missing required TIC columns: {missing}")

mdwarfs = tic_df[
    (tic_df["Teff"] >= TEFF_MIN) &
    (tic_df["Teff"] <= TEFF_MAX) &
    (tic_df["logg"] >= LOGG_MIN)
].copy()

print(f"Late-type dwarf candidates: {len(mdwarfs)}")

# ============================================================
# STEP 3: OPTIONAL SORTING
# ============================================================
if "Tmag" in mdwarfs.columns:
    mdwarfs = mdwarfs.sort_values("Tmag")
    print("Sorted by Tmag (brightest first).")

# ============================================================
# STEP 4: SAVE FINAL SAMPLE
# ============================================================
keep_cols = [c for c in ["ID", "Teff", "logg", "Tmag"] if c in mdwarfs.columns]
final_sample = mdwarfs[keep_cols]

final_sample.to_csv(OUTPUT_FILE, index=False)

print("\n--- PHASE 1 COMPLETE ---")
print(f"Final sample size : {len(final_sample)}")
print(f"Sample saved to   : {OUTPUT_FILE}")
print(">>> THIS FILE DEFINES THE STUDY SAMPLE <<<")
