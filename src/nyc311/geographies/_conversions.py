"""Compatibility conversions backed by nyc_geo_toolkit."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nyc_geo_toolkit import (
    boundaries_to_dataframe as toolkit_boundaries_to_dataframe,
)
from nyc_geo_toolkit import (
    boundaries_to_geojson as toolkit_boundaries_to_geojson,
)

from ..models import BoundaryCollection

if TYPE_CHECKING:
    import pandas as pd  # type: ignore[import-untyped]


def boundaries_to_geojson(boundaries: BoundaryCollection) -> dict[str, object]:
    """Convert a typed boundary collection into a GeoJSON FeatureCollection."""
    return toolkit_boundaries_to_geojson(boundaries)


def boundaries_to_dataframe(boundaries: BoundaryCollection) -> pd.DataFrame:
    """Convert a typed boundary collection into a DataFrame."""
    try:
        return toolkit_boundaries_to_dataframe(boundaries)
    except ImportError as exc:  # pragma: no cover - exercised in optional tests
        raise ImportError(
            "pandas is required for nyc311 geography dataframe helpers. "
            "Install it with `pip install nyc311[dataframes]`, "
            "`pip install nyc311[science]`, or `pip install pandas`."
        ) from exc
