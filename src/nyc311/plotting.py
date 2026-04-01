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


def _point_style(point_count: int, *, matched: bool) -> dict[str, float]:
    if point_count >= 10_000:
        return {
            "markersize": 5.0 if matched else 20.0,
            "alpha": 0.2 if matched else 0.95,
            "linewidth": 0.9,
        }
    if point_count >= 3_000:
        return {
            "markersize": 8.0 if matched else 24.0,
            "alpha": 0.28 if matched else 0.95,
            "linewidth": 1.0,
        }
    if point_count >= 1_000:
        return {
            "markersize": 12.0 if matched else 30.0,
            "alpha": 0.4 if matched else 0.95,
            "linewidth": 1.1,
        }
    return {
        "markersize": 28.0 if matched else 44.0,
        "alpha": 0.78 if matched else 0.95,
        "linewidth": 1.4,
    }


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
    if plot_gdf is None:
        raise TypeError("plot_boundary_choropleth() requires a geodataframe.")
    _figure, axes = plt.subplots(figsize=figsize)
    effective_legend_kwds = {
        "loc": "upper left",
        "bbox_to_anchor": (1.02, 1),
        "frameon": True,
        "borderaxespad": 0.0,
    }
    if legend_kwds is not None:
        effective_legend_kwds.update(legend_kwds)
    missing_mask = plot_gdf[column].isna()
    missing_frame = plot_gdf[missing_mask]
    data_frame = plot_gdf[~missing_mask]
    if not data_frame.empty:
        data_frame.plot(
            ax=axes,
            column=column,
            legend=True,
            cmap=cmap,
            categorical=categorical,
            edgecolor="#334155",
            linewidth=0.7,
            alpha=0.7 if add_basemap else 1.0,
            legend_kwds=effective_legend_kwds,
        )
    if not missing_frame.empty:
        missing_frame.plot(
            ax=axes,
            color="#d4d4d8",
            edgecolor="#94a3b8",
            linewidth=0.7,
        )
        legend = axes.get_legend()
        if categorical and legend is not None:
            matplotlib_patches = import_module("matplotlib.patches")
            handles = list(legend.legend_handles)
            labels = [text.get_text() for text in legend.get_texts()]
            handles.append(
                matplotlib_patches.Patch(
                    facecolor="#d4d4d8",
                    edgecolor="#94a3b8",
                    label="No data",
                )
            )
            labels.append("No data")
            legend.remove()
            axes.legend(handles, labels, **effective_legend_kwds)
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
    if boundary_frame is None:
        raise TypeError("plot_boundary_preview() requires boundaries_gdf.")

    _figure, axes = plt.subplots(figsize=figsize)
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
    if boundary_frame is None:
        raise TypeError("plot_boundary_point_groups() requires boundaries_gdf.")

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
        matched_style = _point_style(len(matched_frame), matched=True)
        matched_frame.plot(
            ax=axes,
            color="#16a34a",
            markersize=matched_style["markersize"],
            alpha=matched_style["alpha"],
            label=matched_label,
        )
    if unmatched_frame is not None and not unmatched_frame.empty:
        unmatched_style = _point_style(len(unmatched_frame), matched=False)
        unmatched_frame.plot(
            ax=axes,
            color="#dc2626",
            markersize=unmatched_style["markersize"],
            marker="x",
            linewidth=unmatched_style["linewidth"],
            alpha=unmatched_style["alpha"],
            label=unmatched_label,
        )
    if add_basemap:
        contextily = _require_contextily()
        contextily.add_basemap(
            axes,
            source=contextily.providers.CartoDB.Positron,
            attribution_size=6,
        )
    legend_handles, _legend_labels = axes.get_legend_handles_labels()
    if legend_handles:
        axes.legend(loc="lower left", frameon=True)
        _style_legend(axes)
    _finish_axes(axes, title=title)
    return figure


__all__ = [
    "plot_boundary_choropleth",
    "plot_boundary_preview",
    "plot_boundary_point_groups",
]
