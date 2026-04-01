"""Optional geospatial dependency helpers for nyc311.spatial."""

from __future__ import annotations

from importlib import import_module
from typing import Any


def require_geospatial_stack() -> tuple[Any, Any]:
    """Import the optional geospatial stack on demand."""
    try:
        geopandas = import_module("geopandas")
        shapely_geometry = import_module("shapely.geometry")
    except ImportError as exc:  # pragma: no cover - exercised via importorskip tests
        raise ImportError(
            "geopandas and shapely are required for nyc311.spatial helpers. "
            "Install them with `pip install nyc311[spatial]` or "
            "`pip install geopandas shapely`."
        ) from exc
    return geopandas, shapely_geometry
