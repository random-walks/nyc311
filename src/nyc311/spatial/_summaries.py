"""Summary GeoDataFrame helpers for nyc311.spatial."""

from __future__ import annotations

from typing import Any

from ..dataframes import summaries_to_dataframe
from ._boundaries import load_boundaries_geodataframe
from ._deps import require_geospatial_stack


def summaries_to_geodataframe(
    summaries: list[Any],
    boundaries_gdf: Any = None,
    *,
    layer: str | None = None,
) -> Any:
    """Merge aggregated geography summaries onto boundary geometries."""
    geopandas, _ = require_geospatial_stack()
    if boundaries_gdf is None:
        if layer is None:
            if not summaries:
                raise ValueError(
                    "summaries_to_geodataframe() requires boundaries_gdf or layer "
                    "when summaries is empty."
                )
            layer = summaries[0].geography
        boundaries_gdf = load_boundaries_geodataframe(layer=layer)
    if "geography" not in boundaries_gdf.columns:
        raise ValueError("boundaries_gdf must include a geography column.")
    if "geography_value" not in boundaries_gdf.columns:
        raise ValueError("boundaries_gdf must include a geography_value column.")

    summary_dataframe = summaries_to_dataframe(summaries)
    merged = boundaries_gdf.merge(
        summary_dataframe,
        on=["geography", "geography_value"],
        how="left",
    )
    return geopandas.GeoDataFrame(merged, geometry="geometry", crs=boundaries_gdf.crs)
