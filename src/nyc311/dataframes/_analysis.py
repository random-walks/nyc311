"""Analysis-shaped dataframe conversions for nyc311 models."""

from __future__ import annotations

from typing import Any

from ..export._tabular import (
    ANOMALY_COLUMNS,
    RESOLUTION_GAP_COLUMNS,
    TOPIC_COVERAGE_COLUMNS,
    TOPIC_SUMMARY_COLUMNS,
)
from ..models import (
    AnomalyResult,
    GeographyTopicSummary,
    ResolutionGapSummary,
    TopicCoverageReport,
)
from ._pandas import require_pandas


def summaries_to_dataframe(summaries: list[GeographyTopicSummary]) -> Any:
    """Convert geography-topic summaries into a DataFrame."""
    pd = require_pandas()
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
        columns=TOPIC_SUMMARY_COLUMNS,
    )


def gaps_to_dataframe(gaps: list[ResolutionGapSummary]) -> Any:
    """Convert resolution-gap summaries into a DataFrame."""
    pd = require_pandas()
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
        columns=RESOLUTION_GAP_COLUMNS,
    )


def anomalies_to_dataframe(anomalies: list[AnomalyResult]) -> Any:
    """Convert anomaly results into a DataFrame."""
    pd = require_pandas()
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
        columns=ANOMALY_COLUMNS,
    )


def coverage_to_dataframe(reports: list[TopicCoverageReport]) -> Any:
    """Convert topic-coverage reports into a DataFrame."""
    pd = require_pandas()
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
        columns=TOPIC_COVERAGE_COLUMNS,
    )
