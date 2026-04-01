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


def _prepare_plot_frame(geodataframe: Any | None, *, add_basemap: bool) -> Any | None:
    if geodataframe is None:
        return None
    return _web_map_frame(geodataframe) if add_basemap else geodataframe


def _finish_axes(axes: Any, *, title: str) -> None:
    axes.set_axis_off()
    axes.set_title(title, pad=12)
    axes.set_facecolor("#f8fafc")
    axes.figure.patch.set_facecolor("white")
    axes.margins(0.02)


def _style_legend(axes: Any, *, title: str | None = None) -> None:
    legend = axes.get_legend()
    if legend is None:
        return
    if title is not None:
        legend.set_title(title)
    frame = legend.get_frame()
    if frame is not None:
        frame.set_facecolor("white")
        frame.set_edgecolor("#cbd5e1")
        frame.set_alpha(0.96)


def plot_boundary_choropleth(
    geodataframe: Any,
    *,
    column: str,
    title: str,
    cmap: str = "viridis",
    categorical: bool = False,
    add_basemap: bool = False,
    figsize: tuple[float, float] = (10, 8),
    outline_gdf: Any | None = None,
    legend_title: str | None = None,
    legend_kwds: dict[str, Any] | None = None,
) -> Any:
    """Render a choropleth map and return the matplotlib figure."""
    plt = _require_matplotlib()
    plt.style.use("seaborn-v0_8-whitegrid")
    plot_gdf = _prepare_plot_frame(geodataframe, add_basemap=add_basemap)
    outline_frame = _prepare_plot_frame(outline_gdf, add_basemap=add_basemap)
    figure, axes = plt.subplots(figsize=figsize)
    effective_legend_kwds = {
        "loc": "upper left",
        "bbox_to_anchor": (1.02, 1),
        "frameon": True,
        "borderaxespad": 0.0,
    }
    if legend_kwds is not None:
        effective_legend_kwds.update(legend_kwds)
    plot_gdf.plot(
        ax=axes,
        column=column,
        legend=True,
        cmap=cmap,
        categorical=categorical,
        edgecolor="#334155",
        linewidth=0.7,
        alpha=0.7 if add_basemap else 1.0,
        missing_kwds={
            "color": "#d4d4d8",
            "label": "No data",
            "edgecolor": "#94a3b8",
        },
        legend_kwds=effective_legend_kwds,
    )
    if outline_frame is not None:
        outline_frame.boundary.plot(
            ax=axes,
            color="#0f172a",
            linewidth=1.15 if not add_basemap else 0.9,
            alpha=0.75,
        )
    axes.set_axis_off()
    if add_basemap:
        contextily = _require_contextily()
        contextily.add_basemap(
            axes,
            source=contextily.providers.CartoDB.Positron,
            attribution_size=6,
        )
    _style_legend(axes, title=legend_title)
    _finish_axes(axes, title=title)
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
    boundary_frame = _prepare_plot_frame(boundaries_gdf, add_basemap=add_basemap)
    point_frame = _prepare_plot_frame(points_gdf, add_basemap=add_basemap)

    figure, axes = plt.subplots(figsize=figsize)
    boundary_frame.boundary.plot(
        ax=axes,
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
    _finish_axes(axes, title=title)
    return axes.figure


def plot_boundary_point_groups(
    boundaries_gdf: Any,
    *,
    title: str,
    matched_points_gdf: Any | None = None,
    unmatched_points_gdf: Any | None = None,
    context_gdf: Any | None = None,
    outline_gdf: Any | None = None,
    matched_label: str = "Matched",
    unmatched_label: str = "Unmatched",
    add_basemap: bool = False,
    figsize: tuple[float, float] = (10, 8),
) -> Any:
    """Render categorized points over highlighted boundaries and optional context."""
    plt = _require_matplotlib()
    plt.style.use("seaborn-v0_8-whitegrid")
    boundary_frame = _prepare_plot_frame(boundaries_gdf, add_basemap=add_basemap)
    context_frame = _prepare_plot_frame(context_gdf, add_basemap=add_basemap)
    outline_frame = _prepare_plot_frame(outline_gdf, add_basemap=add_basemap)
    matched_frame = _prepare_plot_frame(matched_points_gdf, add_basemap=add_basemap)
    unmatched_frame = _prepare_plot_frame(unmatched_points_gdf, add_basemap=add_basemap)

    figure, axes = plt.subplots(figsize=figsize)
    if context_frame is not None and not context_frame.empty:
        context_frame.plot(
            ax=axes,
            color="#f1f5f9",
            edgecolor="#cbd5e1",
            linewidth=0.5,
        )
    boundary_frame.boundary.plot(
        ax=axes,
        color="#334155",
        linewidth=1.25,
    )
    if outline_frame is not None and not outline_frame.empty:
        outline_frame.boundary.plot(
            ax=axes,
            color="#0f172a",
            linewidth=1.15 if not add_basemap else 0.9,
            alpha=0.75,
        )
    if matched_frame is not None and not matched_frame.empty:
        matched_frame.plot(
            ax=axes,
            color="#16a34a",
            markersize=42,
            alpha=0.85,
            label=matched_label,
        )
    if unmatched_frame is not None and not unmatched_frame.empty:
        unmatched_frame.plot(
            ax=axes,
            color="#dc2626",
            markersize=56,
            marker="x",
            linewidth=1.5,
            label=unmatched_label,
        )
    if add_basemap:
        contextily = _require_contextily()
        contextily.add_basemap(
            axes,
            source=contextily.providers.CartoDB.Positron,
            attribution_size=6,
        )
    axes.legend(loc="lower left", frameon=True)
    _style_legend(axes)
    _finish_axes(axes, title=title)
    return figure


__all__ = [
    "plot_boundary_choropleth",
    "plot_boundary_preview",
    "plot_boundary_point_groups",
]
