"""Analysis-oriented dataclasses for nyc311 workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ._constants import SUPPORTED_GEOGRAPHIES
from ._normalize import _normalize_value


@dataclass(frozen=True)
class AnalysisWindow:
    """Rolling time window used for trend and anomaly calculations."""

    days: int

    def __post_init__(self) -> None:
        if self.days < 1:
            raise ValueError("days must be at least 1.")


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
class TopicCoverageReport:
    """Coverage metadata that shows how much a topic ruleset matched."""

    complaint_type: str
    total_records: int
    matched_records: int
    other_records: int
    coverage_rate: float
    top_unmatched_descriptors: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        if not _normalize_value(self.complaint_type):
            raise ValueError("complaint_type must not be empty.")
        if self.total_records < 0:
            raise ValueError("total_records must be non-negative.")
        if self.matched_records < 0:
            raise ValueError("matched_records must be non-negative.")
        if self.other_records < 0:
            raise ValueError("other_records must be non-negative.")
        if self.matched_records + self.other_records != self.total_records:
            raise ValueError(
                "matched_records + other_records must equal total_records."
            )
        if not 0 <= self.coverage_rate <= 1:
            raise ValueError("coverage_rate must be in the interval [0, 1].")
        object.__setattr__(
            self, "complaint_type", _normalize_value(self.complaint_type)
        )


@dataclass(frozen=True)
class ExportTarget:
    """Destination metadata for supported exporters."""

    format: str
    output_path: Path

    def __post_init__(self) -> None:
        normalized_format = self.format.strip().lower()
        if not normalized_format:
            raise ValueError("format must not be empty.")
        object.__setattr__(self, "format", normalized_format)
        object.__setattr__(self, "output_path", Path(self.output_path))


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
class ResolutionGapSummary:
    """A first-pass borough-level summary of unresolved complaint volume."""

    geography: str
    geography_value: str
    complaint_type: str
    total_request_count: int
    resolved_request_count: int
    unresolved_request_count: int
    unresolved_share: float
    resolution_rate: float

    def __post_init__(self) -> None:
        normalized_geography = self.geography.strip().lower()
        if normalized_geography not in SUPPORTED_GEOGRAPHIES:
            msg = (
                "Unsupported geography summary. "
                f"Expected one of {SUPPORTED_GEOGRAPHIES}, got {self.geography!r}."
            )
            raise ValueError(msg)
        if self.total_request_count < 1:
            raise ValueError("total_request_count must be at least 1.")
        if self.resolved_request_count < 0 or self.unresolved_request_count < 0:
            raise ValueError("resolution counts must be non-negative.")
        if (
            self.resolved_request_count + self.unresolved_request_count
            != self.total_request_count
        ):
            raise ValueError(
                "resolved_request_count + unresolved_request_count must equal total_request_count."
            )
        if not 0 <= self.unresolved_share <= 1:
            raise ValueError("unresolved_share must be in the interval [0, 1].")
        if not 0 <= self.resolution_rate <= 1:
            raise ValueError("resolution_rate must be in the interval [0, 1].")
        if not _normalize_value(self.geography_value):
            raise ValueError("geography_value must not be empty.")
        if not _normalize_value(self.complaint_type):
            raise ValueError("complaint_type must not be empty.")

        object.__setattr__(self, "geography", normalized_geography)
        object.__setattr__(
            self, "geography_value", _normalize_value(self.geography_value)
        )
        object.__setattr__(
            self, "complaint_type", _normalize_value(self.complaint_type)
        )


@dataclass(frozen=True)
class AnomalyResult:
    """A standardized anomaly score for one aggregated topic summary."""

    geography: str
    geography_value: str
    complaint_type: str
    topic: str
    complaint_count: int
    geography_total_count: int
    share_of_geography: float
    topic_rank: int
    z_score: float
    is_anomaly: bool
    window_days: int
    anomaly_threshold: float

    def __post_init__(self) -> None:
        normalized_geography = self.geography.strip().lower()
        if normalized_geography not in SUPPORTED_GEOGRAPHIES:
            msg = (
                "Unsupported anomaly geography. "
                f"Expected one of {SUPPORTED_GEOGRAPHIES}, got {self.geography!r}."
            )
            raise ValueError(msg)
        if not _normalize_value(self.geography_value):
            raise ValueError("geography_value must not be empty.")
        if not _normalize_value(self.complaint_type):
            raise ValueError("complaint_type must not be empty.")
        if not _normalize_value(self.topic):
            raise ValueError("topic must not be empty.")
        if self.complaint_count < 1:
            raise ValueError("complaint_count must be at least 1.")
        if self.geography_total_count < self.complaint_count:
            raise ValueError("geography_total_count must be >= complaint_count.")
        if not 0 < self.share_of_geography <= 1:
            raise ValueError("share_of_geography must be in the interval (0, 1].")
        if self.topic_rank < 1:
            raise ValueError("topic_rank must be at least 1.")
        if self.window_days < 1:
            raise ValueError("window_days must be at least 1.")
        if self.anomaly_threshold <= 0:
            raise ValueError("anomaly_threshold must be positive.")

        object.__setattr__(self, "geography", normalized_geography)
        object.__setattr__(
            self, "geography_value", _normalize_value(self.geography_value)
        )
        object.__setattr__(
            self, "complaint_type", _normalize_value(self.complaint_type)
        )
        object.__setattr__(self, "topic", _normalize_value(self.topic))
