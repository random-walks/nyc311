"""Boundary file loading wrappers backed by nyc_geo_toolkit."""

from __future__ import annotations

from pathlib import Path

from nyc_geo_toolkit import load_boundaries as toolkit_load_boundaries

from ..models import BoundaryCollection


def load_boundary_collection(source: str | Path) -> BoundaryCollection:
    """Load simple GeoJSON polygon features for supported geographies."""
    return toolkit_load_boundaries(source)
