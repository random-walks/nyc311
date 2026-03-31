from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import nyc311


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch a filtered NYC 311 Socrata snapshot into a local CSV."
    )
    parser.add_argument(
        "--output",
        default="examples/output/rodent_snapshot.csv",
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
        filters=nyc311.ServiceRequestFilter(
            start_date=date.fromisoformat(args.start_date),
            end_date=date.fromisoformat(args.end_date),
            geography=nyc311.GeographyFilter(args.geography, args.geography_value),
            complaint_types=tuple(complaint_types),
        ),
        socrata_config=nyc311.SocrataConfig(
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
