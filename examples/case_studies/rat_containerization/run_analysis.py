#!/usr/bin/env python3
"""Full rat containerization policy evaluation pipeline.

Orchestrates ten analysis steps using real NYC 311 Rodent complaint
data fetched from Socrata:

  01  Fetch Rodent complaints from NYC Open Data (2023--2024)
  02  Build a balanced community-district x month panel
  03  Descriptive analysis + factor pipeline
  04  Temporal decomposition, anomaly detection, changepoints
  05  Spatial analysis (Moran's I, LISA, Theil, equity gap)
  06  Synthetic control for a treated Manhattan district
  07  Staggered DiD + event study with pre-trend diagnostics
  08  Regression discontinuity at the mandate zone boundary
  09  Power analysis for the panel design
  10  Compile FINDINGS.md and JSON output
"""

from __future__ import annotations

import pickle
from importlib import import_module
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def main() -> None:
    """Run the full analysis pipeline."""
    print("=" * 64)
    print("  Rat Containerization Policy Evaluation")
    print("  (Real NYC 311 Rodent Complaint Data)")
    print("=" * 64)

    results: dict = {}

    # Step 1: Fetch data ───────────────────────────────────────────────
    cache_dir = DATA_DIR / "cache"
    csv_files = sorted(cache_dir.glob("*.csv")) if cache_dir.exists() else []
    if csv_files:
        print("\n-- Step 1: Data already cached, skipping fetch --\n")
        for p in csv_files:
            print(f"  {p.name}  ({p.stat().st_size / 1_048_576:.1f} MB)")
    else:
        print("\n-- Step 1: Fetching Rodent complaints from Socrata --\n")
        step_01 = import_module("01_fetch_data")
        step_01.run()

    # Step 2: Build panel ──────────────────────────────────────────────
    pkl_path = DATA_DIR / "panel.pkl"
    if pkl_path.exists():
        print("\n-- Step 2: Panel already built, loading --\n")
        panel = pickle.loads(pkl_path.read_bytes())
        print(f"  {len(panel.unit_ids)} units x {len(panel.periods)} periods")
    else:
        print("\n-- Step 2: Building balanced panel --\n")
        step_02 = import_module("02_build_panel")
        step_02.run()
        panel = pickle.loads(pkl_path.read_bytes())
    results["panel"] = panel

    # Step 3: Descriptive analysis + factor pipeline ───────────────────
    print("\n-- Step 3: Descriptive Analysis + Factor Pipeline --\n")
    step_03 = import_module("03_descriptive_and_factors")
    results["descriptive"] = step_03.run()

    # Step 4: Temporal analysis ────────────────────────────────────────
    print("\n-- Step 4: Temporal Analysis --\n")
    step_04 = import_module("04_temporal_analysis")
    results["temporal"] = step_04.run()

    # Step 5: Spatial analysis ─────────────────────────────────────────
    print("\n-- Step 5: Spatial Analysis --\n")
    try:
        step_05 = import_module("05_spatial_analysis")
        results["spatial"] = step_05.run()
    except Exception as exc:
        print(f"  Step 05 failed: {exc}")

    # Step 6: Synthetic control ────────────────────────────────────────
    print("\n-- Step 6: Synthetic Control --\n")
    step_06 = import_module("06_synthetic_control")
    results["synthetic_control"] = step_06.run()

    # Step 7: Staggered DiD + event study ──────────────────────────────
    print("\n-- Step 7: Staggered DiD + Event Study --\n")
    step_07 = import_module("07_staggered_did")
    did_result, es_result = step_07.run()
    results["staggered_did"] = did_result
    results["event_study"] = es_result

    # Step 8: Regression discontinuity ─────────────────────────────────
    print("\n-- Step 8: Spatial Discontinuity (RDD) --\n")
    step_08 = import_module("08_spatial_discontinuity")
    rdd_result = step_08.run()
    if rdd_result is not None:
        results["rdd"] = rdd_result

    # Step 9: Power analysis ───────────────────────────────────────────
    print("\n-- Step 9: Power Analysis --\n")
    step_09 = import_module("09_power_analysis")
    results["power"] = step_09.run()

    # Step 10: Generate findings ───────────────────────────────────────
    print("\n-- Step 10: Generating Findings --\n")
    step_10 = import_module("10_generate_findings")
    step_10.run(results)

    print("\n" + "=" * 64)
    print("  Analysis complete.")
    print("=" * 64)


if __name__ == "__main__":
    main()
