"""Typed models for the implemented and planned ``nyc311`` package surface."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Final

SUPPORTED_GEOGRAPHIES: Final[tuple[str, ...]] = ("borough", "community_district")
SOCRATA_DATASET_IDENTIFIER: Final[str] = "erm2-nwe9"


def _normalize_value(value: str) -> str:
    """Normalize user- or file-provided string values."""
    return " ".join(value.strip().split())


@dataclass(frozen=True)
class GeographyFilter:
    """A supported geography selector for implemented loading filters."""

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
    """Filters for CSV and Socrata service-request loading."""

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
class SocrataConfig:
    """Configuration for the implemented live Socrata loader path."""

    dataset_identifier: str = SOCRATA_DATASET_IDENTIFIER
    base_url: str = "https://data.cityofnewyork.us/resource"
    app_token: str | None = None
    page_size: int = 1000
    request_timeout_seconds: float = 30.0
    max_pages: int | None = None
    extra_where_clauses: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        dataset_identifier = self.dataset_identifier.strip()
        base_url = self.base_url.rstrip("/")

        if not dataset_identifier:
            raise ValueError("dataset_identifier must not be empty.")
        if not base_url:
            raise ValueError("base_url must not be empty.")
        if self.page_size < 1:
            raise ValueError("page_size must be at least 1.")
        if self.request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be positive.")
        if self.max_pages is not None and self.max_pages < 1:
            raise ValueError("max_pages must be at least 1 when provided.")

        normalized_extra_where_clauses = tuple(
            normalized
            for raw_value in self.extra_where_clauses
            if (normalized := _normalize_value(raw_value))
        )
        object.__setattr__(self, "dataset_identifier", dataset_identifier)
        object.__setattr__(self, "base_url", base_url)
        object.__setattr__(self, "extra_where_clauses", normalized_extra_where_clauses)


@dataclass(frozen=True)
class AnalysisWindow:
    """Rolling time window used for trend and anomaly calculations."""

    days: int


@dataclass(frozen=True)
class TopicQuery:
    """Topic-analysis parameters for the implemented rules-based workflow."""

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


@dataclass(frozen=True)
class BoundaryFeature:
    """A supported boundary feature for boundary-backed GeoJSON export."""

    geography: str
    geography_value: str
    geometry: dict[str, Any]
    properties: dict[str, Any]

    def __post_init__(self) -> None:
        normalized_geography = self.geography.strip().lower()
        if normalized_geography not in SUPPORTED_GEOGRAPHIES:
            msg = (
                "Unsupported boundary geography. "
                f"Expected one of {SUPPORTED_GEOGRAPHIES}, got {self.geography!r}."
            )
            raise ValueError(msg)
        if not _normalize_value(self.geography_value):
            raise ValueError("geography_value must not be empty.")
        object.__setattr__(self, "geography", normalized_geography)
        object.__setattr__(
            self, "geography_value", _normalize_value(self.geography_value)
        )


@dataclass(frozen=True)
class BoundaryCollection:
    """Boundary features for one supported geography type."""

    geography: str
    features: tuple[BoundaryFeature, ...]

    def __post_init__(self) -> None:
        normalized_geography = self.geography.strip().lower()
        if normalized_geography not in SUPPORTED_GEOGRAPHIES:
            msg = (
                "Unsupported boundary collection geography. "
                f"Expected one of {SUPPORTED_GEOGRAPHIES}, got {self.geography!r}."
            )
            raise ValueError(msg)
        if not self.features:
            raise ValueError("features must not be empty.")
        object.__setattr__(self, "geography", normalized_geography)


@dataclass(frozen=True)
class BoundaryGeoJSONExport:
    """Combined boundary + summary payload for GeoJSON export."""

    boundaries: BoundaryCollection
    summaries: tuple[GeographyTopicSummary, ...]


def supported_topic_queries() -> tuple[str, ...]:
    """Return the complaint types with implemented topic extraction."""
    return (
        "Blocked Driveway",
        "Illegal Parking",
        "Noise - Residential",
        "Rodent",
    )
