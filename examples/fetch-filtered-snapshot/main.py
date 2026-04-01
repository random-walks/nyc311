from __future__ import annotations

import argparse
import os
from pathlib import Path

from nyc311 import io, models, pipeline, presets

ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / "cache"


def cache_path(filename: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / filename


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch a filtered NYC 311 slice into this example's local cache.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=cache_path("rodent-snapshot.csv"),
        help="Where to store the local CSV snapshot.",
    )
    parser.add_argument(
        "--complaint-type",
        action="append",
        default=[],
        help="Optional complaint type filter. Repeat to include more than one value.",
    )
    parser.add_argument("--start-date", default="2025-01-01")
    parser.add_argument("--end-date", default="2025-01-31")
    parser.add_argument(
        "--geography",
        default="borough",
        choices=("borough", "community_district"),
    )
    parser.add_argument("--geography-value", default=models.BOROUGH_BROOKLYN)
    parser.add_argument("--page-size", type=int, default=500)
    parser.add_argument("--max-pages", type=int, default=1)
    parser.add_argument(
        "--app-token",
        default=os.getenv("NYC_OPEN_DATA_APP_TOKEN"),
        help="Optional Socrata app token. Falls back to NYC_OPEN_DATA_APP_TOKEN.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Ignore any existing cache file and fetch a fresh live slice.",
    )
    return parser


def load_records(args: argparse.Namespace) -> tuple[list[models.ServiceRequestRecord], str]:
    output_path = args.output
    if output_path.exists() and not args.refresh:
        return io.load_service_requests(output_path), "cache"

    filters = presets.build_filter(
        start_date=args.start_date,
        end_date=args.end_date,
        geography=args.geography,
        geography_value=args.geography_value,
        complaint_types=tuple(args.complaint_type or ["Rodent"]),
    )
    config = presets.small_socrata_config(
        app_token=args.app_token,
        page_size=args.page_size,
        max_pages=args.max_pages,
    )
    records = pipeline.fetch_service_requests(
        filters=filters,
        socrata_config=config,
        output=output_path,
    )
    return records, "live fetch"


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    records, source = load_records(args)

    print("Fetch Filtered Snapshot")
    print("-----------------------")
    print(f"Record source: {source}")
    print(f"Rows available in memory: {len(records)}")
    print(f"Snapshot path: {args.output}")


if __name__ == "__main__":
    main()
