"""Implemented and planned processing steps for complaint intelligence workflows."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Final

from ._not_implemented import planned_surface
from .models import (
    AnalysisWindow,
    GeographyTopicSummary,
    ServiceRequestRecord,
    TopicAssignment,
    TopicQuery,
)

_SUPPORTED_TOPIC_RULES: Final[dict[str, tuple[tuple[str, tuple[str, ...]], ...]]] = {
    "Noise - Residential": (
        ("party_music", ("party", "music", "speakers", "stereo", "bass", "television")),
        ("construction", ("construction", "drilling", "jackhammer")),
        ("pet_noise", ("dog", "barking", "pet")),
        ("banging", ("banging", "thumping", "shaking", "arguing", "hammering")),
    ),
    "Rodent": (
        ("extermination_request", ("exterminator", "extermination", "infestation")),
        ("rats_seen", ("rats", "rat", "trash bags")),
        ("mouse_condition", ("mouse", "mice", "droppings")),
    ),
}
_TEXT_NORMALIZATION_PATTERN: Final[re.Pattern[str]] = re.compile(r"[^a-z0-9]+")


def _normalize_text(value: str) -> str:
    """Normalize complaint text for deterministic rule matching."""
    stripped = value.strip().lower()
    normalized = _TEXT_NORMALIZATION_PATTERN.sub(" ", stripped)
    return " ".join(normalized.split())


def _matches_keyword(normalized_text: str, keyword: str) -> bool:
    """Return whether a normalized text contains a normalized keyword."""
    if " " in keyword:
        return keyword in normalized_text
    return keyword in normalized_text.split()


def extract_topics(
    service_requests: list[ServiceRequestRecord], query: TopicQuery
) -> list[TopicAssignment]:
    """Extract deterministic first-pass topics for one supported complaint type."""
    complaint_type = query.complaint_type
    if complaint_type not in _SUPPORTED_TOPIC_RULES:
        supported_types = ", ".join(sorted(_SUPPORTED_TOPIC_RULES))
        raise NotImplementedError(
            "extract_topics() currently supports only documented v0.1 complaint types. "
            f"Supported types: {supported_types}. "
            f"Got: {complaint_type!r}."
        )

    rules = _SUPPORTED_TOPIC_RULES[complaint_type]
    topic_assignments: list[TopicAssignment] = []

    for record in service_requests:
        if record.complaint_type != complaint_type:
            continue

        normalized_text = _normalize_text(record.descriptor)
        matched_topic = "other"

        for topic, keywords in rules:
            if any(_matches_keyword(normalized_text, keyword) for keyword in keywords):
                matched_topic = topic
                break

        topic_assignments.append(
            TopicAssignment(
                record=record,
                topic=matched_topic,
                normalized_text=normalized_text,
            )
        )

    if not topic_assignments:
        return []

    topic_frequencies = Counter(assignment.topic for assignment in topic_assignments)
    allowed_topics = {
        topic for topic, _count in topic_frequencies.most_common(query.top_n)
    }
    return [
        assignment
        for assignment in topic_assignments
        if assignment.topic in allowed_topics
    ]


def aggregate_by_geography(
    topic_assignments: list[TopicAssignment],
    geography: str,
) -> list[GeographyTopicSummary]:
    """Aggregate deterministic topic assignments into supported geographies."""
    if not topic_assignments:
        return []

    grouped_counts: dict[tuple[str, str, str], int] = defaultdict(int)
    geography_totals: dict[tuple[str, str], int] = defaultdict(int)

    for assignment in topic_assignments:
        geography_value = assignment.record.geography_value(geography)
        complaint_type = assignment.record.complaint_type
        grouped_counts[(geography_value, complaint_type, assignment.topic)] += 1
        geography_totals[(geography_value, complaint_type)] += 1

    grouped_topics: dict[tuple[str, str], list[tuple[str, int]]] = defaultdict(list)
    for (geography_value, complaint_type, topic), count in grouped_counts.items():
        grouped_topics[(geography_value, complaint_type)].append((topic, count))

    summaries: list[GeographyTopicSummary] = []
    for (geography_value, complaint_type), topic_counts in sorted(
        grouped_topics.items()
    ):
        ordered_topic_counts = sorted(
            topic_counts, key=lambda item: (-item[1], item[0])
        )
        total_count = geography_totals[(geography_value, complaint_type)]

        for index, (topic, count) in enumerate(ordered_topic_counts, start=1):
            summaries.append(
                GeographyTopicSummary(
                    geography=geography,
                    geography_value=geography_value,
                    complaint_type=complaint_type,
                    topic=topic,
                    complaint_count=count,
                    geography_total_count=total_count,
                    share_of_geography=count / total_count,
                    topic_rank=index,
                    is_dominant_topic=index == 1,
                )
            )

    return summaries


def detect_anomalies(
    aggregated_data: list[GeographyTopicSummary], window: AnalysisWindow
) -> list[object]:
    """Detect temporal anomalies in complaint trends."""
    del aggregated_data, window
    planned_surface("detect_anomalies()")


def analyze_resolution_gaps(
    service_requests: list[ServiceRequestRecord], resolution_data: object
) -> list[object]:
    """Analyze where resolution rates or times lag behind complaint volume."""
    del service_requests, resolution_data
    planned_surface("analyze_resolution_gaps()")
