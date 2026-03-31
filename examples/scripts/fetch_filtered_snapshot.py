from __future__ import annotations

import argparse
from pathlib import Path
import sys

import nyc311

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from examples.utils import build_filter, brooklyn_socrata_config, output_path  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch a filtered NYC 311 Socrata snapshot into a local CSV."
    )
    parser.add_argument(
        "--output",
        default=str(output_path("rodent_snapshot.csv")),
        help="Where to write the fetched CSV snapshot.",
    )
    parser.add_argument(
        "--complaint-type",
        action="append",
        default=[],
        help="Optional complaint type filter. Repeat to fetch multiple types.",
    )
    parser.add_argument("--start-date", default="2025-01-01")
    parser.add_argument("--end-date", default="2025-01-31")
    parser.add_argument(
        "--geography",
        default="borough",
        choices=("borough", "community_district"),
    )
    parser.add_argument("--geography-value", default=nyc311.BOROUGH_BROOKLYN)
    parser.add_argument(
        "--page-size",
        default="500",
        help="Rows per Socrata page. Start small while developing.",
    )
    parser.add_argument(
        "--max-pages",
        default="1",
        help="Maximum pages to fetch during development.",
    )
    parser.add_argument(
        "--app-token",
        help="Optional Socrata app token. Recommended for heavier usage.",
    )
    parser.add_argument(
        "--skip-export",
        action="store_true",
        help="Fetch into memory only and skip writing the CSV snapshot.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    complaint_types = args.complaint_type or ["Rodent"]
    records = nyc311.fetch_service_requests(
        filters=build_filter(
            start_date=args.start_date,
            end_date=args.end_date,
            geography=args.geography,
            geography_value=args.geography_value,
            complaint_types=tuple(complaint_types),
        ),
        socrata_config=brooklyn_socrata_config(
            app_token=args.app_token,
            page_size=int(args.page_size),
            max_pages=int(args.max_pages) if args.max_pages else None,
        ),
        output=None if args.skip_export else Path(args.output),
    )

    print(f"Fetched {len(records)} live records.")
    if args.skip_export:
        print("Skipped CSV export; records are available in memory only in this run.")
        return

    print(f"Wrote snapshot to {args.output}")


if __name__ == "__main__":
    main()
