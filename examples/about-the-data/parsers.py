"""Shared argparse fragments for download / analyze / main."""

from __future__ import annotations

import os
from argparse import ArgumentParser
from pathlib import Path

from download_logic import ALL_BOROUGHS
from paths import DEFAULT_CACHE


def build_common_parser() -> ArgumentParser:
    p = ArgumentParser(add_help=False)
    p.add_argument(
        "--boroughs",
        default=",".join(ALL_BOROUGHS),
        help="Comma-separated boroughs (default: all five).",
    )
    p.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    return p


def build_download_parser() -> ArgumentParser:
    p = ArgumentParser(add_help=False)
    p.add_argument(
        "--preset",
        choices=("full", "smoke"),
        default="full",
        help=(
            "full: chronological order (oldest first), no row cap unless "
            "--max-records-per-borough. smoke: ~10k most recent rows per borough "
            "(DESC), smaller default timeouts."
        ),
    )
    p.add_argument("--start-date", default="2010-01-01")
    p.add_argument("--end-date", default=None)
    p.add_argument(
        "--complaint-types",
        default=None,
        help="Comma subset of supported topic complaint types (default: all 9).",
    )
    p.add_argument("--refresh", action="store_true")
    p.add_argument("--app-token", default=os.environ.get("NYC_OPEN_DATA_APP_TOKEN"))
    p.add_argument(
        "--page-size",
        type=int,
        default=5_000,
        help="Rows per Socrata HTTP request (default 5000 for smaller pages).",
    )
    p.add_argument(
        "--request-timeout",
        type=float,
        default=None,
        metavar="SECONDS",
        help=(
            "Per-request HTTP timeout (default: 300s for full, 120s for smoke; "
            "override explicitly, e.g. 600 on slow links)."
        ),
    )
    p.add_argument("--max-records-per-borough", type=int, default=None)
    p.add_argument(
        "--download-by-type",
        action="store_true",
        help="Also fetch per-(borough, complaint type) CSVs (large overlap).",
    )
    p.add_argument(
        "--skip-boundaries",
        action="store_true",
        help="Do not write cache/boundaries/*.geojson (use existing files).",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print per-borough skip/fetch status.",
    )
    p.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable per-page row count lines (pages still use small batches).",
    )
    return p


def build_analyze_parser() -> ArgumentParser:
    p = ArgumentParser(add_help=False)
    p.add_argument("--skip-timeseries", action="store_true")
    p.add_argument("--skip-choropleth", action="store_true")
    p.add_argument("--skip-scatter", action="store_true")
    p.add_argument("--skip-hero", action="store_true")
    p.add_argument("--skip-analysis", action="store_true")
    p.add_argument("--no-publish-report", action="store_true")
    p.add_argument(
        "--clear-figures",
        action="store_true",
        help="Delete reports/figures/*.png before regenerating figures.",
    )
    p.add_argument(
        "--clear-report",
        action="store_true",
        help="Delete reports/about-the-data-tearsheet.md before writing a new one.",
    )
    return p


def build_main_parser() -> ArgumentParser:
    p = ArgumentParser(
        description=(
            "Download NYC 311 Socrata slices (optional) and build catalogue + figures."
        ),
        parents=[
            build_common_parser(),
            build_download_parser(),
            build_analyze_parser(),
        ],
    )
    p.add_argument(
        "--skip-download",
        action="store_true",
        help="Only run analysis / figures (reuse cache/).",
    )
    return p
