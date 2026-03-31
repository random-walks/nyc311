"""Optional geospatial helpers for example maps."""

from __future__ import annotations

from importlib import import_module
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


def _require_contextily() -> Any:
    """Import contextily on demand for basemap-backed example maps."""
    try:
        return import_module("contextily")
    except ImportError as exc:  # pragma: no cover - optional dependency path
        raise ImportError(
            "contextily is required for basemap-backed example maps. "
            "Install it with `pip install nyc311[spatial]` or "
            "`pip install contextily`."
        ) from exc


def _web_map_frame(geodataframe: Any) -> Any:
    """Project a GeoDataFrame to Web Mercator for tiled basemaps."""
    return geodataframe.to_crs(epsg=3857)


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
    plt = configure_matplotlib_style()
    plot_gdf = _web_map_frame(geodataframe) if add_basemap else geodataframe
    axes = plot_gdf.plot(
        column=column,
        legend=True,
        cmap=cmap,
        categorical=categorical,
        figsize=(10, 8),
        edgecolor="black",
        linewidth=0.5,
        alpha=0.7 if add_basemap else 1.0,
        missing_kwds={"color": "lightgrey", "label": "No data"},
    )
    axes.set_axis_off()
    axes.set_title(title)
    if add_basemap:
        contextily = _require_contextily()
        contextily.add_basemap(
            axes,
            source=contextily.providers.CartoDB.Positron,
            attribution_size=6,
        )
    return save_current_figure(filename, axes.figure)


def save_boundary_preview(
    boundaries_gdf: Any,
    *,
    filename: str,
    title: str,
    points_gdf: Any | None = None,
) -> Path:
    """Render boundary outlines, optionally with points, on a real basemap."""
    plt = configure_matplotlib_style()
    contextily = _require_contextily()
    boundary_frame = _web_map_frame(boundaries_gdf)
    point_frame = None if points_gdf is None else _web_map_frame(points_gdf)

    axes = boundary_frame.boundary.plot(figsize=(10, 8), color="#1f2937", linewidth=1.25)
    if point_frame is not None and not point_frame.empty:
        point_frame.plot(
            ax=axes,
            color="#dc2626",
            markersize=18,
            alpha=0.8,
        )
    contextily.add_basemap(
        axes,
        source=contextily.providers.CartoDB.Positron,
        attribution_size=6,
    )
    axes.set_axis_off()
    axes.set_title(title)
    return save_current_figure(filename, axes.figure)
