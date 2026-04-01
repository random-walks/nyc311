"""Shared filtering helpers for loaded service-request records."""

from __future__ import annotations

from ..models import GeographyFilter, ServiceRequestFilter, ServiceRequestRecord


def _casefold(value: str) -> str:
    """Case-insensitive normalization used for filters."""
    return " ".join(value.strip().split()).casefold()


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
