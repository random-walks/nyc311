"""CSV loading helpers for NYC 311-style service-request records."""

from __future__ import annotations

import csv
from collections.abc import Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Final

from ..export._tabular import SERVICE_REQUEST_CSV_COLUMNS
from ..models import ServiceRequestFilter, ServiceRequestRecord
from ._filters import _apply_filters

_REQUIRED_COLUMNS: Final[frozenset[str]] = frozenset(
    {"unique_key", "created_date", "complaint_type", "descriptor", "borough"}
)
_COMMUNITY_DISTRICT_ALIASES: Final[tuple[str, ...]] = (
    "community_district",
    "community_board",
)
REQUIRED_SERVICE_REQUEST_COLUMNS: Final[tuple[str, ...]] = SERVICE_REQUEST_CSV_COLUMNS


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


def _parse_optional_date(raw_value: str | None) -> date | None:
    """Parse an optional NYC 311-style date string into a ``date`` or ``None``.

    Accepts the same ISO shapes as :func:`_parse_created_date` plus
    empty / ``None`` inputs for unresolved complaints.
    """
    if raw_value is None:
        return None
    if not raw_value.strip():
        return None
    return _parse_created_date(raw_value)


def _parse_optional_coordinate(raw_value: str | None) -> float | None:
    if raw_value is None:
        return None
    normalized_value = raw_value.strip()
    if not normalized_value:
        return None
    return float(normalized_value)


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
    """Validate that a CSV contains the required implemented columns."""
    missing_columns = sorted(_REQUIRED_COLUMNS.difference(fieldnames))
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(
            f"CSV file is missing required columns for loading: {missing}."
        )
    return _community_district_column(fieldnames)


def _record_from_mapping(
    row: dict[str, str], community_district_column: str
) -> ServiceRequestRecord:
    return ServiceRequestRecord(
        service_request_id=row["unique_key"],
        created_date=_parse_created_date(row["created_date"]),
        complaint_type=row["complaint_type"],
        descriptor=row["descriptor"],
        borough=row["borough"],
        community_district=row[community_district_column],
        resolution_description=row.get("resolution_description"),
        latitude=_parse_optional_coordinate(row.get("latitude")),
        longitude=_parse_optional_coordinate(row.get("longitude")),
        closed_date=_parse_optional_date(row.get("closed_date")),
    )


def load_service_requests_from_csv(
    source: str | Path,
    *,
    filters: ServiceRequestFilter,
) -> list[ServiceRequestRecord]:
    """Load and filter service-request records from a local CSV snapshot."""
    source_path = Path(source)
    with source_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames
        if fieldnames is None:
            raise ValueError("CSV file must include a header row.")

        community_district_column = _validate_columns(fieldnames)
        loaded_records = [
            _record_from_mapping(row, community_district_column) for row in reader
        ]

    return _apply_filters(loaded_records, filters)
