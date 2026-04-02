"""Normalization wrappers for packaged NYC geography layers and values."""

from __future__ import annotations

from collections.abc import Iterable

from nyc_geo_toolkit import (
    normalize_boundary_layer as _normalize_boundary_layer,
)
from nyc_geo_toolkit import (
    normalize_boundary_value as _normalize_boundary_value,
)
from nyc_geo_toolkit import (
    normalize_boundary_values as _normalize_boundary_values,
)


def _normalize_space(value: str) -> str:
    return " ".join(value.strip().replace("-", " ").replace("_", " ").split())


def normalize_boundary_layer(layer: str) -> str:
    """Normalize a user-facing boundary layer identifier to the canonical key."""
    return _normalize_boundary_layer(layer)


def normalize_boundary_value(layer: str, value: str) -> str:
    """Normalize one boundary value for a packaged NYC boundary layer."""
    return _normalize_boundary_value(layer, value)


def normalize_boundary_values(
    layer: str, values: str | Iterable[str] | None
) -> tuple[str, ...] | None:
    """Normalize and de-duplicate one or more boundary values."""
    return _normalize_boundary_values(layer, values)
