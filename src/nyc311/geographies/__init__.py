"""Public access to packaged NYC geography layers and boundary helpers."""

from __future__ import annotations

from ._conversions import boundaries_to_dataframe, boundaries_to_geojson
from ._loaders import (
    list_boundary_layers,
    list_boundary_values,
    load_boundaries,
    load_nyc_boundaries,
    load_nyc_boundaries_geodataframe,
    load_nyc_census_tracts,
    load_nyc_council_districts,
    load_nyc_neighborhood_tabulation_areas,
)
from ._ops import clip_boundaries_to_bbox, spatially_enrich_records

__all__ = [
    "boundaries_to_dataframe",
    "boundaries_to_geojson",
    "clip_boundaries_to_bbox",
    "list_boundary_layers",
    "list_boundary_values",
    "load_boundaries",
    "load_nyc_boundaries",
    "load_nyc_council_districts",
    "load_nyc_census_tracts",
    "load_nyc_boundaries_geodataframe",
    "load_nyc_neighborhood_tabulation_areas",
    "spatially_enrich_records",
]
