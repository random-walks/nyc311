"""Models for packaged NYC geography resources."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BoundaryLayerSpec:
    """Metadata describing one packaged NYC boundary layer."""

    layer: str
    display_name: str
    resource_path: str
