"""Implemented and planned exporters for complaint-intelligence outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from ._not_implemented import planned_surface
from .models import (
    BoundaryGeoJSONExport,
    ExportTarget,
    GeographyTopicSummary,
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
            fieldnames=(
                "geography",
                "geography_value",
                "complaint_type",
                "topic",
                "complaint_count",
                "geography_total_count",
                "share_of_geography",
                "topic_rank",
                "is_dominant_topic",
            ),
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


def export_anomalies(data: object, target: ExportTarget) -> object:
    """Export anomaly detections for downstream reporting."""
    del data, target
    planned_surface("export_anomalies()")


def export_report_card(data: object, target: ExportTarget) -> object:
    """Export a neighborhood report-card style artifact."""
    del data, target
    planned_surface("export_report_card()")
