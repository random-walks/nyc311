"""Boundary model compatibility layer for nyc311 geographies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from nyc_geo_toolkit import (
    BoundaryCollection as ToolkitBoundaryCollection,
)
from nyc_geo_toolkit import (
    BoundaryFeature as ToolkitBoundaryFeature,
)

if TYPE_CHECKING:
    from ._analysis import GeographyTopicSummary

BoundaryCollection = ToolkitBoundaryCollection
BoundaryFeature = ToolkitBoundaryFeature


@dataclass(frozen=True, slots=True)
class BoundaryGeoJSONExport:
    """Combined boundary + summary payload for GeoJSON export."""

    boundaries: BoundaryCollection
    summaries: tuple[GeographyTopicSummary, ...]
