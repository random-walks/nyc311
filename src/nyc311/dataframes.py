"""Optional pandas conversion helpers for notebook and data-science workflows."""

from __future__ import annotations

from datetime import date
from importlib import import_module
from typing import TYPE_CHECKING, Any

from .models import (
    AnomalyResult,
    GeographyTopicSummary,
    ResolutionGapSummary,
    ServiceRequestRecord,
    TopicAssignment,
    TopicCoverageReport,
)

if TYPE_CHECKING:
    import pandas as pd  # type: ignore[import-untyped]


def _require_pandas() -> Any:
    try:
        return import_module("pandas")
    except ImportError as exc:  # pragma: no cover - exercised in tests via monkeypatch
        raise ImportError(
            "pandas is required for nyc311.dataframes helpers. Install it with "
            "`pip install nyc311[dataframes]`, `pip install nyc311[science]`, "
            "or `pip install pandas`."
        ) from exc


def records_to_dataframe(records: list[ServiceRequestRecord]) -> pd.DataFrame:
    """Convert service-request records into a notebook-friendly DataFrame."""
    pd = _require_pandas()
    dataframe = pd.DataFrame.from_records(
        [
            {
                "service_request_id": record.service_request_id,
                "created_date": record.created_date,
                "complaint_type": record.complaint_type,
                "descriptor": record.descriptor,
                "borough": record.borough,
                "community_district": record.community_district,
                "resolution_description": record.resolution_description,
            }
            for record in records
        ],
        columns=(
            "service_request_id",
            "created_date",
            "complaint_type",
            "descriptor",
            "borough",
            "community_district",
            "resolution_description",
        ),
    )
    if "created_date" in dataframe:
        dataframe["created_date"] = pd.to_datetime(dataframe["created_date"])
    return dataframe


def dataframe_to_records(dataframe: pd.DataFrame) -> list[ServiceRequestRecord]:
    """Convert a DataFrame back into typed service-request records."""
    required_columns = {
        "service_request_id",
        "created_date",
        "complaint_type",
        "descriptor",
        "borough",
        "community_district",
    }
    missing_columns = sorted(required_columns.difference(dataframe.columns))
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(
            f"DataFrame is missing required service-request columns: {missing}."
        )

    records: list[ServiceRequestRecord] = []
    for row in dataframe.to_dict(orient="records"):
        raw_created_date = row["created_date"]
        if hasattr(raw_created_date, "to_pydatetime"):
            created_date = raw_created_date.to_pydatetime().date()
        elif isinstance(raw_created_date, date):
            created_date = raw_created_date
        else:
            created_date = date.fromisoformat(str(raw_created_date))

        resolution_description = row.get("resolution_description")
        normalized_resolution = (
            None
            if resolution_description in (None, "")
            else str(resolution_description)
        )
        records.append(
            ServiceRequestRecord(
                service_request_id=str(row["service_request_id"]),
                created_date=created_date,
                complaint_type=str(row["complaint_type"]),
                descriptor=str(row["descriptor"]),
                borough=str(row["borough"]),
                community_district=str(row["community_district"]),
                resolution_description=normalized_resolution,
            )
        )
    return records


def assignments_to_dataframe(assignments: list[TopicAssignment]) -> pd.DataFrame:
    """Convert topic assignments into a DataFrame."""
    pd = _require_pandas()
    dataframe = pd.DataFrame.from_records(
        [
            {
                "service_request_id": assignment.record.service_request_id,
                "created_date": assignment.record.created_date,
                "complaint_type": assignment.record.complaint_type,
                "descriptor": assignment.record.descriptor,
                "borough": assignment.record.borough,
                "community_district": assignment.record.community_district,
                "resolution_description": assignment.record.resolution_description,
                "topic": assignment.topic,
                "normalized_text": assignment.normalized_text,
            }
            for assignment in assignments
        ],
        columns=(
            "service_request_id",
            "created_date",
            "complaint_type",
            "descriptor",
            "borough",
            "community_district",
            "resolution_description",
            "topic",
            "normalized_text",
        ),
    )
    if "created_date" in dataframe:
        dataframe["created_date"] = pd.to_datetime(dataframe["created_date"])
    return dataframe


def summaries_to_dataframe(
    summaries: list[GeographyTopicSummary],
) -> pd.DataFrame:
    """Convert geography-topic summaries into a DataFrame."""
    pd = _require_pandas()
    return pd.DataFrame.from_records(
        [
            {
                "geography": summary.geography,
                "geography_value": summary.geography_value,
                "complaint_type": summary.complaint_type,
                "topic": summary.topic,
                "complaint_count": summary.complaint_count,
                "geography_total_count": summary.geography_total_count,
                "share_of_geography": summary.share_of_geography,
                "topic_rank": summary.topic_rank,
                "is_dominant_topic": summary.is_dominant_topic,
            }
            for summary in summaries
        ],
        columns=(
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


def gaps_to_dataframe(gaps: list[ResolutionGapSummary]) -> pd.DataFrame:
    """Convert resolution-gap summaries into a DataFrame."""
    pd = _require_pandas()
    return pd.DataFrame.from_records(
        [
            {
                "geography": gap.geography,
                "geography_value": gap.geography_value,
                "complaint_type": gap.complaint_type,
                "total_request_count": gap.total_request_count,
                "resolved_request_count": gap.resolved_request_count,
                "unresolved_request_count": gap.unresolved_request_count,
                "unresolved_share": gap.unresolved_share,
                "resolution_rate": gap.resolution_rate,
            }
            for gap in gaps
        ],
        columns=(
            "geography",
            "geography_value",
            "complaint_type",
            "total_request_count",
            "resolved_request_count",
            "unresolved_request_count",
            "unresolved_share",
            "resolution_rate",
        ),
    )


def anomalies_to_dataframe(anomalies: list[AnomalyResult]) -> pd.DataFrame:
    """Convert anomaly results into a DataFrame."""
    pd = _require_pandas()
    return pd.DataFrame.from_records(
        [
            {
                "geography": anomaly.geography,
                "geography_value": anomaly.geography_value,
                "complaint_type": anomaly.complaint_type,
                "topic": anomaly.topic,
                "complaint_count": anomaly.complaint_count,
                "geography_total_count": anomaly.geography_total_count,
                "share_of_geography": anomaly.share_of_geography,
                "topic_rank": anomaly.topic_rank,
                "z_score": anomaly.z_score,
                "is_anomaly": anomaly.is_anomaly,
                "window_days": anomaly.window_days,
                "anomaly_threshold": anomaly.anomaly_threshold,
            }
            for anomaly in anomalies
        ],
        columns=(
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
        ),
    )


def coverage_to_dataframe(
    reports: list[TopicCoverageReport],
) -> pd.DataFrame:
    """Convert topic-coverage reports into a DataFrame."""
    pd = _require_pandas()
    return pd.DataFrame.from_records(
        [
            {
                "complaint_type": report.complaint_type,
                "total_records": report.total_records,
                "matched_records": report.matched_records,
                "other_records": report.other_records,
                "coverage_rate": report.coverage_rate,
                "top_unmatched_descriptors": list(report.top_unmatched_descriptors),
            }
            for report in reports
        ],
        columns=(
            "complaint_type",
            "total_records",
            "matched_records",
            "other_records",
            "coverage_rate",
            "top_unmatched_descriptors",
        ),
    )
