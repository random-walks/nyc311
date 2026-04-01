"""Conversions for typed boundary collections."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from ..models import BoundaryCollection

if TYPE_CHECKING:
    import pandas as pd  # type: ignore[import-untyped]


def _require_pandas() -> Any:
    try:
        return import_module("pandas")
    except ImportError as exc:  # pragma: no cover - exercised in optional tests
        raise ImportError(
            "pandas is required for nyc311 geography dataframe helpers. "
            "Install it with `pip install nyc311[dataframes]`, "
            "`pip install nyc311[science]`, or `pip install pandas`."
        ) from exc


def boundaries_to_geojson(boundaries: BoundaryCollection) -> dict[str, object]:
    """Convert a typed boundary collection into a GeoJSON FeatureCollection."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "geography": feature.geography,
                    "geography_value": feature.geography_value,
                    **feature.properties,
                },
                "geometry": feature.geometry,
            }
            for feature in boundaries.features
        ],
    }


def boundaries_to_dataframe(boundaries: BoundaryCollection) -> pd.DataFrame:
    """Convert a typed boundary collection into a DataFrame."""
    pd = _require_pandas()
    return pd.DataFrame.from_records(
        [
            {
                "geography": feature.geography,
                "geography_value": feature.geography_value,
                **feature.properties,
                "geometry": feature.geometry,
            }
            for feature in boundaries.features
        ]
    )
