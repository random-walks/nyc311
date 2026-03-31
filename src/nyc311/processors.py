"""Backward-compatible re-export layer for processing helpers."""

from __future__ import annotations

from .aggregation import aggregate_by_geography
from .analytics import _compute_z_scores, analyze_resolution_gaps, detect_anomalies
from .coverage import analyze_topic_coverage
from .topics import (
    DEFAULT_TOPIC_RULES,
    TopicRule,
    TopicRuleSet,
    _OTHER_TOPIC,
    _REGISTERED_TOPIC_RULES,
    _UNSPECIFIED_TEXT,
    _extract_fallback_topics,
    _extract_rule_based_topics,
    _limit_assignments,
    _matches_keyword,
    _normalize_text,
    _normalize_topic_rules,
    _normalize_value,
    _select_topic_rules,
    extract_topics,
    register_topic_rules,
)

__all__ = [
    "DEFAULT_TOPIC_RULES",
    "TopicRule",
    "TopicRuleSet",
    "_OTHER_TOPIC",
    "_REGISTERED_TOPIC_RULES",
    "_UNSPECIFIED_TEXT",
    "_compute_z_scores",
    "_extract_fallback_topics",
    "_extract_rule_based_topics",
    "_limit_assignments",
    "_matches_keyword",
    "_normalize_text",
    "_normalize_topic_rules",
    "_normalize_value",
    "_select_topic_rules",
    "aggregate_by_geography",
    "analyze_resolution_gaps",
    "analyze_topic_coverage",
    "detect_anomalies",
    "extract_topics",
    "register_topic_rules",
]
