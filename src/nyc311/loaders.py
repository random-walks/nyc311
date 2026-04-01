"""Load NYC 311-style records and boundary data into typed nyc311 models."""

from __future__ import annotations

from pathlib import Path
from urllib.request import urlopen

from .boundaries import load_boundary_collection
from .filters import (
    _apply_filters,
    _casefold,
    _matches_complaint_type,
    _matches_date_range,
    _matches_geography,
)
from .geographies.loaders import (
    list_boundary_layers,
    list_boundary_values,
    load_nyc_boundaries,
    load_sample_boundaries,
    load_sample_service_requests,
)
from .loaders_csv import (
    REQUIRED_SERVICE_REQUEST_COLUMNS,
    _community_district_column,
    _parse_created_date,
    _parse_optional_coordinate,
    _record_from_mapping,
    _validate_columns,
    load_service_requests_from_csv,
)
from .loaders_socrata import (
    _SOCRATA_FIELD_ALIASES,
    _build_socrata_url,
    _normalize_socrata_row,
    _socrata_select_fields,
    _socrata_where_clauses,
    load_service_requests_from_socrata,
)
from .models import (
    BoundaryCollection,
    ServiceRequestFilter,
    ServiceRequestRecord,
    SocrataConfig,
)


def load_service_requests(
    source: str | Path | SocrataConfig,
    *,
    filters: ServiceRequestFilter | None = None,
) -> list[ServiceRequestRecord]:
    """Load filtered NYC 311-style service-request records from CSV or Socrata."""
    service_request_filter = filters or ServiceRequestFilter()
    if isinstance(source, SocrataConfig):
        return load_service_requests_from_socrata(
            source,
            filters=service_request_filter,
            request_open=urlopen,
        )

    return load_service_requests_from_csv(source, filters=service_request_filter)


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
    """Load boundaries from a file path or a packaged NYC boundary layer."""
    if isinstance(source, Path) or Path(source).exists():
        return load_boundary_collection(source)
    try:
        return load_nyc_boundaries(str(source))
    except ValueError:
        return load_boundary_collection(source)


__all__ = [
    "REQUIRED_SERVICE_REQUEST_COLUMNS",
    "_SOCRATA_FIELD_ALIASES",
    "_apply_filters",
    "_build_socrata_url",
    "_casefold",
    "_community_district_column",
    "_matches_complaint_type",
    "_matches_date_range",
    "_matches_geography",
    "_normalize_socrata_row",
    "_parse_created_date",
    "_parse_optional_coordinate",
    "_record_from_mapping",
    "_socrata_select_fields",
    "_socrata_where_clauses",
    "_validate_columns",
    "list_boundary_layers",
    "list_boundary_values",
    "load_boundaries",
    "load_nyc_boundaries",
    "load_sample_boundaries",
    "load_sample_service_requests",
    "load_resolution_data",
    "load_service_requests",
    "load_service_requests_from_csv",
    "load_service_requests_from_socrata",
]
