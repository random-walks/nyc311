"""Markdown report exporter for nyc311 artifacts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypeVar

from ..models import (
    AnomalyResult,
    ExportTarget,
    GeographyTopicSummary,
    ResolutionGapSummary,
)


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
