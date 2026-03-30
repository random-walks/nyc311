"""Typed planning models for the target ``nyc311`` package surface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GeographyFilter:
    """A high-level geography selector for pulls and aggregations."""

    geography: str
    value: str


@dataclass(frozen=True)
class AnalysisWindow:
    """Rolling time window used for trend and anomaly calculations."""

    days: int


@dataclass(frozen=True)
class TopicQuery:
    """Topic analysis request parameters."""

    complaint_type: str
    top_n: int = 20


@dataclass(frozen=True)
class ExportTarget:
    """Destination metadata for an eventual export command."""

    format: str
    output_path: Path
