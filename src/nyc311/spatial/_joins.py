"""Spatial join helpers for nyc311 GeoDataFrames."""

from __future__ import annotations

from typing import Any

from ._deps import require_geospatial_stack


def spatial_join_records_to_boundaries(
    records_gdf: Any, boundaries_gdf: Any
) -> Any:
    """Join point records to boundary polygons without clobbering record columns."""
    geopandas, _ = require_geospatial_stack()
    aligned_boundaries = boundaries_gdf
    if (
        getattr(records_gdf, "crs", None)
        and getattr(boundaries_gdf, "crs", None)
        and records_gdf.crs != boundaries_gdf.crs
    ):
        aligned_boundaries = boundaries_gdf.to_crs(records_gdf.crs)

    renamed_boundaries = aligned_boundaries.rename(
        columns={
            column_name: f"boundary_{column_name}"
            for column_name in aligned_boundaries.columns
            if column_name != "geometry"
        }
    )
    joined = geopandas.sjoin(
        records_gdf,
        renamed_boundaries,
        how="left",
        predicate="within",
    )
    if "index_right" in joined.columns:
        joined = joined.drop(columns="index_right")
    return joined
