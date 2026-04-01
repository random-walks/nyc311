"""Loaders for packaged nyc311 sample datasets."""

from __future__ import annotations

from ..geographies import load_nyc_boundaries
from ..geographies._normalize import normalize_boundary_layer
from ..geographies._resources import (
    load_sample_boundary_values,
    sample_service_request_path,
)
from ..io import load_service_requests_from_csv
from ..models import BoundaryCollection, ServiceRequestFilter, ServiceRequestRecord


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
