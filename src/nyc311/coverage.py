"""Coverage analysis for deterministic topic extraction."""

from __future__ import annotations

from collections import Counter

from .models import ServiceRequestRecord, TopicCoverageReport, TopicQuery
from .topics import (
    _OTHER_TOPIC,
    _UNSPECIFIED_TEXT,
    TopicRuleSet,
    _normalize_value,
    extract_topics,
)


def analyze_topic_coverage(
    service_requests: list[ServiceRequestRecord],
    query: TopicQuery,
    *,
    custom_rules: TopicRuleSet | None = None,
    top_unmatched_n: int = 10,
) -> TopicCoverageReport:
    """Report how much a topic configuration matched versus falling into other."""
    matching_records = [
        record
        for record in service_requests
        if record.complaint_type == query.complaint_type
    ]
    assignments = extract_topics(
        matching_records,
        query,
        custom_rules=custom_rules,
    )
    matched_records = sum(
        assignment.topic != _OTHER_TOPIC for assignment in assignments
    )
    other_records = len(assignments) - matched_records
    unmatched_descriptors = Counter(
        _normalize_value(assignment.record.descriptor) or _UNSPECIFIED_TEXT
        for assignment in assignments
        if assignment.topic == _OTHER_TOPIC
    )
    total_records = len(assignments)
    return TopicCoverageReport(
        complaint_type=query.complaint_type,
        total_records=total_records,
        matched_records=matched_records,
        other_records=other_records,
        coverage_rate=0 if total_records == 0 else matched_records / total_records,
        top_unmatched_descriptors=tuple(
            unmatched_descriptors.most_common(top_unmatched_n)
        ),
    )
