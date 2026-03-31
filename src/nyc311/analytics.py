"""Analytical helpers for anomaly scoring and resolution-gap summaries."""

from __future__ import annotations

import math
from collections import defaultdict
from importlib import import_module
from statistics import mean, pstdev

from .models import (
    AnalysisWindow,
    AnomalyResult,
    GeographyTopicSummary,
    ResolutionGapSummary,
    ServiceRequestRecord,
)


def detect_anomalies(
    aggregated_data: list[GeographyTopicSummary],
    window: AnalysisWindow,
    *,
    z_threshold: float = 2.0,
) -> list[AnomalyResult]:
    """Score unusually high or low aggregated topic counts via z-scores."""
    if z_threshold <= 0:
        raise ValueError("z_threshold must be positive.")
    if not aggregated_data:
        return []

    grouped_summaries: dict[tuple[str, str], list[GeographyTopicSummary]] = defaultdict(
        list
    )
    for summary in aggregated_data:
        grouped_summaries[(summary.geography, summary.complaint_type)].append(summary)

    anomaly_results: list[AnomalyResult] = []
    for summaries in grouped_summaries.values():
        ordered_summaries = sorted(
            summaries,
            key=lambda summary: (
                summary.geography_value,
                summary.topic_rank,
                summary.topic,
            ),
        )
        z_scores = _compute_z_scores(
            [summary.complaint_count for summary in ordered_summaries]
        )
        for summary, z_score in zip(ordered_summaries, z_scores, strict=True):
            anomaly_results.append(
                AnomalyResult(
                    geography=summary.geography,
                    geography_value=summary.geography_value,
                    complaint_type=summary.complaint_type,
                    topic=summary.topic,
                    complaint_count=summary.complaint_count,
                    geography_total_count=summary.geography_total_count,
                    share_of_geography=summary.share_of_geography,
                    topic_rank=summary.topic_rank,
                    z_score=z_score,
                    is_anomaly=abs(z_score) >= z_threshold,
                    window_days=window.days,
                    anomaly_threshold=z_threshold,
                )
            )

    return sorted(
        anomaly_results,
        key=lambda result: (
            -abs(result.z_score),
            result.geography,
            result.complaint_type,
            result.geography_value,
            result.topic_rank,
            result.topic,
        ),
    )


def _compute_z_scores(values: list[int]) -> list[float]:
    if len(values) < 2:
        return [0.0 for _value in values]

    try:
        zscore = import_module("scipy.stats").zscore
    except ImportError:
        average = mean(values)
        std_dev = pstdev(values)
        if std_dev == 0:
            return [0.0 for _value in values]
        return [(value - average) / std_dev for value in values]

    z_scores = zscore(values)
    return [0.0 if math.isnan(float(score)) else float(score) for score in z_scores]


def analyze_resolution_gaps(
    service_requests: list[ServiceRequestRecord],
    resolution_data: list[ServiceRequestRecord],
) -> list[ResolutionGapSummary]:
    """Summarize unresolved complaint share by borough and complaint type."""
    if not service_requests:
        return []

    resolved_request_ids = {
        record.service_request_id
        for record in resolution_data
        if record.resolution_description is not None
    }
    grouped_totals: dict[tuple[str, str], int] = defaultdict(int)
    grouped_resolved: dict[tuple[str, str], int] = defaultdict(int)

    for record in service_requests:
        grouping_key = (record.borough, record.complaint_type)
        grouped_totals[grouping_key] += 1
        if (
            record.resolution_description is not None
            or record.service_request_id in resolved_request_ids
        ):
            grouped_resolved[grouping_key] += 1

    summaries: list[ResolutionGapSummary] = []
    for (borough, complaint_type), total_request_count in sorted(
        grouped_totals.items()
    ):
        resolved_request_count = grouped_resolved[(borough, complaint_type)]
        unresolved_request_count = total_request_count - resolved_request_count
        summaries.append(
            ResolutionGapSummary(
                geography="borough",
                geography_value=borough,
                complaint_type=complaint_type,
                total_request_count=total_request_count,
                resolved_request_count=resolved_request_count,
                unresolved_request_count=unresolved_request_count,
                unresolved_share=unresolved_request_count / total_request_count,
                resolution_rate=resolved_request_count / total_request_count,
            )
        )

    return sorted(
        summaries,
        key=lambda summary: (
            -summary.unresolved_share,
            -summary.total_request_count,
            summary.geography_value,
            summary.complaint_type,
        ),
    )
