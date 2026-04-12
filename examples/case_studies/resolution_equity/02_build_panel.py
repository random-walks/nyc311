#!/usr/bin/env python3
"""Step 2: Build a balanced community-district x month panel.

Loads cached CSV files from step 01, constructs the panel via
``build_complaint_panel()``, and exports to a pickle for downstream
analysis scripts.
"""

from pathlib import Path

from nyc311.io import load_service_requests
from nyc311.temporal import build_complaint_panel


def main() -> None:
    cache_dir = Path(__file__).parent / "data" / "cache"
    csv_files = sorted(cache_dir.glob("*.csv"))

    if not csv_files:
        print("No cached CSV files found. Run 01_fetch_data.py first.")
        return

    print(f"Loading records from {len(csv_files)} CSV files ...")
    all_records = []
    for csv_path in csv_files:
        records = load_service_requests(csv_path)
        all_records.extend(records)
        print(f"  {csv_path.name}: {len(records):,} records")

    print(f"\nTotal records: {len(all_records):,}")
    print("Building balanced panel (community_district x month) ...")

    panel = build_complaint_panel(
        all_records,
        geography="community_district",
        freq="ME",
    )

    print(f"  Units: {len(panel.unit_ids)}")
    print(f"  Periods: {len(panel.periods)}")
    print(f"  Observations: {len(panel.observations)}")

    df = panel.to_dataframe()
    output_path = Path(__file__).parent / "data" / "panel.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path)
    print(f"\nPanel exported to {output_path}")


if __name__ == "__main__":
    main()
