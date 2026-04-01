"""Optional in-memory plotting helpers for NYC boundary maps."""

from __future__ import annotations

from importlib import import_module
from typing import Any


def _require_matplotlib() -> Any:
    try:
        return import_module("matplotlib.pyplot")
    except ImportError as exc:  # pragma: no cover - optional dependency path
        raise ImportError(
            "matplotlib is required for nyc311 plotting helpers. "
            "Install it with `pip install nyc311[plotting]`, "
            "`pip install nyc311[science]`, or `pip install matplotlib`."
        ) from exc


def _require_contextily() -> Any:
    try:
        return import_module("contextily")
    except ImportError as exc:  # pragma: no cover - optional dependency path
        raise ImportError(
            "contextily is required when add_basemap=True. "
            "Install it with `pip install nyc311[spatial]` or `pip install contextily`."
        ) from exc


def _web_map_frame(geodataframe: Any) -> Any:
    return geodataframe.to_crs(epsg=3857)


def plot_boundary_choropleth(
    geodataframe: Any,
    *,
    column: str,
    title: str,
    cmap: str = "viridis",
    categorical: bool = False,
    add_basemap: bool = False,
    figsize: tuple[float, float] = (10, 8),
) -> Any:
    """Render a choropleth map and return the matplotlib figure."""
    plt = _require_matplotlib()
    plt.style.use("seaborn-v0_8-whitegrid")
    plot_gdf = _web_map_frame(geodataframe) if add_basemap else geodataframe
    axes = plot_gdf.plot(
        column=column,
        legend=True,
        cmap=cmap,
        categorical=categorical,
        figsize=figsize,
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
    return axes.figure


def plot_boundary_preview(
    boundaries_gdf: Any,
    *,
    title: str,
    points_gdf: Any | None = None,
    add_basemap: bool = False,
    figsize: tuple[float, float] = (10, 8),
) -> Any:
    """Render boundary outlines and optional points, then return the figure."""
    plt = _require_matplotlib()
    plt.style.use("seaborn-v0_8-whitegrid")
    boundary_frame = _web_map_frame(boundaries_gdf) if add_basemap else boundaries_gdf
    point_frame = None
    if points_gdf is not None:
        point_frame = _web_map_frame(points_gdf) if add_basemap else points_gdf

    axes = boundary_frame.boundary.plot(
        figsize=figsize,
        color="#1f2937",
        linewidth=1.25,
    )
    if point_frame is not None and not point_frame.empty:
        point_frame.plot(
            ax=axes,
            color="#dc2626",
            markersize=18,
            alpha=0.8,
        )
    if add_basemap:
        contextily = _require_contextily()
        contextily.add_basemap(
            axes,
            source=contextily.providers.CartoDB.Positron,
            attribution_size=6,
        )
    axes.set_axis_off()
    axes.set_title(title)
    return axes.figure


__all__ = [
    "plot_boundary_choropleth",
    "plot_boundary_preview",
]
