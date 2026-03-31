"""Write complaint-intelligence artifacts such as CSV tables and GeoJSON maps.

The current release includes exporters for tabular summaries, anomaly tables,
boundary-backed GeoJSON output, and markdown report cards.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypeVar

from ._tabular import (
    ANOMALY_COLUMNS,
    SERVICE_REQUEST_CSV_COLUMNS,
    TOPIC_SUMMARY_COLUMNS,
)
from .models import (
    AnomalyResult,
    BoundaryGeoJSONExport,
    ExportTarget,
    GeographyTopicSummary,
    ResolutionGapSummary,
    ServiceRequestRecord,
)


def export_geojson(data: BoundaryGeoJSONExport, target: ExportTarget) -> Path:
    """Export supported boundary-backed complaint outputs to GeoJSON."""
    if target.format != "geojson":
        raise ValueError(
            "export_geojson() currently supports only GeoJSON output. "
            f"Got format={target.format!r}."
        )

    output_path = target.output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary_by_geography = {
        summary.geography_value: summary
        for summary in data.summaries
        if summary.is_dominant_topic
    }
    features: list[dict[str, object]] = []
    for boundary in data.boundaries.features:
        summary = summary_by_geography.get(boundary.geography_value)
        properties: dict[str, object] = {
            "geography": boundary.geography,
            "geography_value": boundary.geography_value,
            **boundary.properties,
        }
        if summary is not None:
            properties.update(
                {
                    "complaint_type": summary.complaint_type,
                    "dominant_topic": summary.topic,
                    "topic_count": summary.complaint_count,
                    "geography_total_count": summary.geography_total_count,
                    "share_of_geography": round(summary.share_of_geography, 6),
                }
            )
        features.append(
            {
                "type": "Feature",
                "geometry": boundary.geometry,
                "properties": properties,
            }
        )

    feature_collection = {"type": "FeatureCollection", "features": features}
    output_path.write_text(
        json.dumps(feature_collection, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output_path


def export_topic_table(data: list[GeographyTopicSummary], target: ExportTarget) -> Path:
    """Export geography-topic summaries to a CSV file."""
    if target.format != "csv":
        raise ValueError(
            "export_topic_table() currently supports only CSV output. "
            f"Got format={target.format!r}."
        )

    output_path = target.output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=TOPIC_SUMMARY_COLUMNS,
        )
        writer.writeheader()
        for row in data:
            writer.writerow(
                {
                    "geography": row.geography,
                    "geography_value": row.geography_value,
                    "complaint_type": row.complaint_type,
                    "topic": row.topic,
                    "complaint_count": row.complaint_count,
                    "geography_total_count": row.geography_total_count,
                    "share_of_geography": f"{row.share_of_geography:.6f}",
                    "topic_rank": row.topic_rank,
                    "is_dominant_topic": str(row.is_dominant_topic).lower(),
                }
            )

    return output_path


def export_service_requests_csv(
    data: list[ServiceRequestRecord], target: ExportTarget
) -> Path:
    """Export loaded service-request records to a reproducible CSV snapshot."""
    if target.format != "csv":
        raise ValueError(
            "export_service_requests_csv() currently supports only CSV output. "
            f"Got format={target.format!r}."
        )

    output_path = target.output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=(*SERVICE_REQUEST_CSV_COLUMNS, "resolution_description"),
        )
        writer.writeheader()
        for row in data:
            writer.writerow(
                {
                    "unique_key": row.service_request_id,
                    "created_date": row.created_date.isoformat(),
                    "complaint_type": row.complaint_type,
                    "descriptor": row.descriptor,
                    "borough": row.borough,
                    "community_district": row.community_district,
                    "resolution_description": row.resolution_description or "",
                }
            )

    return output_path


def export_anomalies(data: list[AnomalyResult], target: ExportTarget) -> Path:
    """Export anomaly detections to a CSV file."""
    if target.format != "csv":
        raise ValueError(
            "export_anomalies() currently supports only CSV output. "
            f"Got format={target.format!r}."
        )

    output_path = target.output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=ANOMALY_COLUMNS,
        )
        writer.writeheader()
        for row in data:
            writer.writerow(
                {
                    "geography": row.geography,
                    "geography_value": row.geography_value,
                    "complaint_type": row.complaint_type,
                    "topic": row.topic,
                    "complaint_count": row.complaint_count,
                    "geography_total_count": row.geography_total_count,
                    "share_of_geography": f"{row.share_of_geography:.6f}",
                    "topic_rank": row.topic_rank,
                    "z_score": f"{row.z_score:.6f}",
                    "is_anomaly": str(row.is_anomaly).lower(),
                    "window_days": row.window_days,
                    "anomaly_threshold": f"{row.anomaly_threshold:.6f}",
                }
            )

    return output_path


def export_report_card(data: object, target: ExportTarget) -> Path:
    """Export a markdown report card from summaries, gaps, and anomalies."""
    if target.format not in {"md", "markdown"}:
        raise ValueError(
            "export_report_card() currently supports only markdown output. "
            f"Got format={target.format!r}."
        )

    topic_summaries, resolution_gaps, anomalies = _coerce_report_card_data(data)
    output_path = target.output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    geographies = sorted(
        {
            *[summary.geography_value for summary in topic_summaries],
            *[gap.geography_value for gap in resolution_gaps],
            *[anomaly.geography_value for anomaly in anomalies],
        }
    )
    dominant_topics_by_geography: dict[str, list[GeographyTopicSummary]] = {}
    for summary in topic_summaries:
        if summary.is_dominant_topic:
            dominant_topics_by_geography.setdefault(summary.geography_value, []).append(
                summary
            )
    gaps_by_geography: dict[str, list[ResolutionGapSummary]] = {}
    for gap in resolution_gaps:
        gaps_by_geography.setdefault(gap.geography_value, []).append(gap)
    anomalies_by_geography: dict[str, list[AnomalyResult]] = {}
    for anomaly in anomalies:
        anomalies_by_geography.setdefault(anomaly.geography_value, []).append(anomaly)

    sections = ["# NYC311 Report Card", ""]
    for geography_value in geographies:
        sections.append(f"## {geography_value}")
        sections.append("")

        dominant_topics = sorted(
            dominant_topics_by_geography.get(geography_value, []),
            key=lambda summary: (
                -summary.geography_total_count,
                summary.complaint_type,
            ),
        )
        if dominant_topics:
            sections.append("Dominant topic")
            sections.extend(
                [
                    f"- {dominant_topic.complaint_type}: {dominant_topic.topic} "
                    f"({dominant_topic.complaint_count}/{dominant_topic.geography_total_count}, "
                    f"{dominant_topic.share_of_geography:.1%})"
                    for dominant_topic in dominant_topics[:5]
                ]
            )
        else:
            sections.append("Dominant topic")
            sections.append("- No topic summaries available.")
        sections.append("")

        sections.append("Resolution overview")
        geography_gaps = sorted(
            gaps_by_geography.get(geography_value, []),
            key=lambda gap: (-gap.total_request_count, gap.complaint_type),
        )
        if geography_gaps:
            sections.extend(
                [
                    f"- {gap.complaint_type}: resolution rate {gap.resolution_rate:.1%}, "
                    f"unresolved {gap.unresolved_request_count}/{gap.total_request_count}"
                    for gap in geography_gaps[:5]
                ]
            )
        else:
            sections.append("- No resolution gap summaries available.")
        sections.append("")

        sections.append("Anomaly flags")
        flagged_anomalies = [
            anomaly
            for anomaly in sorted(
                anomalies_by_geography.get(geography_value, []),
                key=lambda anomaly: (
                    -abs(anomaly.z_score),
                    anomaly.topic_rank,
                    anomaly.topic,
                ),
            )
            if anomaly.is_anomaly
        ]
        if flagged_anomalies:
            sections.extend(
                [
                    f"- {anomaly.complaint_type} / {anomaly.topic}: "
                    f"count={anomaly.complaint_count}, z={anomaly.z_score:.2f}"
                    for anomaly in flagged_anomalies[:5]
                ]
            )
        else:
            sections.append("- No anomaly flags above the configured threshold.")
        sections.append("")

    output_path.write_text("\n".join(sections).rstrip() + "\n", encoding="utf-8")
    return output_path


def _coerce_report_card_data(
    data: object,
) -> tuple[
    list[GeographyTopicSummary], list[ResolutionGapSummary], list[AnomalyResult]
]:
    if not isinstance(data, Mapping):
        raise TypeError(
            "export_report_card() expects a mapping with topic_summaries, "
            "resolution_gaps, and optional anomalies."
        )

    raw_topic_summaries = data.get("topic_summaries", ())
    raw_resolution_gaps = data.get("resolution_gaps", ())
    raw_anomalies = data.get("anomalies", ())

    topic_summaries = _coerce_sequence(
        raw_topic_summaries,
        GeographyTopicSummary,
        field_name="topic_summaries",
    )
    resolution_gaps = _coerce_sequence(
        raw_resolution_gaps,
        ResolutionGapSummary,
        field_name="resolution_gaps",
    )
    anomalies = _coerce_sequence(
        raw_anomalies,
        AnomalyResult,
        field_name="anomalies",
    )
    return topic_summaries, resolution_gaps, anomalies


T = TypeVar("T")


def _coerce_sequence(
    value: object,
    expected_type: type[T],
    *,
    field_name: str,
) -> list[T]:
    if not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a sequence.")
    if any(not isinstance(item, expected_type) for item in value):
        raise TypeError(
            f"{field_name} must contain only {expected_type.__name__} instances."
        )
    return list(value)
