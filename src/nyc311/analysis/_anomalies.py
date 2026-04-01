"""Analytical helpers for anomaly scoring."""

from __future__ import annotations

import math
from collections import defaultdict
from importlib import import_module
from statistics import mean, pstdev

from ..models import AnalysisWindow, AnomalyResult, GeographyTopicSummary


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
