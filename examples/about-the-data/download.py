"""Bulk Socrata + boundary downloads for the about-the-data example.

Re-run safely: completed borough CSVs are skipped unless ``--refresh`` is set.
Interrupted runs leave only ``*.csv.part`` (removed on the next attempt).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Literal

from dates import parse_cli_date
from download_logic import (
    download_all_records,
    download_boundary_layers,
    download_per_type_records,
    parse_borough_list,
    parse_complaint_types,
)
from parsers import build_common_parser, build_download_parser


def run_download(args: argparse.Namespace) -> None:
    boroughs = parse_borough_list(args.boroughs)
    start = parse_cli_date(args.start_date)
    end = parse_cli_date(args.end_date)
    types = parse_complaint_types(args.complaint_types)
    cache_root = Path(args.cache_dir).expanduser().resolve()
    app_token: str | None = args.app_token

    if args.request_timeout is None:
        request_timeout = 120.0 if args.preset == "smoke" else 300.0
    else:
        request_timeout = args.request_timeout

    if args.preset == "smoke":
        max_records = (
            args.max_records_per_borough
            if args.max_records_per_borough is not None
            else 100_000
        )
        sort_order: Literal["asc", "desc"] = "desc"
    else:
        max_records = args.max_records_per_borough
        sort_order = "asc"

    progress = not args.no_progress

    if not args.skip_boundaries:
        download_boundary_layers(cache_root, refresh=args.refresh)
    download_all_records(
        cache_root,
        boroughs,
        refresh=args.refresh,
        app_token=app_token,
        start_date=start,
        end_date=end,
        page_size=args.page_size,
        max_records_per_borough=max_records,
        request_timeout_seconds=request_timeout,
        created_date_sort=sort_order,
        progress=progress,
        verbose=args.verbose,
    )
    if args.download_by_type:
        download_per_type_records(
            cache_root,
            boroughs,
            types,
            refresh=args.refresh,
            app_token=app_token,
            start_date=start,
            end_date=end,
            page_size=args.page_size,
            max_records_per_borough=max_records,
            request_timeout_seconds=request_timeout,
            created_date_sort=sort_order,
            progress=progress,
            verbose=args.verbose,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        parents=[build_common_parser(), build_download_parser()],
    )
    args = parser.parse_args()
    run_download(args)


if __name__ == "__main__":
    main()
