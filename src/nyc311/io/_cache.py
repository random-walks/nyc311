"""Deterministic on-disk CSV caching for large Socrata fetches."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from ..export._tabular import SERVICE_REQUEST_EXPORT_COLUMNS
from ..models import ServiceRequestFilter, ServiceRequestRecord, SocrataConfig
from ._filters import record_matches_service_request_filter
from ._socrata import iter_service_requests_from_socrata

_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def _partial_cache_path(output_path: Path) -> Path:
    """While streaming, rows are written here; renamed to ``output_path`` when done."""
    return output_path.with_name(output_path.name + ".part")


def _slug(text: str, *, max_len: int = 80) -> str:
    lowered = text.strip().lower()
    slug = _SLUG_PATTERN.sub("_", lowered).strip("_")
    return slug[:max_len] if slug else "x"


def cache_path_for_request(
    socrata_config: SocrataConfig,
    filters: ServiceRequestFilter,
    cache_dir: Path,
) -> Path:
    """Return the deterministic CSV path for a Socrata config + filter pair."""
    start = filters.start_date.isoformat() if filters.start_date else "none"
    end = filters.end_date.isoformat() if filters.end_date else "none"
    page = socrata_config.page_size
    sort_suffix = "_desc" if socrata_config.created_date_sort == "desc" else ""

    if filters.geography is None and not filters.complaint_types:
        name = f"all_{start}_{end}_{page}{sort_suffix}.csv"
        return cache_dir / name

    borough = "all"
    if filters.geography is not None and filters.geography.geography == "borough":
        borough = _slug(filters.geography.value)

    complaint_types = filters.complaint_types
    if not complaint_types:
        ct_slug = "all"
    elif len(complaint_types) == 1:
        ct_slug = _slug(complaint_types[0])
    else:
        joined = "_".join(sorted(_slug(c) for c in complaint_types))
        ct_slug = joined[:120]

    name = f"{borough}_{ct_slug}_{start}_{end}_{page}{sort_suffix}.csv"
    return cache_dir / name


def _write_record_row(
    writer: csv.DictWriter[str], record: ServiceRequestRecord
) -> None:
    writer.writerow(
        {
            "unique_key": record.service_request_id,
            "created_date": record.created_date.isoformat(),
            "complaint_type": record.complaint_type,
            "descriptor": record.descriptor,
            "borough": record.borough,
            "community_district": record.community_district,
            "resolution_description": record.resolution_description or "",
            "latitude": "" if record.latitude is None else str(record.latitude),
            "longitude": "" if record.longitude is None else str(record.longitude),
        }
    )


def cached_fetch(
    socrata_config: SocrataConfig,
    filters: ServiceRequestFilter,
    *,
    cache_dir: Path,
    refresh: bool = False,
    request_open: Callable[..., Any] | None = None,
    max_records: int | None = None,
    on_page: Callable[[int, int], None] | None = None,
) -> Path:
    """Stream a Socrata query to a CSV file under ``cache_dir``; return the path.

    Skips the network fetch when the file already exists and ``refresh`` is False.
    Rows are filtered with the same rules as :func:`load_service_requests_from_socrata`.

    For multi-gigabyte extracts, prefer this function and analyze with chunked
    ``pandas.read_csv`` instead of loading via :func:`load_service_requests`, which
    materializes rows in memory.

    Optional ``on_page`` is forwarded to :func:`nyc311.io.iter_service_requests_from_socrata`
    for per-HTTP-page progress (page index and row count for that page).
    """
    opener = urlopen if request_open is None else request_open
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    output_path = cache_path_for_request(socrata_config, filters, cache_dir)
    partial_path = _partial_cache_path(output_path)

    if output_path.is_file() and not refresh:
        return output_path

    if refresh:
        if output_path.is_file():
            output_path.unlink()
        if partial_path.is_file():
            partial_path.unlink()
    elif partial_path.is_file() and not output_path.is_file():
        # Interrupted previous run left a partial file; do not treat as complete.
        partial_path.unlink()

    written = 0
    try:
        with partial_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=SERVICE_REQUEST_EXPORT_COLUMNS)
            writer.writeheader()
            for record in iter_service_requests_from_socrata(
                socrata_config,
                filters=filters,
                request_open=opener,
                on_page=on_page,
            ):
                if not record_matches_service_request_filter(record, filters):
                    continue
                _write_record_row(writer, record)
                written += 1
                if max_records is not None and written >= max_records:
                    break
        partial_path.replace(output_path)
    except BaseException:
        if partial_path.is_file():
            partial_path.unlink()
        raise

    _write_meta(output_path, written, socrata_config, filters)
    return output_path


def _write_meta(
    csv_path: Path,
    record_count: int,
    socrata_config: SocrataConfig,
    filters: ServiceRequestFilter,
) -> None:
    """Write a ``.meta.json`` sidecar with download integrity metadata."""
    sha256 = hashlib.sha256()
    with csv_path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            sha256.update(chunk)

    meta = {
        "record_count": record_count,
        "sha256": sha256.hexdigest(),
        "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
        "start_date": filters.start_date.isoformat() if filters.start_date else None,
        "end_date": filters.end_date.isoformat() if filters.end_date else None,
        "borough": (
            filters.geography.value
            if filters.geography and filters.geography.geography == "borough"
            else None
        ),
        "complaint_types": list(filters.complaint_types),
        "page_size": socrata_config.page_size,
    }
    meta_path = csv_path.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


__all__ = ["cache_path_for_request", "cached_fetch"]
