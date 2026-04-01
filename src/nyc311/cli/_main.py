"""Main command dispatch for the nyc311 CLI."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from ..pipeline import fetch_service_requests, run_topic_pipeline
from ._args import build_service_request_filter, build_socrata_config
from ._parser import build_parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the implemented fetch and complaint-topic export commands."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "topics":
        filters = build_service_request_filter(args)
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
        filters = build_service_request_filter(args)
        fetch_service_requests(
            filters=filters,
            socrata_config=build_socrata_config(args),
            output=Path(args.output),
        )
        return 0

    raise AssertionError(f"Unsupported command: {args.command}")
