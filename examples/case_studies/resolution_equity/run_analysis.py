#!/usr/bin/env python3
"""End-to-end analysis pipeline for the resolution equity case study.

Orchestrates eight analysis steps plus a findings compilation:

  01  Fetch five years of NYC 311 data via bulk_fetch()
  02  Build a balanced community-district x month panel
  03  STL seasonal decomposition and anomaly detection
  04  Equity analysis (panel FE, Theil, Oaxaca-Blinder, EquityGapFactor)
  05  Spatial autocorrelation analysis (Moran's I + LISA)
  06  Policy evaluation (PELT changepoints + interrupted time series)
  07  Latent reporting bias estimation (EM)
  08  Compile FINDINGS.md from stored results

Steps 01--02 require network access (or cached CSV files).  If the
panel parquet already exists, steps 01--02 can be skipped.  Steps 03--07
all depend on the panel.  Step 08 reads the accumulated JSON results.
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
CACHE_DIR = DATA_DIR / "cache"
PANEL_PATH = DATA_DIR / "panel.parquet"


def main() -> None:
    """Run the full analysis pipeline."""
    print("=" * 64)
    print("  Resolution Equity Analysis Pipeline")
    print("  (Real NYC 311 Data)")
    print("=" * 64)

    # Step 1: Fetch data ───────────────────────────────────────────────
    csv_files = sorted(CACHE_DIR.glob("*.csv")) if CACHE_DIR.exists() else []
    if csv_files:
        print("\n-- Step 1: Data already cached, skipping fetch --\n")
        for p in csv_files:
            print(f"  {p.name}  ({p.stat().st_size / 1_048_576:.1f} MB)")
    else:
        print("\n-- Step 1: Fetching NYC 311 data from Socrata --\n")
        step_01 = import_module("01_fetch_data")
        step_01.main()

    # Step 2: Build panel ──────────────────────────────────────────────
    if PANEL_PATH.exists():
        print("\n-- Step 2: Panel already built --\n")
    else:
        print("\n-- Step 2: Building balanced panel --\n")
        step_02 = import_module("02_build_panel")
        step_02.main()

    if not PANEL_PATH.exists():
        print("\nCannot proceed without panel data. Please run:")
        print("  python 01_fetch_data.py")
        print("  python 02_build_panel.py")
        return

    # Step 3: Seasonal decomposition + anomalies ───────────────────────
    print("\n-- Step 3: STL Decomposition + Anomaly Detection --\n")
    try:
        step_03 = import_module("03_decomposition_and_anomalies")
        step_03.main()
    except Exception as exc:
        print(f"  Step 03 failed: {exc}")

    # Step 4: Equity analysis ──────────────────────────────────────────
    print("\n-- Step 4: Equity Analysis --\n")
    try:
        step_04 = import_module("04_equity_analysis")
        step_04.main()
    except Exception as exc:
        print(f"  Step 04 failed: {exc}")

    # Step 5: Spatial analysis ─────────────────────────────────────────
    print("\n-- Step 5: Spatial Autocorrelation (Moran's I + LISA) --\n")
    try:
        step_05 = import_module("05_spatial_analysis")
        step_05.main()
    except Exception as exc:
        print(f"  Step 05 failed: {exc}")

    # Step 6: Policy evaluation ────────────────────────────────────────
    print("\n-- Step 6: Policy Evaluation (Changepoints + ITS) --\n")
    try:
        step_06 = import_module("06_policy_evaluation")
        step_06.main()
    except Exception as exc:
        print(f"  Step 06 failed: {exc}")

    # Step 7: Reporting bias ───────────────────────────────────────────
    print("\n-- Step 7: Latent Reporting Bias (EM) --\n")
    try:
        step_07 = import_module("07_reporting_bias")
        step_07.main()
    except Exception as exc:
        print(f"  Step 07 failed: {exc}")

    # Step 8: Generate findings ────────────────────────────────────────
    print("\n-- Step 8: Generating FINDINGS.md --\n")
    try:
        step_08 = import_module("08_generate_findings")
        step_08.main()
    except Exception as exc:
        print(f"  Step 08 failed: {exc}")

    # Step 9: Render jellycell tearsheets (additive) ──────────────────
    print("\n-- Step 9: Rendering Jellycell Tearsheets --\n")
    try:
        step_09 = import_module("09_generate_tearsheets")
        step_09.run()
    except Exception as exc:
        print(f"  Step 09 (tearsheets) failed: {exc}")
        print("  This step is additive; FINDINGS.md was still generated.")

    print("\n" + "=" * 64)
    print("  Analysis complete.")
    print("=" * 64)


if __name__ == "__main__":
    main()
