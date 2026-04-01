"""Boundary operations built on top of packaged NYC geography layers."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from ..models import BoundaryCollection, BoundaryFeature, ServiceRequestRecord
from ..spatial import records_to_geodataframe, spatial_join_records_to_boundaries
from ._loaders import _boundary_collection_to_geodataframe, load_nyc_boundaries
from ._normalize import normalize_boundary_layer

if TYPE_CHECKING:
    import geopandas as gpd  # type: ignore[import-untyped]


def _require_shapely() -> Any:
    try:
        shapely_geometry = import_module("shapely.geometry")
    except ImportError as exc:  # pragma: no cover - exercised in optional tests
        raise ImportError(
            "shapely is required for nyc311 geography clipping helpers. "
            "Install it with `pip install nyc311[spatial]` or `pip install shapely`."
        ) from exc
    return shapely_geometry


def clip_boundaries_to_bbox(
    boundaries: BoundaryCollection,
    *,
    min_longitude: float,
    min_latitude: float,
    max_longitude: float,
    max_latitude: float,
) -> BoundaryCollection:
    """Clip boundary geometries to a longitude/latitude bounding box."""
    if min_longitude >= max_longitude or min_latitude >= max_latitude:
        raise ValueError("Bounding boxes must satisfy min < max on both axes.")

    shapely_geometry = _require_shapely()
    clip_box = shapely_geometry.box(
        min_longitude,
        min_latitude,
        max_longitude,
        max_latitude,
    )
    clipped_features: list[BoundaryFeature] = []
    for feature in boundaries.features:
        geometry = shapely_geometry.shape(feature.geometry)
        clipped_geometry = geometry.intersection(clip_box)
        if clipped_geometry.is_empty:
            continue
        clipped_features.append(
            BoundaryFeature(
                geography=feature.geography,
                geography_value=feature.geography_value,
                geometry=shapely_geometry.mapping(clipped_geometry),
                properties=dict(feature.properties),
            )
        )

    if not clipped_features:
        raise ValueError("No boundaries intersect the requested bounding box.")
    return BoundaryCollection(
        geography=boundaries.geography,
        features=tuple(clipped_features),
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
