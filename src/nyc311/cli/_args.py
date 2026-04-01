"""Argument helpers for the nyc311 CLI."""

from __future__ import annotations

import argparse
from datetime import date

from ..models import GeographyFilter, ServiceRequestFilter, SocrataConfig

DEFAULT_SOCRATA_CONFIG = SocrataConfig()


def add_filter_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the shared date and geography filter flags."""
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


def build_service_request_filter(args: argparse.Namespace) -> ServiceRequestFilter:
    """Convert parsed CLI args into a typed service-request filter."""
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


def build_socrata_config(args: argparse.Namespace) -> SocrataConfig:
    """Convert parsed CLI args into a typed Socrata config."""
    return SocrataConfig(
        dataset_identifier=args.dataset_identifier,
        base_url=args.base_url,
        app_token=args.app_token,
        page_size=args.page_size,
        request_timeout_seconds=args.request_timeout_seconds,
        max_pages=args.max_pages,
        extra_where_clauses=tuple(args.where or ()),
    )
