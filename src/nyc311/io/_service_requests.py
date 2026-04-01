"""High-level service-request loading entrypoints."""

from __future__ import annotations

from pathlib import Path
from urllib.request import urlopen

from ..models import ServiceRequestFilter, ServiceRequestRecord, SocrataConfig
from ._csv import load_service_requests_from_csv
from ._socrata import load_service_requests_from_socrata


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
