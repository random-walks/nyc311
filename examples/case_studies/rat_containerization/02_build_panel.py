#!/usr/bin/env python3
"""Step 2: Build a balanced community-district x month panel from real data.

Loads cached Rodent complaint CSVs from step 01, constructs a balanced
panel via ``build_complaint_panel()``, and defines the treatment event
for the 2024 NYC rat containerization mandate.

Treatment timeline (real policy):
  - June 2024: Pilot enforcement in lower Manhattan CDs
  - Nov 12, 2024: Citywide containerization mandate effective

This study uses June 2024 as the treatment date for Manhattan CDs 01-09
(the initial pilot zone), with remaining CDs as the control group.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from nyc311.io import load_service_requests
from nyc311.temporal import build_complaint_panel
from nyc311.temporal._models import TreatmentEvent

# The actual Manhattan community districts in the initial pilot zone
TREATED_UNITS = (
    "MANHATTAN 01",
    "MANHATTAN 02",
    "MANHATTAN 03",
    "MANHATTAN 04",
    "MANHATTAN 05",
    "MANHATTAN 06",
    "MANHATTAN 07",
    "MANHATTAN 08",
    "MANHATTAN 09",
)

TREATMENT = TreatmentEvent(
    name="rat_containerization_mandate",
    description=(
        "2024 NYC rat containerization mandate -- pilot enforcement "
        "in lower Manhattan community districts beginning June 2024"
    ),
    treated_units=TREATED_UNITS,
    treatment_date=date(2024, 6, 1),
    geography="community_district",
)


def run() -> None:
    """Load cached CSVs, build panel, and export to parquet."""
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

    print(f"\n  Total records: {len(all_records):,}")
    print("Building balanced panel (community_district x month) ...")

    panel = build_complaint_panel(
        all_records,
        geography="community_district",
        freq="ME",
        treatment_events=(TREATMENT,),
    )

    print(f"  Units: {len(panel.unit_ids)}")
    print(f"  Periods: {len(panel.periods)}")
    print(f"  Observations: {len(panel.observations)}")
    print(f"  Treated units: {len(TREATED_UNITS)} ({', '.join(TREATED_UNITS[:3])}...)")
    print(f"  Treatment date: {TREATMENT.treatment_date}")

    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Save DataFrame (for quick loading in steps that need only tabular data)
    parquet_path = data_dir / "panel.parquet"
    df = panel.to_dataframe()
    df.to_parquet(parquet_path)
    print(f"\n  Panel DataFrame exported to {parquet_path}")

    # Save PanelDataset object (for steps that need the full object, e.g. SCM/DiD)
    import pickle

    pkl_path = data_dir / "panel.pkl"
    pkl_path.write_bytes(pickle.dumps(panel))
    print(f"  PanelDataset object saved to {pkl_path}")


if __name__ == "__main__":
    print("Step 2: Building balanced panel\n")
    run()
