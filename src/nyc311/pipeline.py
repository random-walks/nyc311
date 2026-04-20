"""High-level workflow helpers for live fetching and topic-analysis pipelines."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path

from .analysis import aggregate_by_geography, extract_topics
from .export import export_geojson, export_service_requests_csv, export_topic_table
from .geographies import load_boundaries
from .io import load_service_requests
from .io._cache import cached_fetch
from .models import (
    BoundaryGeoJSONExport,
    ExportTarget,
    GeographyFilter,
    GeographyTopicSummary,
    ServiceRequestFilter,
    ServiceRequestRecord,
    SocrataConfig,
    TopicQuery,
)
from .models._constants import SUPPORTED_BOROUGHS
from .presets import large_socrata_config


def fetch_service_requests(
    *,
    filters: ServiceRequestFilter | None = None,
    socrata_config: SocrataConfig | None = None,
    output: str | Path | None = None,
    cache_dir: Path | str | None = None,
    refresh: bool = False,
    max_cached_records: int | None = None,
) -> list[ServiceRequestRecord]:
    """Fetch a live Socrata slice into memory and optionally stage it as CSV.

    This is the intended SDK helper for notebook and workflow users who want to
    fetch once, inspect records in memory, and only export a local snapshot when
    they decide the filtered slice is worth keeping.

    When ``cache_dir`` is set, responses are streamed to a CSV cache first (see
    :func:`nyc311.io.cached_fetch`), then loaded—avoid huge slices unless you use
    chunked analysis on the cache file.
    """
    records = load_service_requests(
        socrata_config or SocrataConfig(),
        filters=filters,
        cache_dir=cache_dir,
        refresh=refresh,
        max_cached_records=max_cached_records,
    )
    if output is not None:
        export_service_requests_csv(
            records,
            ExportTarget(format="csv", output_path=Path(output)),
        )
    return records


def run_topic_pipeline(
    source: str | Path | SocrataConfig,
    complaint_type: str,
    *,
    geography: str = "community_district",
    filters: ServiceRequestFilter | None = None,
    top_n: int = 20,
    output: str | Path | None = None,
    output_format: str = "csv",
    boundaries: str | Path | None = None,
) -> list[GeographyTopicSummary]:
    """Run the implemented load-extract-aggregate-export topic workflow.

    When ``output`` is provided, this helper also writes either a CSV or GeoJSON
    artifact using the same behavior exposed by the current CLI. The aggregated
    summaries are always returned to support notebook and workflow use cases.
    """
    service_request_filter = ServiceRequestFilter(
        start_date=filters.start_date if filters is not None else None,
        end_date=filters.end_date if filters is not None else None,
        geography=filters.geography if filters is not None else None,
        complaint_types=(complaint_type,),
    )
    records = load_service_requests(source, filters=service_request_filter)
    assignments = extract_topics(
        records,
        TopicQuery(complaint_type=complaint_type, top_n=top_n),
    )
    summaries = aggregate_by_geography(assignments, geography=geography)

    if output is None:
        return summaries

    target = ExportTarget(format=output_format, output_path=Path(output))
    if target.format == "csv":
        export_topic_table(summaries, target)
        return summaries
    if target.format != "geojson":
        raise ValueError(
            "run_topic_pipeline() currently supports only csv and geojson output. "
            f"Got format={target.format!r}."
        )
    if boundaries is None:
        raise ValueError(
            "run_topic_pipeline() requires boundaries when format='geojson'."
        )

    boundary_collection = load_boundaries(boundaries)
    export_geojson(
        BoundaryGeoJSONExport(
            boundaries=boundary_collection, summaries=tuple(summaries)
        ),
        target,
    )
    return summaries


def bulk_fetch(
    *,
    complaint_types: tuple[str, ...] = (),
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    cache_dir: Path | str = Path("data/cache"),
    boroughs: tuple[str, ...] | None = None,
    app_token: str | None = None,
    page_size: int = 5_000,
    on_progress: Callable[[str, int, int], None] | None = None,
) -> list[Path]:
    """Fetch full-city 311 data split by borough for manageable file sizes.

    Downloads are split per-borough so that each CSV stays under a few
    hundred megabytes. Files are written to ``cache_dir`` with
    deterministic names; subsequent calls skip any borough whose file
    already exists. Each completed CSV is paired with a ``.meta.json``
    sidecar containing the row count, SHA-256 checksum, fetch
    timestamp, and the filter parameters used.

    The Socrata ``$select`` fragment requests the schema:
    ``unique_key, created_date, closed_date, complaint_type,
    descriptor, borough, community_board, resolution_description,
    latitude, longitude``. ``closed_date`` (added in v1.0.1 per
    random-walks/nyc311#20) is nullable — unresolved complaints
    serialize it as an empty column — which lets downstream
    resolution-time / SLA analyses compute
    ``closed_date - created_date`` directly without a second
    round-trip.

    Args:
        complaint_types: Optional whitelist of complaint types. When
            empty, every complaint type is included.
        start_date: Inclusive lower bound on ``created_date``. Accepts a
            ``datetime.date`` or an ISO-8601 string.
        end_date: Inclusive upper bound on ``created_date``. Accepts a
            ``datetime.date`` or an ISO-8601 string.
        cache_dir: Directory to write per-borough CSV files into. The
            directory is created on demand.
        boroughs: Boroughs to include. Defaults to all five.
        app_token: Socrata app token for higher rate limits.
        page_size: Rows per Socrata HTTP request.
        on_progress: Optional callback invoked after each HTTP page as
            ``on_progress(borough, page_index, page_row_count)``.

    Returns:
        Paths to the completed per-borough CSV files in the order the
        boroughs were processed.
    """
    target_boroughs = boroughs or SUPPORTED_BOROUGHS
    cache_path = Path(cache_dir)

    parsed_start = (
        date.fromisoformat(start_date) if isinstance(start_date, str) else start_date
    )
    parsed_end = date.fromisoformat(end_date) if isinstance(end_date, str) else end_date

    config = large_socrata_config(
        page_size=page_size,
        app_token=app_token,
    )

    paths: list[Path] = []
    for borough_name in target_boroughs:
        filters = ServiceRequestFilter(
            start_date=parsed_start,
            end_date=parsed_end,
            geography=GeographyFilter(geography="borough", value=borough_name),
            complaint_types=complaint_types,
        )

        def _on_page(page_idx: int, row_count: int, _boro: str = borough_name) -> None:
            if on_progress is not None:
                on_progress(_boro, page_idx, row_count)

        result_path = cached_fetch(
            config,
            filters,
            cache_dir=cache_path,
            on_page=_on_page,
        )
        paths.append(result_path)

    return paths


__all__ = [
    "bulk_fetch",
    "fetch_service_requests",
    "run_topic_pipeline",
]
