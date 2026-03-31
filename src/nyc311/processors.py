"""Transform loaded records into deterministic topic and geography summaries.

The processing flow stays reproducible and rules-friendly while also exposing
notebook-oriented helpers for coverage audits, custom rule registration, and
basic anomaly scoring over aggregated outputs.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from importlib import import_module
from statistics import mean, pstdev
from typing import Final

from .models import (
    AnalysisWindow,
    AnomalyResult,
    GeographyTopicSummary,
    ResolutionGapSummary,
    ServiceRequestRecord,
    TopicAssignment,
    TopicCoverageReport,
    TopicQuery,
)

TopicRule = tuple[str, tuple[str, ...]]
TopicRuleSet = tuple[TopicRule, ...]

_OTHER_TOPIC: Final[str] = "other"
_UNSPECIFIED_TEXT: Final[str] = "unspecified"
DEFAULT_TOPIC_RULES: Final[dict[str, TopicRuleSet]] = {
    "Noise - Residential": (
        ("party_music", ("party", "music", "speakers", "stereo", "bass", "television")),
        ("construction", ("construction", "drilling", "jackhammer")),
        ("pet_noise", ("dog", "barking", "pet")),
        ("banging", ("banging", "thumping", "shaking", "arguing", "hammering")),
    ),
    "Illegal Parking": (
        ("hydrant_blocking", ("hydrant", "fire hydrant")),
        ("crosswalk_blocking", ("crosswalk",)),
        ("bus_stop_blocking", ("bus stop",)),
        ("double_parked", ("double parked", "double parking", "double parked")),
    ),
    "Blocked Driveway": (
        ("commercial_driveway", ("commercial van", "delivery truck", "truck")),
        ("overnight_blocking", ("overnight", "all night")),
        ("residential_driveway", ("residential driveway", "driveway", "garage")),
    ),
    "Rodent": (
        ("extermination_request", ("exterminator", "extermination", "infestation")),
        ("rats_seen", ("rats", "rat", "trash bags")),
        ("mouse_condition", ("mouse", "mice", "droppings")),
    ),
    "HEAT/HOT WATER": (
        ("no_heat", ("no heat", "without heat", "radiator cold", "heat not working")),
        (
            "no_hot_water",
            ("no hot water", "without hot water", "hot water not working"),
        ),
        (
            "intermittent_heat",
            ("intermittent heat", "heat comes and goes", "heat inconsistent"),
        ),
    ),
    "Street Condition": (
        ("pothole", ("pothole", "potholes")),
        ("cave_in", ("cave in", "cave-in", "sinkhole", "collapsed roadway")),
        ("rough_road", ("uneven", "rough road", "broken asphalt", "road surface")),
    ),
    "Noise - Street/Sidewalk": (
        ("construction", ("construction", "drilling", "jackhammer")),
        ("loud_vehicle", ("car alarm", "engine idling", "horn", "vehicle", "muffler")),
        ("bar_noise", ("bar", "club", "restaurant", "patrons", "crowd")),
    ),
    "UNSANITARY CONDITION": (
        ("garbage", ("garbage", "trash", "refuse", "debris")),
        ("sewage", ("sewage", "feces", "human waste", "overflow")),
        ("pest_waste", ("rodent", "rat", "mouse", "droppings", "animal waste")),
    ),
    "Abandoned Vehicle": (
        ("derelict_vehicle", ("abandoned", "derelict", "stripped", "wrecked")),
        ("unlicensed_vehicle", ("no plate", "no registration", "expired registration")),
    ),
}
_REGISTERED_TOPIC_RULES: dict[str, TopicRuleSet] = dict(DEFAULT_TOPIC_RULES)
_TEXT_NORMALIZATION_PATTERN: Final[re.Pattern[str]] = re.compile(r"[^a-z0-9]+")


def _normalize_text(value: str) -> str:
    """Normalize complaint text for deterministic rule matching."""
    stripped = value.strip().lower()
    normalized = _TEXT_NORMALIZATION_PATTERN.sub(" ", stripped)
    return " ".join(normalized.split())


def _normalize_value(value: str) -> str:
    return " ".join(value.strip().split())


def _matches_keyword(normalized_text: str, keyword: str) -> bool:
    """Return whether a normalized text contains a normalized keyword."""
    normalized_keyword = _normalize_text(keyword)
    if " " in normalized_keyword:
        return normalized_keyword in normalized_text
    return normalized_keyword in normalized_text.split()


def _normalize_topic_rules(rules: TopicRuleSet) -> TopicRuleSet:
    normalized_rules: list[TopicRule] = []
    for topic, keywords in rules:
        normalized_topic = _normalize_value(topic)
        normalized_keywords = tuple(
            normalized_keyword
            for keyword in keywords
            if (normalized_keyword := _normalize_text(keyword))
        )
        if not normalized_topic:
            raise ValueError("Topic rule labels must not be empty.")
        if not normalized_keywords:
            raise ValueError(
                f"Topic rule {topic!r} must include at least one non-empty keyword."
            )
        normalized_rules.append((normalized_topic, normalized_keywords))
    return tuple(normalized_rules)


def _descriptor_topic_label(normalized_text: str) -> str:
    return normalized_text if normalized_text else _UNSPECIFIED_TEXT


def register_topic_rules(complaint_type: str, rules: TopicRuleSet) -> None:
    """Register or replace topic rules for one complaint type."""
    normalized_complaint_type = _normalize_value(complaint_type)
    if not normalized_complaint_type:
        raise ValueError("complaint_type must not be empty.")
    _REGISTERED_TOPIC_RULES[normalized_complaint_type] = _normalize_topic_rules(rules)


def _select_topic_rules(
    complaint_type: str,
    custom_rules: TopicRuleSet | None,
) -> TopicRuleSet | None:
    if custom_rules is not None:
        if not custom_rules:
            return None
        return _normalize_topic_rules(custom_rules)
    return _REGISTERED_TOPIC_RULES.get(complaint_type)


def _limit_assignments(
    topic_assignments: list[TopicAssignment],
    *,
    top_n: int,
) -> list[TopicAssignment]:
    non_other_frequencies = Counter(
        assignment.topic
        for assignment in topic_assignments
        if assignment.topic != _OTHER_TOPIC
    )
    allowed_topics = {
        topic for topic, _count in non_other_frequencies.most_common(top_n)
    }
    if len(allowed_topics) == len(non_other_frequencies):
        return topic_assignments

    limited_assignments: list[TopicAssignment] = []
    for assignment in topic_assignments:
        if assignment.topic in allowed_topics or assignment.topic == _OTHER_TOPIC:
            limited_assignments.append(assignment)
            continue
        limited_assignments.append(
            TopicAssignment(
                record=assignment.record,
                topic=_OTHER_TOPIC,
                normalized_text=assignment.normalized_text,
            )
        )
    return limited_assignments


def _extract_rule_based_topics(
    service_requests: list[ServiceRequestRecord],
    rules: TopicRuleSet,
) -> list[TopicAssignment]:
    topic_assignments: list[TopicAssignment] = []
    for record in service_requests:
        normalized_text = _normalize_text(record.descriptor)
        matched_topic = _OTHER_TOPIC
        if normalized_text:
            for topic, keywords in rules:
                if any(
                    _matches_keyword(normalized_text, keyword) for keyword in keywords
                ):
                    matched_topic = topic
                    break
        else:
            normalized_text = _UNSPECIFIED_TEXT

        topic_assignments.append(
            TopicAssignment(
                record=record,
                topic=matched_topic,
                normalized_text=normalized_text,
            )
        )
    return topic_assignments


def _extract_fallback_topics(
    service_requests: list[ServiceRequestRecord],
) -> list[TopicAssignment]:
    topic_assignments: list[TopicAssignment] = []
    for record in service_requests:
        normalized_text = _normalize_text(record.descriptor) or _UNSPECIFIED_TEXT
        topic_assignments.append(
            TopicAssignment(
                record=record,
                topic=_descriptor_topic_label(normalized_text),
                normalized_text=normalized_text,
            )
        )
    return topic_assignments


def extract_topics(
    service_requests: list[ServiceRequestRecord],
    query: TopicQuery,
    *,
    custom_rules: TopicRuleSet | None = None,
) -> list[TopicAssignment]:
    """Extract deterministic first-pass topics for one complaint type."""
    complaint_type = query.complaint_type
    matching_records = [
        record for record in service_requests if record.complaint_type == complaint_type
    ]
    if not matching_records:
        return []

    rules = _select_topic_rules(complaint_type, custom_rules)
    if rules is None:
        topic_assignments = _extract_fallback_topics(matching_records)
    else:
        topic_assignments = _extract_rule_based_topics(matching_records, rules)
    return _limit_assignments(topic_assignments, top_n=query.top_n)


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
