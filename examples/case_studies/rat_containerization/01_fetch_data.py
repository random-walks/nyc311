#!/usr/bin/env python3
"""Step 1: Fetch rodent complaint data from NYC Open Data (Socrata).

Downloads Rodent-type 311 complaints for 2023--2024, split per-borough
and cached as CSV under ``data/cache/``.  Re-running skips boroughs
whose files already exist.
"""

from __future__ import annotations

from pathlib import Path

from nyc311.pipeline import bulk_fetch


def run() -> list[Path]:
    """Fetch rodent complaint data and return paths to cached CSVs."""
    cache_dir = Path(__file__).parent / "data" / "cache"

    def on_progress(borough: str, page: int, rows: int) -> None:
        print(f"  [{borough}] page {page}: {rows} rows")

    print("Fetching Rodent complaints (2023-01 through 2024-12) ...")
    paths = bulk_fetch(
        complaint_types=("Rodent",),
        start_date="2023-01-01",
        end_date="2024-12-31",
        cache_dir=cache_dir,
        on_progress=on_progress,
    )

    print(f"\n  {len(paths)} CSV files cached:")
    for p in paths:
        size_mb = p.stat().st_size / 1_048_576
        print(f"    {p.name}  ({size_mb:.1f} MB)")

    return paths


if __name__ == "__main__":
    print("Step 1: Fetching rodent complaint data\n")
    run()
