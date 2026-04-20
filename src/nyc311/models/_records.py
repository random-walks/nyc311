"""Core record-like dataclasses for nyc311 workflows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ._constants import SUPPORTED_GEOGRAPHIES
from ._normalize import (
    _normalize_borough_or_passthrough,
    _normalize_community_district_or_passthrough,
    _normalize_coordinate_pair,
    _normalize_value,
)


@dataclass(frozen=True, slots=True)
class ServiceRequestRecord:
    """A single loaded NYC 311-style service-request record.

    .. note::

        As of nyc311 v1.0.1, ``closed_date`` is carried alongside
        ``created_date`` so resolution-time analyses don't have to
        bypass the SDK. The field is optional — Socrata returns a
        null ``closed_date`` for any unresolved complaint — and
        existing call sites that instantiate the record without it
        keep working unchanged.
    """

    service_request_id: str
    created_date: date
    complaint_type: str
    descriptor: str
    borough: str
    community_district: str
    resolution_description: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    #: Date the complaint was closed. ``None`` for unresolved
    #: complaints. Use ``closed_date - created_date`` for resolution
    #: latency in days.
    closed_date: date | None = None

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
        object.__setattr__(
            self, "borough", _normalize_borough_or_passthrough(self.borough)
        )
        object.__setattr__(
            self,
            "community_district",
            _normalize_community_district_or_passthrough(self.community_district),
        )

        normalized_resolution = (
            None
            if self.resolution_description is None
            else _normalize_value(self.resolution_description)
        )
        object.__setattr__(
            self,
            "resolution_description",
            normalized_resolution if normalized_resolution else None,
        )

        latitude, longitude = _normalize_coordinate_pair(
            self.latitude,
            self.longitude,
        )
        object.__setattr__(self, "latitude", latitude)
        object.__setattr__(self, "longitude", longitude)

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


@dataclass(frozen=True, slots=True)
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
