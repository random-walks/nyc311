"""Parse supported GeoJSON boundary files into nyc311 boundary models.

Boundary-backed exports are intentionally narrow, so this module keeps the
parsing rules explicit: a feature collection must provide supported geography
metadata that downstream exports can join against aggregated topic summaries.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from .models import BoundaryCollection, BoundaryFeature

_GEOJSON_REQUIRED_KEYS: Final[tuple[str, ...]] = ("type", "features")


def boundary_collection_from_geojson(payload: object) -> BoundaryCollection:
    """Parse a GeoJSON payload into a typed boundary collection."""
    if not isinstance(payload, dict):
        raise ValueError("Boundary file must be a GeoJSON object.")
    missing_keys = [key for key in _GEOJSON_REQUIRED_KEYS if key not in payload]
    if missing_keys:
        missing = ", ".join(missing_keys)
        raise ValueError(f"Boundary GeoJSON is missing required keys: {missing}.")
    if payload.get("type") != "FeatureCollection":
        raise ValueError("Boundary GeoJSON must be a FeatureCollection.")

    raw_features = payload.get("features")
    if not isinstance(raw_features, list):
        raise ValueError("Boundary GeoJSON features must be a list.")

    features: list[BoundaryFeature] = []
    for raw_feature in raw_features:
        if not isinstance(raw_feature, dict):
            raise ValueError("Each boundary feature must be a GeoJSON object.")
        properties = raw_feature.get("properties")
        geometry = raw_feature.get("geometry")
        if not isinstance(properties, dict):
            raise ValueError("Boundary feature properties must be an object.")
        if not isinstance(geometry, dict):
            raise ValueError("Boundary feature geometry must be an object.")

        geography = properties.get("geography")
        geography_value = properties.get("geography_value")
        if not isinstance(geography, str) or not isinstance(geography_value, str):
            raise ValueError(
                "Boundary feature properties must include string geography and geography_value."
            )

        features.append(
            BoundaryFeature(
                geography=geography,
                geography_value=geography_value,
                geometry=geometry,
                properties={
                    key: value
                    for key, value in properties.items()
                    if key not in {"geography", "geography_value"}
                },
            )
        )

    if not features:
        raise ValueError("Boundary GeoJSON must contain at least one feature.")
    geography = features[0].geography
    return BoundaryCollection(geography=geography, features=tuple(features))


def load_boundary_collection(source: str | Path) -> BoundaryCollection:
    """Load simple GeoJSON polygon features for supported geographies."""
    source_path = Path(source)
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    return boundary_collection_from_geojson(payload)
