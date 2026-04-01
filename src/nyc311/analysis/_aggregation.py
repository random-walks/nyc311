"""Geography-level aggregation helpers for topic assignments."""

from __future__ import annotations

from collections import defaultdict

from ..models import GeographyTopicSummary, TopicAssignment


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
