"""CSV exporters for nyc311 artifacts."""

from __future__ import annotations

import csv
from pathlib import Path

from ..models import (
    AnomalyResult,
    ExportTarget,
    GeographyTopicSummary,
    ServiceRequestRecord,
)
from ._tabular import (
    ANOMALY_COLUMNS,
    SERVICE_REQUEST_EXPORT_COLUMNS,
    TOPIC_SUMMARY_COLUMNS,
)


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
            fieldnames=SERVICE_REQUEST_EXPORT_COLUMNS,
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
                    "closed_date": (
                        "" if row.closed_date is None else row.closed_date.isoformat()
                    ),
                    "latitude": "" if row.latitude is None else row.latitude,
                    "longitude": "" if row.longitude is None else row.longitude,
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
