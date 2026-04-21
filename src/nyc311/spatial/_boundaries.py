"""Boundary GeoDataFrame loading helpers for nyc311.spatial."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..geographies._geojson import load_boundary_collection
from ..geographies._loaders import (
    _boundary_collection_to_geodataframe,
)
from ..geographies._loaders import (
    load_nyc_boundaries_geodataframe as _load_nyc_boundaries_geodataframe,
)
from ..models import BoundaryCollection


def load_boundaries_geodataframe(
    source: str | Path | BoundaryCollection | None = None,
    *,
    layer: str | None = None,
) -> Any:
    """Load supported boundaries from a path, collection, or packaged layer.

    .. note::

       Need polygon centroids for spatial weights / Moran's I / label
       placement? Upstream :func:`nyc_geo_toolkit.centroids_from_boundaries`
       (v0.4+) converts any polygon ``BoundaryCollection`` into a Point
       ``BoundaryCollection``, preserving geography / vintage / properties.
       Pair with ``representative=True`` for non-convex polygons. See the
       :mod:`nyc311.spatial` module docstring for the full recipe.
    """
    if layer is not None:
        if source is not None:
            raise ValueError("Pass either source or layer, not both.")
        return _load_nyc_boundaries_geodataframe(layer)

    if source is None:
        raise TypeError("load_boundaries_geodataframe() requires source or layer.")
    if isinstance(source, BoundaryCollection):
        return _boundary_collection_to_geodataframe(source)
    if isinstance(source, Path) or Path(source).exists():
        return _boundary_collection_to_geodataframe(load_boundary_collection(source))
    try:
        return _load_nyc_boundaries_geodataframe(str(source))
    except ValueError:
        return _boundary_collection_to_geodataframe(load_boundary_collection(source))
