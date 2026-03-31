"""Shared tabular schemas for CSV exports and dataframe helpers."""

from __future__ import annotations

from typing import Final

COMMON_COMPLAINT_RECORD_COLUMNS: Final[tuple[str, ...]] = (
    "created_date",
    "complaint_type",
    "descriptor",
    "borough",
    "community_district",
)

SERVICE_REQUEST_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "unique_key",
    *COMMON_COMPLAINT_RECORD_COLUMNS,
)

SERVICE_REQUEST_DATAFRAME_COLUMNS: Final[tuple[str, ...]] = (
    "service_request_id",
    *COMMON_COMPLAINT_RECORD_COLUMNS,
    "resolution_description",
)

TOPIC_ASSIGNMENT_COLUMNS: Final[tuple[str, ...]] = (
    *SERVICE_REQUEST_DATAFRAME_COLUMNS,
    "topic",
    "normalized_text",
)

TOPIC_SUMMARY_COLUMNS: Final[tuple[str, ...]] = (
    "geography",
    "geography_value",
    "complaint_type",
    "topic",
    "complaint_count",
    "geography_total_count",
    "share_of_geography",
    "topic_rank",
    "is_dominant_topic",
)

RESOLUTION_GAP_COLUMNS: Final[tuple[str, ...]] = (
    "geography",
    "geography_value",
    "complaint_type",
    "total_request_count",
    "resolved_request_count",
    "unresolved_request_count",
    "unresolved_share",
    "resolution_rate",
)

ANOMALY_COLUMNS: Final[tuple[str, ...]] = (
    "geography",
    "geography_value",
    "complaint_type",
    "topic",
    "complaint_count",
    "geography_total_count",
    "share_of_geography",
    "topic_rank",
    "z_score",
    "is_anomaly",
    "window_days",
    "anomaly_threshold",
)

TOPIC_COVERAGE_COLUMNS: Final[tuple[str, ...]] = (
    "complaint_type",
    "total_records",
    "matched_records",
    "other_records",
    "coverage_rate",
    "top_unmatched_descriptors",
)
