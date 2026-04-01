"""High-level workflow helpers for live fetching and topic-analysis pipelines."""

from __future__ import annotations

from pathlib import Path

from .analysis import aggregate_by_geography, extract_topics
from .export import export_geojson, export_service_requests_csv, export_topic_table
from .geographies import load_boundaries
from .io import load_service_requests
from .models import (
    BoundaryGeoJSONExport,
    ExportTarget,
    GeographyTopicSummary,
    ServiceRequestFilter,
    ServiceRequestRecord,
    SocrataConfig,
    TopicQuery,
)


def fetch_service_requests(
    *,
    filters: ServiceRequestFilter | None = None,
    socrata_config: SocrataConfig | None = None,
    output: str | Path | None = None,
) -> list[ServiceRequestRecord]:
    """Fetch a live Socrata slice into memory and optionally stage it as CSV.

    This is the intended SDK helper for notebook and workflow users who want to
    fetch once, inspect records in memory, and only export a local snapshot when
    they decide the filtered slice is worth keeping.
    """
    records = load_service_requests(
        socrata_config or SocrataConfig(),
        filters=filters,
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


__all__ = [
    "fetch_service_requests",
    "run_topic_pipeline",
]
