"""High-level service-request loading entrypoints."""

from __future__ import annotations

from pathlib import Path
from urllib.request import urlopen

from ..models import ServiceRequestFilter, ServiceRequestRecord, SocrataConfig
from ._cache import cached_fetch
from ._csv import load_service_requests_from_csv
from ._socrata import load_service_requests_from_socrata


def load_service_requests(
    source: str | Path | SocrataConfig,
    *,
    filters: ServiceRequestFilter | None = None,
    cache_dir: Path | str | None = None,
    refresh: bool = False,
    max_cached_records: int | None = None,
) -> list[ServiceRequestRecord]:
    """Load filtered NYC 311-style service-request records from CSV or Socrata.

    When ``source`` is a :class:`~nyc311.models.SocrataConfig` and ``cache_dir``
    is set, the live API response is streamed to a deterministic CSV under
    ``cache_dir`` (see :func:`cached_fetch`), then loaded from disk. Very large
    extracts should use :func:`cached_fetch` with chunked pandas analysis instead
    of this helper, which returns an in-memory list.
    """
    service_request_filter = filters or ServiceRequestFilter()
    if isinstance(source, SocrataConfig):
        if cache_dir is not None:
            cache_path = Path(cache_dir)
            csv_path = cached_fetch(
                source,
                service_request_filter,
                cache_dir=cache_path,
                refresh=refresh,
                request_open=urlopen,
                max_records=max_cached_records,
            )
            return load_service_requests_from_csv(
                csv_path, filters=service_request_filter
            )
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
    cache_dir: Path | str | None = None,
    refresh: bool = False,
    max_cached_records: int | None = None,
) -> list[ServiceRequestRecord]:
    """Load the subset of service requests that already include resolution text."""
    loaded_records = load_service_requests(
        source,
        filters=filters,
        cache_dir=cache_dir,
        refresh=refresh,
        max_cached_records=max_cached_records,
    )
    return [
        record for record in loaded_records if record.resolution_description is not None
    ]
