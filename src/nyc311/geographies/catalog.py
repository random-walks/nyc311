"""Catalog of packaged NYC geography layers."""

from __future__ import annotations

from typing import Final

from .models import BoundaryLayerSpec

BOUNDARY_LAYER_CATALOG: Final[tuple[BoundaryLayerSpec, ...]] = (
    BoundaryLayerSpec(
        layer="borough",
        display_name="NYC borough boundaries",
        resource_path="data/boundaries/borough.geojson",
    ),
    BoundaryLayerSpec(
        layer="community_district",
        display_name="NYC community district boundaries",
        resource_path="data/boundaries/community_district.geojson",
    ),
    BoundaryLayerSpec(
        layer="council_district",
        display_name="NYC city council district boundaries",
        resource_path="data/boundaries/council_district.geojson",
    ),
    BoundaryLayerSpec(
        layer="neighborhood_tabulation_area",
        display_name="NYC neighborhood tabulation areas",
        resource_path="data/boundaries/neighborhood_tabulation_area.geojson",
    ),
    BoundaryLayerSpec(
        layer="zcta",
        display_name="NYC modified ZIP Code Tabulation Areas",
        resource_path="data/boundaries/zcta.geojson",
    ),
    BoundaryLayerSpec(
        layer="census_tract",
        display_name="NYC census tracts",
        resource_path="data/boundaries/census_tract.geojson",
    ),
)

BOUNDARY_LAYER_LOOKUP: Final[dict[str, BoundaryLayerSpec]] = {
    spec.layer: spec for spec in BOUNDARY_LAYER_CATALOG
}
