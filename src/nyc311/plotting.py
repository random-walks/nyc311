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


def _apply_top_n_categorical_point_legend(
    axes: Any,
    *,
    point_frame: Any,
    column: str,
    top_n: int,
    legend_kwds: dict[str, Any] | None = None,
) -> None:
    """Keep all points/colors; show only the top-N categories in the legend (by row count)."""
    series = point_frame[column]
    vc = series.value_counts()
    top_cats = list(vc.head(top_n).index)
    leg = axes.get_legend()
    if leg is None:
        return
    handles = list(getattr(leg, "legend_handles", None) or getattr(leg, "legendHandles", []))
    texts = [t.get_text() for t in leg.get_texts()]
    n = min(len(handles), len(texts))
    by_label: dict[str, Any] = dict(zip(texts[:n], handles[:n], strict=True))

    def _resolve_handle(cat: Any) -> Any | None:
        s = str(cat)
        if s in by_label:
            return by_label[s]
        sl = s.lower()
        for k, h in by_label.items():
            if k.lower() == sl:
                return h
        return None

    nh: list[Any] = []
    nl: list[str] = []
    for cat in top_cats:
        handle = _resolve_handle(cat)
        if handle is None:
            continue
        nh.append(handle)
        lbl = str(cat)
        if len(lbl) > 72:
            lbl = lbl[:69] + "..."
        cnt = int(vc.loc[cat])
        nl.append(f"{lbl} ({cnt:,})")
    if not nh:
        _style_legend(axes)
        return
    default_kw: dict[str, Any] = {
        "bbox_to_anchor": (1.02, 1),
        "loc": "upper left",
        "frameon": True,
    }
    if legend_kwds:
        default_kw.update(legend_kwds)
    leg.remove()
    axes.legend(handles=nh, labels=nl, **default_kw)
    _style_legend(axes)
    n_other = max(0, len(vc) - top_n)
    if n_other > 0:
        fig = axes.figure
        fig.text(
            0.99,
            0.012,
            f"+ {n_other} other complaint types on map (same colors; not listed)",
            ha="right",
            fontsize=8,
            va="bottom",
            color="#444",
            transform=fig.transFigure,
        )


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
    if categorical:
        effective_legend_kwds: dict[str, Any] = {
            "loc": "upper left",
            "bbox_to_anchor": (1.02, 1),
            "frameon": True,
            "borderaxespad": 0.0,
        }
    else:
        # Continuous choropleth uses a matplotlib colorbar (not a legend).
        effective_legend_kwds = {"shrink": 0.72, "label": column}
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


def plot_timeseries(
    dataframe: Any,
    *,
    title: str,
    figsize: tuple[float, float] = (12, 5),
    footnote: str | None = None,
) -> Any:
    """Line chart for a :class:`~pandas.DataFrame` with a DatetimeIndex or ``created_date`` column."""
    plt = _require_matplotlib()
    pd = import_module("pandas")
    plt.style.use("seaborn-v0_8-whitegrid")
    _figure, axes = plt.subplots(figsize=figsize)
    plot_df = dataframe
    if isinstance(dataframe.index, pd.DatetimeIndex):
        plot_df = dataframe
    elif "created_date" in getattr(dataframe, "columns", ()):
        plot_df = dataframe.set_index("created_date").sort_index()
    else:
        plot_df = dataframe.copy()
    plot_df.plot(ax=axes, legend=True)
    axes.set_title(title, pad=12)
    axes.set_xlabel("")
    axes.grid(True, alpha=0.3)
    axes.figure.patch.set_facecolor("white")
    if footnote:
        fig = axes.figure
        fig.subplots_adjust(bottom=0.16)
        fig.text(
            0.5,
            0.02,
            footnote,
            ha="center",
            fontsize=8,
            color="#555",
            va="bottom",
            wrap=True,
        )
    return axes.figure


def plot_complaint_heatmap(
    dataframe: Any,
    *,
    title: str,
    time_column: str = "created_date",
    figsize: tuple[float, float] = (10, 6),
) -> Any:
    """Hour-of-day x day-of-week density heatmap (expects datetime resolution in ``time_column``)."""
    plt = _require_matplotlib()
    pd = import_module("pandas")
    np = import_module("numpy")
    plt.style.use("seaborn-v0_8-whitegrid")
    if time_column not in dataframe.columns:
        raise ValueError(f"DataFrame must include column {time_column!r}.")

    times = pd.to_datetime(dataframe[time_column])
    hour = times.dt.hour
    weekday = times.dt.dayofweek
    grid = (
        pd.DataFrame({"hour": hour, "weekday": weekday})
        .assign(n=1)
        .groupby(["weekday", "hour"], observed=False)["n"]
        .sum()
        .unstack(fill_value=0)
        .reindex(index=range(7), columns=range(24), fill_value=0)
    )
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    _figure, axes = plt.subplots(figsize=figsize)
    im = axes.imshow(np.asarray(grid), aspect="auto", cmap="YlOrRd", origin="lower")
    axes.set_xticks(range(0, 24, 2))
    axes.set_yticks(range(7))
    axes.set_yticklabels(labels)
    axes.set_xlabel("Hour of day")
    axes.set_ylabel("Weekday")
    axes.set_title(title, pad=12)
    plt.colorbar(im, ax=axes, fraction=0.046, pad=0.04, label="Complaints")
    axes.figure.patch.set_facecolor("white")
    return axes.figure


def plot_stacked_area(
    dataframe: Any,
    *,
    title: str,
    top_n: int = 8,
    figsize: tuple[float, float] = (12, 6),
) -> Any:
    """Stacked area chart of the top-N columns (by total) over a DatetimeIndex."""
    plt = _require_matplotlib()
    pd = import_module("pandas")
    plt.style.use("seaborn-v0_8-whitegrid")
    if not isinstance(dataframe.index, pd.DatetimeIndex):
        raise TypeError("plot_stacked_area() expects a DatetimeIndex-indexed DataFrame.")
    totals = dataframe.sum().sort_values(ascending=False)
    cols = list(totals.head(top_n).index)
    sub = dataframe[cols].fillna(0)
    if sub.shape[1] == 0:
        sub = dataframe.fillna(0)
    mdates = import_module("matplotlib.dates")
    _figure, axes = plt.subplots(figsize=figsize)
    xnum = mdates.date2num(pd.DatetimeIndex(sub.index).to_pydatetime())
    axes.stackplot(
        xnum,
        *[sub[c].to_numpy() for c in sub.columns],
        labels=list(sub.columns),
        alpha=0.85,
    )
    axes.xaxis_date()
    ax_fig = axes.figure
    ax_fig.autofmt_xdate()
    axes.legend(loc="upper left", bbox_to_anchor=(1.02, 1), frameon=True)
    axes.set_title(title, pad=12)
    axes.set_xlabel("")
    axes.grid(True, alpha=0.25)
    axes.figure.patch.set_facecolor("white")
    return axes.figure


def plot_bar_counts(
    labels: list[str],
    counts: list[float],
    *,
    title: str,
    horizontal: bool = False,
    figsize: tuple[float, float] = (10, 6),
) -> Any:
    """Simple bar chart for categorical counts."""
    plt = _require_matplotlib()
    plt.style.use("seaborn-v0_8-whitegrid")
    _figure, axes = plt.subplots(figsize=figsize)
    if horizontal:
        axes.barh(labels, counts, color="#3b82f6", edgecolor="#1e40af", linewidth=0.5)
    else:
        axes.bar(labels, counts, color="#3b82f6", edgecolor="#1e40af", linewidth=0.5)
        plt.setp(axes.xaxis.get_majorticklabels(), rotation=45, ha="right")
    axes.set_title(title, pad=12)
    axes.grid(True, axis="y", alpha=0.3)
    axes.figure.patch.set_facecolor("white")
    return axes.figure


def plot_complaint_scatter(
    points_gdf: Any,
    *,
    boundaries_gdf: Any | None = None,
    title: str,
    column: str = "complaint_type",
    add_basemap: bool = False,
    figsize: tuple[float, float] = (12, 10),
    legend_top_n: int | None = None,
) -> Any:
    """Scatter plot of points colored by ``column`` over optional boundary outlines."""
    plt = _require_matplotlib()
    plt.style.use("seaborn-v0_8-whitegrid")
    point_frame = _prepare_plot_frame(points_gdf, add_basemap=add_basemap)
    boundary_frame = _prepare_plot_frame(boundaries_gdf, add_basemap=add_basemap)
    if point_frame is None or point_frame.empty:
        raise TypeError("plot_complaint_scatter() requires a non-empty points GeoDataFrame.")

    _figure, axes = plt.subplots(figsize=figsize)
    scatter_legend_kwds = {"bbox_to_anchor": (1.02, 1), "loc": "upper left"}
    if boundary_frame is not None and not boundary_frame.empty:
        boundary_frame.boundary.plot(ax=axes, color="#0f172a", linewidth=0.8, alpha=0.7)
    point_frame.plot(
        ax=axes,
        column=column,
        legend=True,
        markersize=12,
        alpha=0.5,
        categorical=True,
        cmap="tab20",
        legend_kwds=scatter_legend_kwds,
    )
    if add_basemap:
        contextily = _require_contextily()
        contextily.add_basemap(
            axes,
            source=contextily.providers.CartoDB.Positron,
            attribution_size=6,
        )
    if legend_top_n is not None:
        _apply_top_n_categorical_point_legend(
            axes,
            point_frame=point_frame,
            column=column,
            top_n=legend_top_n,
            legend_kwds=scatter_legend_kwds,
        )
    else:
        _style_legend(axes)
    _finish_axes(axes, title=title)
    return axes.figure


def plot_hero_banner(
    points_gdf: Any,
    *,
    boundaries_gdf: Any | None = None,
    title: str,
    bbox: tuple[float, float, float, float] | None = None,
    column: str = "complaint_type",
    figsize: tuple[float, float] = (16, 5),
    legend_top_n: int | None = None,
) -> Any:
    """Wide horizontal map with OSM basemap, points, and boundaries (Web Mercator)."""
    plt = _require_matplotlib()
    plt.style.use("seaborn-v0_8-whitegrid")
    point_frame = points_gdf
    boundary_frame = boundaries_gdf
    if bbox is not None:
        minx, miny, maxx, maxy = bbox
        point_frame = points_gdf.cx[minx:maxx, miny:maxy]
        if boundaries_gdf is not None:
            boundary_frame = boundaries_gdf.cx[minx:maxx, miny:maxy]

    point_frame = _prepare_plot_frame(point_frame, add_basemap=True)
    boundary_frame = _prepare_plot_frame(boundary_frame, add_basemap=True)
    if point_frame is None or point_frame.empty:
        raise TypeError("plot_hero_banner() requires a non-empty points GeoDataFrame.")

    _figure, axes = plt.subplots(figsize=figsize)
    hero_legend_kwds = {"bbox_to_anchor": (1.01, 1), "loc": "upper left", "fontsize": 8}
    if boundary_frame is not None and not boundary_frame.empty:
        boundary_frame.boundary.plot(ax=axes, color="#0f172a", linewidth=0.9, alpha=0.85)
    point_frame.plot(
        ax=axes,
        column=column,
        legend=True,
        markersize=8,
        alpha=0.65,
        categorical=True,
        cmap="tab20",
        legend_kwds=hero_legend_kwds,
    )
    contextily = _require_contextily()
    contextily.add_basemap(
        axes,
        source=contextily.providers.CartoDB.Positron,
        attribution_size=5,
    )
    if legend_top_n is not None:
        _apply_top_n_categorical_point_legend(
            axes,
            point_frame=point_frame,
            column=column,
            top_n=legend_top_n,
            legend_kwds=hero_legend_kwds,
        )
    else:
        _style_legend(axes)
    axes.set_axis_off()
    axes.set_title(title, pad=10, fontsize=14, fontweight="600")
    axes.figure.patch.set_facecolor("white")
    return axes.figure


__all__ = [
    "plot_bar_counts",
    "plot_boundary_choropleth",
    "plot_boundary_preview",
    "plot_boundary_point_groups",
    "plot_complaint_heatmap",
    "plot_complaint_scatter",
    "plot_hero_banner",
    "plot_stacked_area",
    "plot_timeseries",
]
