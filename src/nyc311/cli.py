"""Command-line interface for the implemented happy path."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from .exporters import export_geojson, export_topic_table
from .loaders import load_boundaries, load_service_requests
from .models import (
    BoundaryGeoJSONExport,
    ExportTarget,
    GeographyFilter,
    ServiceRequestFilter,
    TopicQuery,
)
from .processors import aggregate_by_geography, extract_topics


def main(argv: Sequence[str] | None = None) -> int:
    """Run the implemented complaint-topic export commands."""
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
    export_parser.add_argument(
        "--geography",
        choices=("borough", "community_district"),
        default="community_district",
        help="Supported aggregation geography.",
    )
    export_parser.add_argument(
        "--start-date", help="Inclusive start date (YYYY-MM-DD)."
    )
    export_parser.add_argument("--end-date", help="Inclusive end date (YYYY-MM-DD).")
    export_parser.add_argument(
        "--geography-value",
        help="Optional geography filter value for borough/community district.",
    )
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

    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command != "topics":
        parser.error(f"Unsupported command: {args.command}")

    geography_filter = None
    if args.geography_value:
        geography_filter = GeographyFilter(args.geography, args.geography_value)

    filters = ServiceRequestFilter(
        start_date=date.fromisoformat(args.start_date) if args.start_date else None,
        end_date=date.fromisoformat(args.end_date) if args.end_date else None,
        geography=geography_filter,
        complaint_types=(args.complaint_type,),
    )
    records = load_service_requests(args.source, filters=filters)
    assignments = extract_topics(
        records,
        TopicQuery(complaint_type=args.complaint_type, top_n=args.top_n),
    )
    summaries = aggregate_by_geography(assignments, geography=args.geography)
    target = ExportTarget(format=args.format, output_path=Path(args.output))

    if args.format == "csv":
        export_topic_table(summaries, target)
        return 0

    if not args.boundaries:
        parser.error("--boundaries is required when --format geojson is used.")

    boundaries = load_boundaries(args.boundaries)
    export_geojson(
        BoundaryGeoJSONExport(boundaries=boundaries, summaries=tuple(summaries)), target
    )
    return 0
