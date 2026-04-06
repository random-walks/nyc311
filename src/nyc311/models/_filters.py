"""Filter and query dataclasses for nyc311 workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from ._constants import SOCRATA_DATASET_IDENTIFIER, SUPPORTED_GEOGRAPHIES
from ._normalize import _normalize_value, normalize_borough_name


@dataclass(frozen=True)
class GeographyFilter:
    """A supported geography selector for implemented loading filters."""

    geography: str
    value: str

    def __post_init__(self) -> None:
        normalized_geography = self.geography.strip().lower()
        normalized_value = (
            normalize_borough_name(self.value)
            if normalized_geography == "borough"
            else _normalize_value(self.value)
        )

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
    """Configuration for the implemented live Socrata loader path.

    ``extra_where_clauses`` holds additional ``$where`` fragments (Socrata SoQL) that
    are AND-joined after the predicates derived from :class:`ServiceRequestFilter`.
    Use for predicates not covered by the filter (e.g. ``latitude IS NOT NULL``).
    Values are stripped; empty strings are dropped.
    """

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
