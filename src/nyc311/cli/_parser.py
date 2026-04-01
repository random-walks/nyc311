"""Parser construction for the nyc311 CLI."""

from __future__ import annotations

import argparse

from ._args import DEFAULT_SOCRATA_CONFIG, add_filter_arguments


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argparse parser for the nyc311 CLI."""
    parser = argparse.ArgumentParser(prog="nyc311")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser(
        "topics",
        help="Load service requests and export a topic summary.",
    )
    export_parser.add_argument("--source", required=True, help="CSV input path.")
    export_parser.add_argument("--output", required=True, help="Output file path.")
    export_parser.add_argument(
        "--complaint-type", required=True, help="Supported complaint type to analyze."
    )
    add_filter_arguments(export_parser)
    export_parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="Maximum number of topics to keep for the requested complaint type.",
    )
    export_parser.add_argument(
        "--format",
        choices=("csv", "geojson"),
        default="csv",
        help="Export format.",
    )
    export_parser.add_argument(
        "--boundaries",
        help="Boundary GeoJSON required for GeoJSON exports.",
    )

    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Fetch a filtered Socrata slice and write a local CSV snapshot.",
    )
    fetch_parser.add_argument("--output", required=True, help="Output CSV path.")
    fetch_parser.add_argument(
        "--complaint-type",
        action="append",
        default=[],
        help="Optional complaint type filter. Repeat to fetch multiple types.",
    )
    add_filter_arguments(fetch_parser)
    fetch_parser.add_argument(
        "--dataset-identifier",
        default=DEFAULT_SOCRATA_CONFIG.dataset_identifier,
        help="Socrata dataset identifier.",
    )
    fetch_parser.add_argument(
        "--base-url",
        default=DEFAULT_SOCRATA_CONFIG.base_url,
        help="Socrata API base URL.",
    )
    fetch_parser.add_argument(
        "--app-token",
        help="Optional Socrata app token for higher-rate live fetches.",
    )
    fetch_parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_SOCRATA_CONFIG.page_size,
        help="Rows to request per Socrata page.",
    )
    fetch_parser.add_argument(
        "--max-pages",
        type=int,
        help="Optional maximum number of Socrata pages to fetch.",
    )
    fetch_parser.add_argument(
        "--request-timeout-seconds",
        type=float,
        default=DEFAULT_SOCRATA_CONFIG.request_timeout_seconds,
        help="Timeout in seconds for each Socrata request.",
    )
    fetch_parser.add_argument(
        "--where",
        action="append",
        default=[],
        help="Extra SoQL where clause. Repeatable.",
    )

    return parser
