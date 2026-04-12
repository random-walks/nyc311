#!/usr/bin/env python3
"""Step 1: Fetch five years of NYC 311 data via bulk_fetch().

Downloads are split per-borough and cached as CSV under ``data/cache/``.
Re-running this script skips boroughs whose files already exist.
"""

from pathlib import Path

from nyc311.pipeline import bulk_fetch


def main() -> None:
    cache_dir = Path(__file__).parent / "data" / "cache"

    def on_progress(borough: str, page: int, rows: int) -> None:
        print(f"  [{borough}] page {page}: {rows} rows")

    print("Fetching 311 data for 2020-01 through 2024-12 ...")
    paths = bulk_fetch(
        start_date="2020-01-01",
        end_date="2024-12-31",
        cache_dir=cache_dir,
        on_progress=on_progress,
    )

    print(f"\nDone. {len(paths)} CSV files written:")
    for p in paths:
        size_mb = p.stat().st_size / 1_048_576
        print(f"  {p.name}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
