"""Library-owned loaders for packaged NYC boundary and sample resources."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from ..boundaries import boundary_collection_from_geojson
from ..loaders_csv import load_service_requests_from_csv
from ..models import BoundaryCollection, ServiceRequestFilter, ServiceRequestRecord
from .catalog import BOUNDARY_LAYER_CATALOG
from .normalize import normalize_boundary_layer, normalize_boundary_values
from .resources import (
    load_boundary_payload,
    load_sample_boundary_values,
    sample_service_request_path,
)

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
    return tuple(spec.layer for spec in BOUNDARY_LAYER_CATALOG)


def list_boundary_values(layer: str) -> tuple[str, ...]:
    """List the canonical values available for one packaged boundary layer."""
    normalized_layer = normalize_boundary_layer(layer)
    boundaries = load_nyc_boundaries(normalized_layer)
    return tuple(feature.geography_value for feature in boundaries.features)


def load_nyc_boundaries(
    layer: str = "community_district",
    *,
    values: str | tuple[str, ...] | list[str] | None = None,
) -> BoundaryCollection:
    """Load a packaged NYC boundary layer as typed boundary models."""
    normalized_layer = normalize_boundary_layer(layer)
    boundary_collection = boundary_collection_from_geojson(
        load_boundary_payload(normalized_layer)
    )
    normalized_values = normalize_boundary_values(normalized_layer, values)
    if normalized_values is None:
        return boundary_collection

    requested_values = set(normalized_values)
    selected_features = tuple(
        feature
        for feature in boundary_collection.features
        if feature.geography_value in requested_values
    )
    if not selected_features:
        raise ValueError(
            "No boundaries matched the requested values for layer "
            f"{normalized_layer!r}: {normalized_values!r}."
        )
    return BoundaryCollection(geography=normalized_layer, features=selected_features)


def load_nyc_boundaries_geodataframe(
    layer: str = "community_district",
    *,
    values: str | tuple[str, ...] | list[str] | None = None,
) -> gpd.GeoDataFrame:
    """Load a packaged NYC boundary layer directly into a GeoDataFrame."""
    return _boundary_collection_to_geodataframe(
        load_nyc_boundaries(layer, values=values)
    )


def load_nyc_census_tracts(
    *,
    values: str | tuple[str, ...] | list[str] | None = None,
) -> BoundaryCollection:
    """Load the packaged NYC census-tract layer."""
    return load_nyc_boundaries("census_tract", values=values)


def load_nyc_neighborhood_tabulation_areas(
    *,
    values: str | tuple[str, ...] | list[str] | None = None,
) -> BoundaryCollection:
    """Load the packaged NYC neighborhood-tabulation-area layer."""
    return load_nyc_boundaries("neighborhood_tabulation_area", values=values)


def load_nyc_council_districts(
    *,
    values: str | tuple[str, ...] | list[str] | None = None,
) -> BoundaryCollection:
    """Load the packaged NYC city-council-district layer."""
    return load_nyc_boundaries("council_district", values=values)


def load_sample_service_requests(
    *,
    filters: ServiceRequestFilter | None = None,
) -> list[ServiceRequestRecord]:
    """Load the packaged sample NYC 311 service-request slice."""
    with sample_service_request_path() as sample_path:
        return load_service_requests_from_csv(
            sample_path,
            filters=filters or ServiceRequestFilter(),
        )


def load_sample_boundaries(layer: str = "community_district") -> BoundaryCollection:
    """Load the subset of packaged boundaries that overlaps the sample records."""
    normalized_layer = normalize_boundary_layer(layer)
    sample_boundary_values = load_sample_boundary_values()
    values = sample_boundary_values.get(normalized_layer)
    if values is None:
        raise ValueError(
            "No packaged sample boundaries are available for layer "
            f"{normalized_layer!r}."
        )
    return load_nyc_boundaries(normalized_layer, values=values)
