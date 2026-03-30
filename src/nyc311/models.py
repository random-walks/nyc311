"""Typed models for the implemented and planned ``nyc311`` package surface."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Final

SUPPORTED_GEOGRAPHIES: Final[tuple[str, ...]] = ("borough", "community_district")


def _normalize_value(value: str) -> str:
    """Normalize user- or file-provided string values."""
    return " ".join(value.strip().split())


@dataclass(frozen=True)
class GeographyFilter:
    """A supported geography selector for v0.1 CSV loading filters."""

    geography: str
    value: str

    def __post_init__(self) -> None:
        normalized_geography = self.geography.strip().lower()
        normalized_value = _normalize_value(self.value)

        if normalized_geography not in SUPPORTED_GEOGRAPHIES:
            msg = (
                "Unsupported geography filter. "
                f"Expected one of {SUPPORTED_GEOGRAPHIES}, got {self.geography!r}."
            )
            raise ValueError(msg)

        if not normalized_value:
            raise ValueError("Geography filter value must not be empty.")

        object.__setattr__(self, "geography", normalized_geography)
        object.__setattr__(self, "value", normalized_value)


@dataclass(frozen=True)
class ServiceRequestFilter:
    """Loader filters for the implemented v0.1 local-CSV happy path."""

    start_date: date | None = None
    end_date: date | None = None
    geography: GeographyFilter | None = None
    complaint_types: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date.")

        normalized_complaint_types = tuple(
            normalized
            for raw_value in self.complaint_types
            if (normalized := _normalize_value(raw_value))
        )
        object.__setattr__(self, "complaint_types", normalized_complaint_types)


@dataclass(frozen=True)
class AnalysisWindow:
    """Rolling time window used for trend and anomaly calculations."""

    days: int


@dataclass(frozen=True)
class TopicQuery:
    """Topic-analysis parameters for the implemented v0.1 rules-based workflow."""

    complaint_type: str
    top_n: int = 20

    def __post_init__(self) -> None:
        normalized_complaint_type = _normalize_value(self.complaint_type)
        if not normalized_complaint_type:
            raise ValueError("complaint_type must not be empty.")
        if self.top_n < 1:
            raise ValueError("top_n must be at least 1.")
        object.__setattr__(self, "complaint_type", normalized_complaint_type)


@dataclass(frozen=True)
class ExportTarget:
    """Destination metadata for implemented and planned exporters."""

    format: str
    output_path: Path

    def __post_init__(self) -> None:
        normalized_format = self.format.strip().lower()
        if not normalized_format:
            raise ValueError("format must not be empty.")
        object.__setattr__(self, "format", normalized_format)
        object.__setattr__(self, "output_path", Path(self.output_path))


@dataclass(frozen=True)
class ServiceRequestRecord:
    """A single loaded NYC 311-style service-request record."""

    service_request_id: str
    created_date: date
    complaint_type: str
    descriptor: str
    borough: str
    community_district: str
    resolution_description: str | None = None

    def __post_init__(self) -> None:
        if not _normalize_value(self.service_request_id):
            raise ValueError("service_request_id must not be empty.")
        if not _normalize_value(self.complaint_type):
            raise ValueError("complaint_type must not be empty.")
        if not _normalize_value(self.borough):
            raise ValueError("borough must not be empty.")
        if not _normalize_value(self.community_district):
            raise ValueError("community_district must not be empty.")

        object.__setattr__(
            self, "service_request_id", _normalize_value(self.service_request_id)
        )
        object.__setattr__(
            self, "complaint_type", _normalize_value(self.complaint_type)
        )
        object.__setattr__(self, "descriptor", _normalize_value(self.descriptor))
        object.__setattr__(self, "borough", _normalize_value(self.borough))
        object.__setattr__(
            self, "community_district", _normalize_value(self.community_district)
        )

        if self.resolution_description is None:
            return

        normalized_resolution = _normalize_value(self.resolution_description)
        object.__setattr__(
            self,
            "resolution_description",
            normalized_resolution if normalized_resolution else None,
        )

    def geography_value(self, geography: str) -> str:
        """Return the value for a supported geography key."""
        normalized_geography = geography.strip().lower()
        if normalized_geography == "borough":
            return self.borough
        if normalized_geography == "community_district":
            return self.community_district
        msg = (
            "Unsupported aggregation geography. "
            f"Expected one of {SUPPORTED_GEOGRAPHIES}, got {geography!r}."
        )
        raise ValueError(msg)


@dataclass(frozen=True)
class TopicAssignment:
    """A deterministic topic label derived from one service-request record."""

    record: ServiceRequestRecord
    topic: str
    normalized_text: str

    def __post_init__(self) -> None:
        if not _normalize_value(self.topic):
            raise ValueError("topic must not be empty.")
        if not _normalize_value(self.normalized_text):
            raise ValueError("normalized_text must not be empty.")

        object.__setattr__(self, "topic", _normalize_value(self.topic))
        object.__setattr__(
            self, "normalized_text", _normalize_value(self.normalized_text)
        )


@dataclass(frozen=True)
class GeographyTopicSummary:
    """An export-ready summary row for topic counts within one geography."""

    geography: str
    geography_value: str
    complaint_type: str
    topic: str
    complaint_count: int
    geography_total_count: int
    share_of_geography: float
    topic_rank: int
    is_dominant_topic: bool

    def __post_init__(self) -> None:
        normalized_geography = self.geography.strip().lower()
        if normalized_geography not in SUPPORTED_GEOGRAPHIES:
            msg = (
                "Unsupported geography summary. "
                f"Expected one of {SUPPORTED_GEOGRAPHIES}, got {self.geography!r}."
            )
            raise ValueError(msg)
        if self.complaint_count < 1:
            raise ValueError("complaint_count must be at least 1.")
        if self.geography_total_count < self.complaint_count:
            raise ValueError("geography_total_count must be >= complaint_count.")
        if not 0 < self.share_of_geography <= 1:
            raise ValueError("share_of_geography must be in the interval (0, 1].")
        if self.topic_rank < 1:
            raise ValueError("topic_rank must be at least 1.")
        if not _normalize_value(self.geography_value):
            raise ValueError("geography_value must not be empty.")
        if not _normalize_value(self.complaint_type):
            raise ValueError("complaint_type must not be empty.")
        if not _normalize_value(self.topic):
            raise ValueError("topic must not be empty.")

        object.__setattr__(self, "geography", normalized_geography)
        object.__setattr__(
            self, "geography_value", _normalize_value(self.geography_value)
        )
        object.__setattr__(
            self, "complaint_type", _normalize_value(self.complaint_type)
        )
        object.__setattr__(self, "topic", _normalize_value(self.topic))


def supported_topic_queries() -> tuple[str, ...]:
    """Return the complaint types with implemented topic extraction in v0.1."""
    return ("Noise - Residential", "Rodent")
