"""Packaged NYC geography layers and sample data."""

from __future__ import annotations

from .conversions import boundaries_to_dataframe, boundaries_to_geojson
from .loaders import (
    list_boundary_layers,
    list_boundary_values,
    load_nyc_boundaries,
    load_nyc_boundaries_geodataframe,
    load_nyc_census_tracts,
    load_nyc_council_districts,
    load_nyc_neighborhood_tabulation_areas,
    load_sample_boundaries,
    load_sample_service_requests,
)
from .ops import clip_boundaries_to_bbox, spatially_enrich_records

__all__ = [
    "boundaries_to_dataframe",
    "boundaries_to_geojson",
    "clip_boundaries_to_bbox",
    "list_boundary_layers",
    "list_boundary_values",
    "load_nyc_boundaries",
    "load_nyc_council_districts",
    "load_nyc_census_tracts",
    "load_nyc_boundaries_geodataframe",
    "load_nyc_neighborhood_tabulation_areas",
    "load_sample_boundaries",
    "load_sample_service_requests",
    "spatially_enrich_records",
]
