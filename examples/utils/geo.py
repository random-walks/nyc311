"""Optional geospatial helpers for example maps."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import nyc311

from .plotting import configure_matplotlib_style, save_current_figure


def load_boundary_frame(source: str | Path) -> Any:
    """Load a boundary GeoDataFrame for example maps."""
    return nyc311.load_boundaries_geodataframe(source)


def merge_summary_map(
    summaries: list[nyc311.GeographyTopicSummary],
    *,
    boundaries_source: str | Path,
) -> Any:
    """Merge topic summaries onto boundary geometries."""
    boundaries_gdf = load_boundary_frame(boundaries_source)
    return nyc311.summaries_to_geodataframe(summaries, boundaries_gdf)


def save_choropleth(
    geodataframe: Any,
    *,
    column: str,
    title: str,
    filename: str,
    cmap: str = "viridis",
    categorical: bool = False,
) -> Path:
    """Render and save a simple choropleth map."""
    plt = configure_matplotlib_style()
    axes = geodataframe.plot(
        column=column,
        legend=True,
        cmap=cmap,
        categorical=categorical,
        figsize=(10, 8),
        edgecolor="black",
        linewidth=0.5,
        missing_kwds={"color": "lightgrey", "label": "No data"},
    )
    axes.set_axis_off()
    axes.set_title(title)
    return save_current_figure(filename, axes.figure)
