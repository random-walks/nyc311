"""Socrata loading helpers for live NYC 311 data fetches."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterator
from typing import Any, Final
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request

from ..models import ServiceRequestFilter, ServiceRequestRecord, SocrataConfig
from ._csv import _record_from_mapping
from ._filters import _apply_filters

_SOCRATA_FIELD_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "unique_key": ("unique_key",),
    "created_date": ("created_date",),
    "complaint_type": ("complaint_type",),
    "descriptor": ("descriptor",),
    "borough": ("borough",),
    "community_district": ("community_district", "community_board"),
    "resolution_description": ("resolution_description",),
    "latitude": ("latitude",),
    "longitude": ("longitude",),
}


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
            if canonical_field in {
                "resolution_description",
                "latitude",
                "longitude",
            }:
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
        "community_board, resolution_description, latitude, longitude"
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


def _socrata_order_clause(socrata_config: SocrataConfig) -> str:
    if socrata_config.created_date_sort == "desc":
        return "created_date DESC, unique_key DESC"
    return "created_date ASC, unique_key ASC"


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
        "$order": _socrata_order_clause(socrata_config),
    }
    where_clauses = _socrata_where_clauses(service_request_filter)
    if socrata_config.extra_where_clauses:
        where_clauses.extend(socrata_config.extra_where_clauses)
    if where_clauses:
        query_params["$where"] = " AND ".join(where_clauses)
    encoded_query = urlencode(query_params)
    return f"{socrata_config.base_url}/{socrata_config.dataset_identifier}.json?{encoded_query}"


def _read_socrata_page_once(
    request: Request,
    request_open: Callable[..., Any],
    timeout: float,
) -> list[object]:
    with request_open(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
    payload = json.loads(raw)
    if not isinstance(payload, list):
        raise ValueError(
            "Unexpected Socrata response payload; expected a JSON list."
        )
    return payload


def _fetch_socrata_page_json(
    request: Request,
    *,
    request_open: Callable[..., Any],
    timeout: float,
    _attempt: int = 0,
) -> list[object]:
    """Load one JSON list page with retries on transient network timeouts."""
    try:
        return _read_socrata_page_once(request, request_open, timeout)
    except (TimeoutError, URLError):
        if _attempt >= 3:
            raise
        time.sleep(min(8.0, 2.0**_attempt))
        return _fetch_socrata_page_json(
            request,
            request_open=request_open,
            timeout=timeout,
            _attempt=_attempt + 1,
        )


def iter_service_requests_from_socrata(
    socrata_config: SocrataConfig,
    *,
    filters: ServiceRequestFilter,
    request_open: Callable[..., Any],
    on_page: Callable[[int, int], None] | None = None,
) -> Iterator[ServiceRequestRecord]:
    """Yield service-request records from Socrata without holding all pages in memory.

    ``on_page`` is invoked after each successful HTTP response with
    ``(page_index, row_count_in_page)`` (0-based page index).
    """
    headers = {"Accept": "application/json"}
    if socrata_config.app_token is not None:
        headers["X-App-Token"] = socrata_config.app_token

    request_limit = socrata_config.page_size
    offset = 0
    page_count = 0

    while True:
        if (
            socrata_config.max_pages is not None
            and page_count >= socrata_config.max_pages
        ):
            break

        request_url = _build_socrata_url(socrata_config, filters, offset=offset)
        request = Request(request_url, headers=headers)
        payload = _fetch_socrata_page_json(
            request,
            request_open=request_open,
            timeout=socrata_config.request_timeout_seconds,
        )

        if on_page is not None:
            on_page(page_count, len(payload))

        if not payload:
            break

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
            yield _record_from_mapping(normalized_row, community_district_column)

        if len(payload) < request_limit:
            break
        offset += request_limit
        page_count += 1


def load_service_requests_from_socrata(
    socrata_config: SocrataConfig,
    *,
    filters: ServiceRequestFilter,
    request_open: Callable[..., Any],
) -> list[ServiceRequestRecord]:
    """Load and filter service-request records from the live Socrata API."""
    records = list(
        iter_service_requests_from_socrata(
            socrata_config, filters=filters, request_open=request_open
        )
    )
    return _apply_filters(records, filters)
