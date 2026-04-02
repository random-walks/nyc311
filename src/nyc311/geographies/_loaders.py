"""Compatibility loaders backed by nyc_geo_toolkit."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any

from nyc_geo_toolkit import (
    list_boundary_layers as toolkit_list_boundary_layers,
)
from nyc_geo_toolkit import (
    list_boundary_values as toolkit_list_boundary_values,
)
from nyc_geo_toolkit import (
    load_boundaries as toolkit_load_boundaries,
)
from nyc_geo_toolkit import (
    load_nyc_boundaries as toolkit_load_nyc_boundaries,
)
from nyc_geo_toolkit import (
    load_nyc_boundaries_geodataframe as toolkit_load_nyc_boundaries_geodataframe,
)
from nyc_geo_toolkit import (
    load_nyc_census_tracts as toolkit_load_nyc_census_tracts,
)
from nyc_geo_toolkit import (
    load_nyc_council_districts as toolkit_load_nyc_council_districts,
)
from nyc_geo_toolkit import (
    load_nyc_neighborhood_tabulation_areas as toolkit_load_nyc_neighborhood_tabulation_areas,
)

from ..models import BoundaryCollection

if TYPE_CHECKING:
    import geopandas as gpd  # type: ignore[import-untyped]


def _require_geospatial_stack() -> tuple[Any, Any]:
    try:
        geopandas = import_module("geopandas")
        shapely_geometry = import_module("shapely.geometry")
    except ImportError as exc:  # pragma: no cover - exercised in optional tests
        raise ImportError(
            "geopandas and shapely are required for nyc311 geography helpers. "
            "Install them with `pip install nyc311[spatial]` or "
            "`pip install geopandas shapely`."
        ) from exc
    return geopandas, shapely_geometry


def _boundary_collection_to_geodataframe(
    boundaries: BoundaryCollection,
) -> gpd.GeoDataFrame:
    geopandas, shapely_geometry = _require_geospatial_stack()
    rows = [
        {
            "geography": feature.geography,
            "geography_value": feature.geography_value,
            **feature.properties,
            "geometry": shapely_geometry.shape(feature.geometry),
        }
        for feature in boundaries.features
    ]
    return geopandas.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")


def list_boundary_layers() -> tuple[str, ...]:
    """List the packaged NYC boundary layers shipped with nyc311."""
    return toolkit_list_boundary_layers()


def list_boundary_values(layer: str) -> tuple[str, ...]:
    """List the canonical values available for one packaged boundary layer."""
    return toolkit_list_boundary_values(layer)


def load_nyc_boundaries(
    layer: str = "community_district",
    *,
    values: str | tuple[str, ...] | list[str] | None = None,
) -> BoundaryCollection:
    """Load a packaged NYC boundary layer as typed boundary models."""
    return toolkit_load_nyc_boundaries(layer, values=values)


def load_boundaries(source: str | Path) -> BoundaryCollection:
    """Load boundaries from a file path or a packaged NYC boundary layer."""
    return toolkit_load_boundaries(source)


def load_nyc_boundaries_geodataframe(
    layer: str = "community_district",
    *,
    values: str | tuple[str, ...] | list[str] | None = None,
) -> gpd.GeoDataFrame:
    """Load a packaged NYC boundary layer directly into a GeoDataFrame."""
    return toolkit_load_nyc_boundaries_geodataframe(layer, values=values)


def load_nyc_census_tracts(
    *,
    values: str | tuple[str, ...] | list[str] | None = None,
) -> BoundaryCollection:
    """Load the packaged NYC census-tract layer."""
    return toolkit_load_nyc_census_tracts(values=values)


def load_nyc_neighborhood_tabulation_areas(
    *,
    values: str | tuple[str, ...] | list[str] | None = None,
) -> BoundaryCollection:
    """Load the packaged NYC neighborhood-tabulation-area layer."""
    return toolkit_load_nyc_neighborhood_tabulation_areas(values=values)


def load_nyc_council_districts(
    *,
    values: str | tuple[str, ...] | list[str] | None = None,
) -> BoundaryCollection:
    """Load the packaged NYC city-council-district layer."""
    return toolkit_load_nyc_council_districts(values=values)
