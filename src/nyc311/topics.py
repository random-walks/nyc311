"""Deterministic topic rules and extraction helpers."""

from __future__ import annotations

import re
from collections import Counter
from typing import Final

from .models import ServiceRequestRecord, TopicAssignment, TopicQuery

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
