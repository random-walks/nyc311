"""Argparse-powered CLI for fetching and analyzing NYC 311 data slices."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from .models import (
    GeographyFilter,
    ServiceRequestFilter,
    SocrataConfig,
)
from .pipeline import fetch_service_requests, run_topic_pipeline

_DEFAULT_SOCRATA_CONFIG = SocrataConfig()


def _add_filter_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--start-date", help="Inclusive start date (YYYY-MM-DD).")
    parser.add_argument("--end-date", help="Inclusive end date (YYYY-MM-DD).")
    parser.add_argument(
        "--geography",
        choices=("borough", "community_district"),
        default="community_district",
        help="Supported aggregation or filter geography.",
    )
    parser.add_argument(
        "--geography-value",
        help="Optional geography filter value for borough/community district.",
    )


def _build_service_request_filter(args: argparse.Namespace) -> ServiceRequestFilter:
    geography_filter = None
    if args.geography_value:
        geography_filter = GeographyFilter(args.geography, args.geography_value)

    raw_complaint_type = getattr(args, "complaint_type", [])
    if isinstance(raw_complaint_type, str):
        complaint_types = (raw_complaint_type,)
    else:
        complaint_types = tuple(raw_complaint_type or ())

    return ServiceRequestFilter(
        start_date=date.fromisoformat(args.start_date) if args.start_date else None,
        end_date=date.fromisoformat(args.end_date) if args.end_date else None,
        geography=geography_filter,
        complaint_types=complaint_types,
    )


def _build_socrata_config(args: argparse.Namespace) -> SocrataConfig:
    return SocrataConfig(
        dataset_identifier=args.dataset_identifier,
        base_url=args.base_url,
        app_token=args.app_token,
        page_size=args.page_size,
        request_timeout_seconds=args.request_timeout_seconds,
        max_pages=args.max_pages,
        extra_where_clauses=tuple(args.where or ()),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the implemented fetch and complaint-topic export commands."""
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
    _add_filter_arguments(export_parser)
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
    _add_filter_arguments(fetch_parser)
    fetch_parser.add_argument(
        "--dataset-identifier",
        default=_DEFAULT_SOCRATA_CONFIG.dataset_identifier,
        help="Socrata dataset identifier.",
    )
    fetch_parser.add_argument(
        "--base-url",
        default=_DEFAULT_SOCRATA_CONFIG.base_url,
        help="Socrata API base URL.",
    )
    fetch_parser.add_argument(
        "--app-token",
        help="Optional Socrata app token for higher-rate live fetches.",
    )
    fetch_parser.add_argument(
        "--page-size",
        type=int,
        default=_DEFAULT_SOCRATA_CONFIG.page_size,
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
        default=_DEFAULT_SOCRATA_CONFIG.request_timeout_seconds,
        help="Timeout in seconds for each Socrata request.",
    )
    fetch_parser.add_argument(
        "--where",
        action="append",
        default=[],
        help="Extra SoQL where clause. Repeatable.",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "topics":
        filters = _build_service_request_filter(args)
        if args.format == "geojson" and not args.boundaries:
            parser.error("--boundaries is required when --format geojson is used.")

        run_topic_pipeline(
            args.source,
            args.complaint_type,
            geography=args.geography,
            filters=filters,
            top_n=args.top_n,
            output=Path(args.output),
            output_format=args.format,
            boundaries=args.boundaries,
        )
        return 0

    if args.command == "fetch":
        filters = _build_service_request_filter(args)
        fetch_service_requests(
            filters=filters,
            socrata_config=_build_socrata_config(args),
            output=Path(args.output),
        )
        return 0

    raise AssertionError(f"Unsupported command: {args.command}")
