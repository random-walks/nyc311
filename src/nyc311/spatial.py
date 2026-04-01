"""Optional geospatial helpers built on top of the typed nyc311 models."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ._tabular import SERVICE_REQUEST_DATAFRAME_COLUMNS
from .boundaries import load_boundary_collection
from .dataframes import records_to_dataframe, summaries_to_dataframe
from .geographies.loaders import (
    _boundary_collection_to_geodataframe,
)
from .geographies.loaders import (
    load_nyc_boundaries_geodataframe as _load_nyc_boundaries_geodataframe,
)
from .models import BoundaryCollection, GeographyTopicSummary, ServiceRequestRecord

if TYPE_CHECKING:
    import geopandas as gpd  # type: ignore[import-untyped]


def _require_geospatial_stack() -> tuple[Any, Any]:
    """Import the optional geospatial stack on demand."""
    try:
        geopandas = import_module("geopandas")
        shapely_geometry = import_module("shapely.geometry")
    except ImportError as exc:  # pragma: no cover - exercised via importorskip tests
        raise ImportError(
            "geopandas and shapely are required for nyc311.spatial helpers. "
            "Install them with `pip install nyc311[spatial]` or "
            "`pip install geopandas shapely`."
        ) from exc
    return geopandas, shapely_geometry


def records_to_geodataframe(records: list[ServiceRequestRecord]) -> gpd.GeoDataFrame:
    """Convert point-capable service-request records into a GeoDataFrame."""
    geopandas, _ = _require_geospatial_stack()
    records_with_coordinates = [
        record
        for record in records
        if record.latitude is not None and record.longitude is not None
    ]
    if not records_with_coordinates:
        return geopandas.GeoDataFrame(
            columns=(*SERVICE_REQUEST_DATAFRAME_COLUMNS, "geometry"),
            geometry="geometry",
            crs="EPSG:4326",
        )

    dataframe = records_to_dataframe(records_with_coordinates).copy()
    return geopandas.GeoDataFrame(
        dataframe,
        geometry=geopandas.points_from_xy(
            dataframe["longitude"],
            dataframe["latitude"],
        ),
        crs="EPSG:4326",
    )


def load_boundaries_geodataframe(
    source: str | Path | BoundaryCollection | None = None,
    *,
    layer: str | None = None,
) -> gpd.GeoDataFrame:
    """Load supported boundaries from a path, collection, or packaged layer."""
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


def spatial_join_records_to_boundaries(
    records_gdf: gpd.GeoDataFrame,
    boundaries_gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Join point records to boundary polygons without clobbering record columns."""
    geopandas, _ = _require_geospatial_stack()
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


def summaries_to_geodataframe(
    summaries: list[GeographyTopicSummary],
    boundaries_gdf: gpd.GeoDataFrame | None = None,
    *,
    layer: str | None = None,
) -> gpd.GeoDataFrame:
    """Merge aggregated geography summaries onto boundary geometries."""
    geopandas, _ = _require_geospatial_stack()
    if boundaries_gdf is None:
        if layer is None:
            if not summaries:
                raise ValueError(
                    "summaries_to_geodataframe() requires boundaries_gdf or layer "
                    "when summaries is empty."
                )
            layer = summaries[0].geography
        boundaries_gdf = _load_nyc_boundaries_geodataframe(layer)
    if "geography" not in boundaries_gdf.columns:
        raise ValueError("boundaries_gdf must include a geography column.")
    if "geography_value" not in boundaries_gdf.columns:
        raise ValueError("boundaries_gdf must include a geography_value column.")

    summary_dataframe = summaries_to_dataframe(summaries)
    merged = boundaries_gdf.merge(
        summary_dataframe,
        on=["geography", "geography_value"],
        how="left",
    )
    return geopandas.GeoDataFrame(merged, geometry="geometry", crs=boundaries_gdf.crs)
