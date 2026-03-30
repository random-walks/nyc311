"""Loader entry points for implemented and planned NYC 311 data sources."""

from __future__ import annotations

import csv
from collections.abc import Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Final

from ._not_implemented import planned_surface
from .models import GeographyFilter, ServiceRequestFilter, ServiceRequestRecord

_REQUIRED_COLUMNS: Final[frozenset[str]] = frozenset(
    {"unique_key", "created_date", "complaint_type", "descriptor", "borough"}
)
_COMMUNITY_DISTRICT_ALIASES: Final[tuple[str, ...]] = (
    "community_district",
    "community_board",
)
REQUIRED_SERVICE_REQUEST_COLUMNS: Final[tuple[str, ...]] = (
    "unique_key",
    "created_date",
    "complaint_type",
    "descriptor",
    "borough",
    "community_district",
)


def _parse_created_date(raw_value: str) -> date:
    """Parse a NYC 311-style created-date string into a ``date``."""
    normalized_value = raw_value.strip()
    if not normalized_value:
        raise ValueError("created_date must not be empty.")

    normalized_value = normalized_value.removesuffix("Z")
    if "T" in normalized_value:
        return datetime.fromisoformat(normalized_value).date()
    if " " in normalized_value:
        return datetime.fromisoformat(normalized_value).date()
    return date.fromisoformat(normalized_value)


def _casefold(value: str) -> str:
    """Case-insensitive normalization used for filters."""
    return " ".join(value.strip().split()).casefold()


def _community_district_column(fieldnames: Sequence[str]) -> str:
    """Resolve the supported community-district source column."""
    for candidate in _COMMUNITY_DISTRICT_ALIASES:
        if candidate in fieldnames:
            return candidate

    expected = ", ".join(_COMMUNITY_DISTRICT_ALIASES)
    raise ValueError(
        f"CSV file is missing a community-district column. Expected one of: {expected}."
    )


def _validate_columns(fieldnames: Sequence[str]) -> str:
    """Validate that a CSV contains the required v0.1 columns."""
    missing_columns = sorted(_REQUIRED_COLUMNS.difference(fieldnames))
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(
            f"CSV file is missing required columns for v0.1 loading: {missing}."
        )
    return _community_district_column(fieldnames)


def _matches_geography(
    record: ServiceRequestRecord, geography_filter: GeographyFilter | None
) -> bool:
    """Return whether a record satisfies the optional geography filter."""
    if geography_filter is None:
        return True
    return _casefold(record.geography_value(geography_filter.geography)) == _casefold(
        geography_filter.value
    )


def _matches_complaint_type(
    record: ServiceRequestRecord, complaint_types: tuple[str, ...]
) -> bool:
    """Return whether a record matches the optional complaint-type allowlist."""
    if not complaint_types:
        return True
    normalized_complaint_type = _casefold(record.complaint_type)
    return any(
        normalized_complaint_type == _casefold(complaint_type)
        for complaint_type in complaint_types
    )


def _matches_date_range(
    record: ServiceRequestRecord, service_request_filter: ServiceRequestFilter
) -> bool:
    """Return whether a record falls within the optional date range."""
    if (
        service_request_filter.start_date
        and record.created_date < service_request_filter.start_date
    ):
        return False
    if (
        service_request_filter.end_date
        and record.created_date > service_request_filter.end_date
    ):
        return False
    return True


def load_service_requests(
    source: str | Path,
    *,
    filters: ServiceRequestFilter | None = None,
) -> list[ServiceRequestRecord]:
    """Load filtered NYC 311-style service-request records from a local CSV."""
    source_path = Path(source)
    with source_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames
        if fieldnames is None:
            raise ValueError("CSV file must include a header row.")

        community_district_column = _validate_columns(fieldnames)
        service_request_filter = filters or ServiceRequestFilter()
        loaded_records: list[ServiceRequestRecord] = []

        for row in reader:
            record = ServiceRequestRecord(
                service_request_id=row["unique_key"],
                created_date=_parse_created_date(row["created_date"]),
                complaint_type=row["complaint_type"],
                descriptor=row["descriptor"],
                borough=row["borough"],
                community_district=row[community_district_column],
                resolution_description=row.get("resolution_description"),
            )
            if not _matches_date_range(record, service_request_filter):
                continue
            if not _matches_geography(record, service_request_filter.geography):
                continue
            if not _matches_complaint_type(
                record, service_request_filter.complaint_types
            ):
                continue
            loaded_records.append(record)

    return loaded_records


def load_resolution_data(source: str | Path) -> list[object]:
    """Load or derive resolution-related fields for gap analysis."""
    del source
    planned_surface("load_resolution_data()")


def load_boundaries(source: str | Path) -> object:
    """Load spatial boundaries used for tract, district, or borough aggregation."""
    del source
    planned_surface("load_boundaries()")
