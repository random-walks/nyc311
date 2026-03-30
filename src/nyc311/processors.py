"""Planned processing steps for complaint intelligence workflows."""

from __future__ import annotations

from typing import Any

from ._not_implemented import planned_surface
from .models import AnalysisWindow, TopicQuery


def extract_topics(service_requests: Any, query: TopicQuery) -> Any:
    """Extract fine-grained topics from complaint text."""
    planned_surface("extract_topics()")


def aggregate_by_geography(service_requests: Any, boundaries: Any) -> Any:
    """Aggregate complaint information into supported geographies."""
    planned_surface("aggregate_by_geography()")


def detect_anomalies(aggregated_data: Any, window: AnalysisWindow) -> Any:
    """Detect temporal anomalies in complaint trends."""
    planned_surface("detect_anomalies()")


def analyze_resolution_gaps(service_requests: Any, resolution_data: Any) -> Any:
    """Analyze where resolution rates or times lag behind complaint volume."""
    planned_surface("analyze_resolution_gaps()")
