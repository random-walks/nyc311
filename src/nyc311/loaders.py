"""Load NYC 311-style records and boundary data into typed nyc311 models.

This module contains the implemented ingestion paths for local CSV extracts,
live Socrata queries, boundary GeoJSON files, and resolution-data loading used
by the analysis and reporting helpers.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Final
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .boundaries import load_boundary_collection
from .models import (
    BoundaryCollection,
    GeographyFilter,
    ServiceRequestFilter,
    ServiceRequestRecord,
    SocrataConfig,
)

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

_SOCRATA_FIELD_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "unique_key": ("unique_key",),
    "created_date": ("created_date",),
    "complaint_type": ("complaint_type",),
    "descriptor": ("descriptor",),
    "borough": ("borough",),
    "community_district": ("community_district", "community_board"),
    "resolution_description": ("resolution_description",),
}


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
    """Validate that a CSV contains the required implemented columns."""
    missing_columns = sorted(_REQUIRED_COLUMNS.difference(fieldnames))
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(
            f"CSV file is missing required columns for loading: {missing}."
        )
    return _community_district_column(fieldnames)


def _matches_geography(
    record: ServiceRequestRecord, geography_filter: GeographyFilter | None
) -> bool:
    if geography_filter is None:
        return True
    return _casefold(record.geography_value(geography_filter.geography)) == _casefold(
        geography_filter.value
    )


def _matches_complaint_type(
    record: ServiceRequestRecord, complaint_types: tuple[str, ...]
) -> bool:
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
    )


def _apply_filters(
    records: list[ServiceRequestRecord],
    service_request_filter: ServiceRequestFilter,
) -> list[ServiceRequestRecord]:
    filtered_records: list[ServiceRequestRecord] = []
    for record in records:
        if not _matches_date_range(record, service_request_filter):
            continue
        if not _matches_geography(record, service_request_filter.geography):
            continue
        if not _matches_complaint_type(record, service_request_filter.complaint_types):
            continue
        filtered_records.append(record)
    return filtered_records


def _normalize_socrata_row(raw_row: dict[str, object]) -> dict[str, str]:
    normalized_row: dict[str, str] = {}
    missing_fields: list[str] = []

    for canonical_field, aliases in _SOCRATA_FIELD_ALIASES.items():
        matched_value: object | None = None
        for alias in aliases:
            candidate = raw_row.get(alias)
            if candidate not in (None, ""):
                matched_value = candidate
                break

        if matched_value is None:
            if canonical_field == "descriptor":
                normalized_row[canonical_field] = ""
                continue
            if canonical_field == "resolution_description":
                continue
            missing_fields.append(canonical_field)
            continue

        normalized_row[canonical_field] = str(matched_value)

    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"Socrata response row is missing required fields: {missing}.")

    return normalized_row


def _socrata_select_fields() -> str:
    return (
        "unique_key, created_date, complaint_type, descriptor, borough, "
        "community_board, resolution_description"
    )


def _socrata_where_clauses(service_request_filter: ServiceRequestFilter) -> list[str]:
    clauses: list[str] = []
    if service_request_filter.start_date is not None:
        clauses.append(
            f"created_date >= '{service_request_filter.start_date.isoformat()}T00:00:00'"
        )
    if service_request_filter.end_date is not None:
        clauses.append(
            f"created_date <= '{service_request_filter.end_date.isoformat()}T23:59:59'"
        )
    if service_request_filter.geography is not None:
        field = service_request_filter.geography.geography
        value = service_request_filter.geography.value.replace("'", "''")
        if field == "community_district":
            clauses.append(f"community_board = '{value}'")
        else:
            clauses.append(f"{field} = '{value}'")
    if service_request_filter.complaint_types:
        escaped_values = [
            complaint_type.replace("'", "''")
            for complaint_type in service_request_filter.complaint_types
        ]
        allowed_values = ", ".join(
            f"'{complaint_type}'" for complaint_type in escaped_values
        )
        clauses.append(f"complaint_type IN ({allowed_values})")
    return clauses


def _build_socrata_url(
    socrata_config: SocrataConfig,
    service_request_filter: ServiceRequestFilter,
    *,
    offset: int,
) -> str:
    query_params: dict[str, str] = {
        "$select": _socrata_select_fields(),
        "$limit": str(socrata_config.page_size),
        "$offset": str(offset),
        "$order": "created_date ASC, unique_key ASC",
    }
    where_clauses = _socrata_where_clauses(service_request_filter)
    if socrata_config.extra_where_clauses:
        where_clauses.extend(socrata_config.extra_where_clauses)
    if where_clauses:
        query_params["$where"] = " AND ".join(where_clauses)
    encoded_query = urlencode(query_params)
    return f"{socrata_config.base_url}/{socrata_config.dataset_identifier}.json?{encoded_query}"


def _load_service_requests_from_socrata(
    socrata_config: SocrataConfig,
    service_request_filter: ServiceRequestFilter,
) -> list[ServiceRequestRecord]:
    headers = {"Accept": "application/json"}
    if socrata_config.app_token is not None:
        headers["X-App-Token"] = socrata_config.app_token

    request_limit = socrata_config.page_size
    offset = 0
    page_count = 0
    records: list[ServiceRequestRecord] = []

    while True:
        if (
            socrata_config.max_pages is not None
            and page_count >= socrata_config.max_pages
        ):
            break

        request_url = _build_socrata_url(
            socrata_config, service_request_filter, offset=offset
        )
        request = Request(request_url, headers=headers)
        with urlopen(
            request, timeout=socrata_config.request_timeout_seconds
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))

        if not isinstance(payload, list):
            raise ValueError(
                "Unexpected Socrata response payload; expected a JSON list."
            )
        if not payload:
            break

        batch_records: list[ServiceRequestRecord] = []
        for raw_row in payload:
            if not isinstance(raw_row, dict):
                raise ValueError(
                    "Unexpected Socrata response row; expected a JSON object."
                )
            normalized_row = _normalize_socrata_row(raw_row)
            community_district_column = (
                "community_district"
                if "community_district" in normalized_row
                else "community_board"
            )
            batch_records.append(
                _record_from_mapping(normalized_row, community_district_column)
            )

        records.extend(batch_records)
        if len(payload) < request_limit:
            break
        offset += request_limit
        page_count += 1

    return _apply_filters(records, service_request_filter)


def load_service_requests(
    source: str | Path | SocrataConfig,
    *,
    filters: ServiceRequestFilter | None = None,
) -> list[ServiceRequestRecord]:
    """Load filtered NYC 311-style service-request records from CSV or Socrata."""
    service_request_filter = filters or ServiceRequestFilter()
    if isinstance(source, SocrataConfig):
        return _load_service_requests_from_socrata(source, service_request_filter)

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

    return _apply_filters(loaded_records, service_request_filter)


def load_resolution_data(
    source: str | Path | SocrataConfig,
    *,
    filters: ServiceRequestFilter | None = None,
) -> list[ServiceRequestRecord]:
    """Load the subset of service requests that already include resolution text."""
    loaded_records = load_service_requests(source, filters=filters)
    return [
        record for record in loaded_records if record.resolution_description is not None
    ]


def load_boundaries(source: str | Path) -> BoundaryCollection:
    """Load boundary polygons from a GeoJSON file for supported exports."""
    return load_boundary_collection(source)
