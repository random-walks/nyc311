"""Boundary model dataclasses for nyc311 geographies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._analysis import GeographyTopicSummary
from ._constants import SUPPORTED_BOUNDARY_GEOGRAPHIES
from ._normalize import _normalize_value


@dataclass(frozen=True)
class BoundaryFeature:
    """A supported boundary feature for boundary-backed GeoJSON export."""

    geography: str
    geography_value: str
    geometry: dict[str, Any]
    properties: dict[str, Any]

    def __post_init__(self) -> None:
        normalized_geography = self.geography.strip().lower()
        if normalized_geography not in SUPPORTED_BOUNDARY_GEOGRAPHIES:
            msg = (
                "Unsupported boundary geography. "
                f"Expected one of {SUPPORTED_BOUNDARY_GEOGRAPHIES}, got {self.geography!r}."
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
        if normalized_geography not in SUPPORTED_BOUNDARY_GEOGRAPHIES:
            msg = (
                "Unsupported boundary collection geography. "
                f"Expected one of {SUPPORTED_BOUNDARY_GEOGRAPHIES}, got {self.geography!r}."
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
