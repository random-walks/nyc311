"""Boundary operations built on top of nyc311 and nyc_geo_toolkit."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nyc_geo_toolkit import clip_boundaries_to_bbox as toolkit_clip_boundaries_to_bbox

from ..models import BoundaryCollection, ServiceRequestRecord
from ..spatial import records_to_geodataframe, spatial_join_records_to_boundaries
from ._loaders import _boundary_collection_to_geodataframe, load_nyc_boundaries
from ._normalize import normalize_boundary_layer

if TYPE_CHECKING:
    import geopandas as gpd  # type: ignore[import-untyped]


def clip_boundaries_to_bbox(
    boundaries: BoundaryCollection,
    *,
    min_longitude: float,
    min_latitude: float,
    max_longitude: float,
    max_latitude: float,
) -> BoundaryCollection:
    """Clip boundary geometries to a longitude/latitude bounding box."""
    return toolkit_clip_boundaries_to_bbox(
        boundaries,
        min_longitude=min_longitude,
        min_latitude=min_latitude,
        max_longitude=max_longitude,
        max_latitude=max_latitude,
    )


def spatially_enrich_records(
    records: list[ServiceRequestRecord],
    *,
    layer: str = "community_district",
    boundaries: BoundaryCollection | None = None,
) -> gpd.GeoDataFrame:
    """Attach packaged boundary attributes to point-capable service requests."""
    normalized_layer = normalize_boundary_layer(layer)
    boundary_collection = boundaries or load_nyc_boundaries(normalized_layer)
    boundaries_gdf = _boundary_collection_to_geodataframe(boundary_collection)
    records_gdf = records_to_geodataframe(records)
    return spatial_join_records_to_boundaries(records_gdf, boundaries_gdf)
