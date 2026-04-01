"""Optional geospatial helpers for example maps."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nyc311 import models, plotting, spatial

from .plotting import save_current_figure


def load_boundary_frame(source: str | Path) -> Any:
    """Load a boundary GeoDataFrame for example maps."""
    return spatial.load_boundaries_geodataframe(source)


def merge_summary_map(
    summaries: list[models.GeographyTopicSummary],
    *,
    boundaries_source: str | Path,
) -> Any:
    """Merge topic summaries onto boundary geometries."""
    return spatial.summaries_to_geodataframe(
        summaries,
        boundaries_gdf=load_boundary_frame(boundaries_source),
    )


def save_choropleth(
    geodataframe: Any,
    *,
    column: str,
    title: str,
    filename: str,
    cmap: str = "viridis",
    categorical: bool = False,
    add_basemap: bool = True,
) -> Path:
    """Render and save a choropleth map, optionally over a real basemap."""
    figure = plotting.plot_boundary_choropleth(
        geodataframe,
        column=column,
        title=title,
        cmap=cmap,
        categorical=categorical,
        add_basemap=add_basemap,
    )
    return save_current_figure(filename, figure)


def save_boundary_preview(
    boundaries_gdf: Any,
    *,
    filename: str,
    title: str,
    points_gdf: Any | None = None,
) -> Path:
    """Render boundary outlines, optionally with points, on a real basemap."""
    figure = plotting.plot_boundary_preview(
        boundaries_gdf,
        title=title,
        points_gdf=points_gdf,
        add_basemap=True,
    )
    return save_current_figure(filename, figure)
