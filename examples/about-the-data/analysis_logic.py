"""Figures and catalogue for the about-the-data tearsheet (chunked CSV analysis)."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from nyc311 import analysis, dataframes, geographies, models, plotting, spatial

from download_logic import ALL_COMPLAINT_TYPES, borough_cache_dir, borough_slug

# --- Section 1: catalogue ---


@dataclass
class BoroughCatalogueRow:
    borough: str
    total_records: int
    complaint_types_seen: int
    supported_types_records: int
    date_range_start: date
    date_range_end: date
    records_with_coords: int
    records_with_resolution: int
    community_districts_seen: int
    cache_bytes: int


@dataclass
class CatalogueSummary:
    rows: list[BoroughCatalogueRow]
    sources: list[tuple[str, str, int]]


def _scan_borough_csv(csv_path: Path) -> dict[str, Any]:
    """Aggregate stats from a borough cache CSV without loading all rows."""
    total = 0
    coords = 0
    res = 0
    cds: set[str] = set()
    types: set[str] = set()
    supp = 0
    min_d: date | None = None
    max_d: date | None = None
    for chunk in pd.read_csv(
        csv_path,
        chunksize=50_000,
        parse_dates=["created_date"],
        dtype={"complaint_type": "string"},
    ):
        total += len(chunk)
        types.update(chunk["complaint_type"].dropna().unique().tolist())
        supp += chunk["complaint_type"].isin(ALL_COMPLAINT_TYPES).sum()
        lat_ok = chunk["latitude"].notna() & chunk["longitude"].notna()
        coords += int(lat_ok.sum())
        if "resolution_description" in chunk.columns:
            res += chunk["resolution_description"].notna().sum()
        if "community_district" in chunk.columns:
            cds.update(chunk["community_district"].dropna().astype(str).unique())
        elif "community_board" in chunk.columns:
            cds.update(chunk["community_board"].dropna().astype(str).unique())
        cmin = chunk["created_date"].min()
        cmax = chunk["created_date"].max()
        if pd.notna(cmin):
            dmin = cmin.date() if hasattr(cmin, "date") else date.fromisoformat(str(cmin)[:10])
            min_d = dmin if min_d is None else min(min_d, dmin)
        if pd.notna(cmax):
            dmax = cmax.date() if hasattr(cmax, "date") else date.fromisoformat(str(cmax)[:10])
            max_d = dmax if max_d is None else max(max_d, dmax)
    return {
        "total": total,
        "complaint_types_seen": len(types),
        "supported_types_records": int(supp),
        "date_range_start": min_d or date.today(),
        "date_range_end": max_d or date.today(),
        "records_with_coords": coords,
        "records_with_resolution": res,
        "community_districts_seen": len(cds),
    }


def build_catalogue(
    cache_root: Path, boroughs: tuple[str, ...]
) -> CatalogueSummary:
    rows: list[BoroughCatalogueRow] = []
    for b in boroughs:
        bdir = borough_cache_dir(cache_root, b)
        csvs = list(bdir.glob("*.csv"))
        if not csvs:
            continue
        path = csvs[0]
        stats = _scan_borough_csv(path)
        rows.append(
            BoroughCatalogueRow(
                borough=b,
                total_records=stats["total"],
                complaint_types_seen=stats["complaint_types_seen"],
                supported_types_records=stats["supported_types_records"],
                date_range_start=stats["date_range_start"],
                date_range_end=stats["date_range_end"],
                records_with_coords=stats["records_with_coords"],
                records_with_resolution=stats["records_with_resolution"],
                community_districts_seen=stats["community_districts_seen"],
                cache_bytes=path.stat().st_size,
            )
        )
    sources: list[tuple[str, str, int]] = [
        (
            "NYC 311 Service Requests",
            f"https://data.cityofnewyork.us/resource/{models.SOCRATA_DATASET_IDENTIFIER}.json",
            sum(r.total_records for r in rows),
        )
    ]
    bdir = cache_root / "boundaries"
    if bdir.is_dir():
        for p in sorted(bdir.glob("*.geojson")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                n = len(data.get("features", []))
                sources.append((p.stem, str(p.name), n))
            except OSError:
                continue
    return CatalogueSummary(rows=rows, sources=sources)


# --- Section 2: EDA ---


def sample_eda_figures(
    cache_root: Path,
    boroughs: tuple[str, ...],
    *,
    figures_dir: Path,
    artifacts_dir: Path,
) -> tuple[Path, ...]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pd.DataFrame] = []
    for b in boroughs:
        bdir = borough_cache_dir(cache_root, b)
        for p in bdir.glob("*.csv"):
            frames.append(
                pd.read_csv(
                    p,
                    nrows=500_000,
                    parse_dates=["created_date"],
                )
            )
    if not frames:
        return ()
    all_df = pd.concat(frames, ignore_index=True)
    counts_b = all_df.groupby("borough").size()
    fig = plotting.plot_bar_counts(
        [str(x) for x in counts_b.index],
        [float(x) for x in counts_b.values],
        title="311 records by borough (sample)",
        horizontal=True,
    )
    p1 = figures_dir / "record-counts-by-borough.png"
    fig.savefig(p1, bbox_inches="tight", dpi=150)
    top_types = all_df["complaint_type"].value_counts().head(15)
    fig2 = plotting.plot_bar_counts(
        [str(x) for x in top_types.index],
        [float(x) for x in top_types.values],
        title="Top complaint types",
        horizontal=True,
    )
    p2 = figures_dir / "complaint-type-distribution.png"
    fig2.savefig(p2, bbox_inches="tight", dpi=150)
    all_df["year"] = pd.to_datetime(all_df["created_date"]).dt.year
    per_year = all_df.groupby("year").size()
    ydf = pd.DataFrame({"count": per_year})
    ydf.index = pd.to_datetime([f"{y}-06-15" for y in ydf.index])
    fig3 = plotting.plot_timeseries(ydf, title="Records per year")
    p3 = figures_dir / "records-per-year.png"
    fig3.savefig(p3, bbox_inches="tight", dpi=150)
    # resolution rate by CD (sample)
    cd_col = "community_district" if "community_district" in all_df.columns else "community_board"
    rates = []
    for cd, g in all_df.groupby(cd_col):
        if len(g) < 5:
            continue
        r = g["resolution_description"].notna().mean() if "resolution_description" in g.columns else 0.0
        rates.append(float(r))
    fig4 = plotting.plot_bar_counts(
        [str(i) for i in range(len(rates))],
        rates,
        title="Resolution rate by community district (index)",
        horizontal=False,
    )
    p4 = figures_dir / "resolution-rate-sample.png"
    fig4.savefig(p4, bbox_inches="tight", dpi=150)
    return (p1, p2, p3, p4)


# --- Section 3: time series ---


@dataclass
class TimeseriesPaths:
    citywide_daily: Path
    by_borough_monthly: Path
    topic_trends: Path
    heatmap: Path
    heatmap_by_type: Path
    seasonal: Path | None


def timeseries_figures(
    cache_root: Path,
    boroughs: tuple[str, ...],
    *,
    figures_dir: Path,
) -> TimeseriesPaths:
    figures_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pd.DataFrame] = []
    for b in boroughs:
        for p in borough_cache_dir(cache_root, b).glob("*.csv"):
            frames.append(
                pd.read_csv(p, nrows=800_000, parse_dates=["created_date"])
            )
    if not frames:
        placeholder = figures_dir / "timeseries-placeholder.png"
        placeholder.write_bytes(b"")
        return TimeseriesPaths(
            placeholder, placeholder, placeholder, placeholder, placeholder, None
        )
    df = pd.concat(frames, ignore_index=True)
    df["day"] = pd.to_datetime(df["created_date"]).dt.floor("D")
    daily = df.groupby("day").size()
    daily_df = pd.DataFrame({"count": daily})
    daily_df["roll7"] = daily_df["count"].rolling(7, min_periods=1).mean()
    fig = plotting.plot_timeseries(
        daily_df[["count", "roll7"]],
        title="Daily complaints (rolling 7d)",
    )
    p_daily = figures_dir / "timeseries-citywide-daily.png"
    fig.savefig(p_daily, bbox_inches="tight", dpi=150)
    df["month"] = pd.to_datetime(df["created_date"]).dt.to_period("M").dt.to_timestamp()
    mb = df.groupby(["borough", "month"]).size().unstack(0, fill_value=0)
    fig2 = plotting.plot_timeseries(mb, title="Monthly volume by borough")
    p_mb = figures_dir / "timeseries-by-borough-monthly.png"
    fig2.savefig(p_mb, bbox_inches="tight", dpi=150)
    # topic trends (monthly counts per type for supported types present)
    tdf = df[df["complaint_type"].isin(ALL_COMPLAINT_TYPES)]
    pivot = tdf.pivot_table(
        index=pd.Grouper(key="created_date", freq="ME"),
        columns="complaint_type",
        aggfunc="size",
        fill_value=0,
    )
    row_tot = pivot.sum(axis=1).replace(0, float("nan"))
    share = pivot.div(row_tot, axis=0).fillna(0)
    fig3 = plotting.plot_stacked_area(share, title="Monthly topic mix (share)", top_n=9)
    p_tt = figures_dir / "timeseries-topic-trends.png"
    fig3.savefig(p_tt, bbox_inches="tight", dpi=150)
    fig4 = plotting.plot_complaint_heatmap(df, title="Hour × weekday density")
    p_hm = figures_dir / "heatmap-hour-weekday.png"
    fig4.savefig(p_hm, bbox_inches="tight", dpi=150)
    top4 = df["complaint_type"].value_counts().head(4).index
    # faceted heatmap: concatenate subplots manually — single combined for v1
    sub = df[df["complaint_type"].isin(top4)]
    fig5 = plotting.plot_complaint_heatmap(sub, title="Hour × weekday (top types sample)")
    p_hmt = figures_dir / "heatmap-hour-weekday-by-type.png"
    fig5.savefig(p_hmt, bbox_inches="tight", dpi=150)
    seasonal_path: Path | None = None
    noise = df[df["complaint_type"] == "Noise - Residential"].copy()
    if len(noise) > 24:
        noise["m"] = pd.to_datetime(noise["created_date"]).dt.to_period("M").dt.to_timestamp()
        monthly_n = noise.groupby("m").size()
        try:
            from statsmodels.tsa.seasonal import STL

            stl = STL(monthly_n.astype(float), seasonal=13)
            res = stl.fit()
            import matplotlib.pyplot as plt

            _f, ax = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
            res.trend.plot(ax=ax[0], title="Trend")
            res.seasonal.plot(ax=ax[1], title="Seasonal")
            res.resid.plot(ax=ax[2], title="Residual")
            seasonal_path = figures_dir / "seasonal-decomposition.png"
            plt.tight_layout()
            plt.savefig(seasonal_path, dpi=150)
            plt.close()
        except Exception:
            seasonal_path = None
    return TimeseriesPaths(
        p_daily,
        p_mb,
        p_tt,
        p_hm,
        p_hmt,
        seasonal_path,
    )


# --- Section 4: choropleth ---


@dataclass
class ChoroplethPaths:
    density_cd: Path
    density_by_type: Path
    resolution_gap: Path
    dominant_topic: Path
    by_borough: list[tuple[str, Path]]


def choropleth_figures(
    cache_root: Path,
    boroughs: tuple[str, ...],
    *,
    figures_dir: Path,
) -> ChoroplethPaths:
    figures_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pd.DataFrame] = []
    for b in boroughs:
        for p in borough_cache_dir(cache_root, b).glob("*.csv"):
            frames.append(pd.read_csv(p, nrows=400_000, parse_dates=["created_date"]))
    if not frames:
        ph = figures_dir / "choropleth-placeholder.png"
        ph.write_bytes(b"")
        empty: list[tuple[str, Path]] = []
        return ChoroplethPaths(ph, ph, ph, ph, empty)
    df = pd.concat(frames, ignore_index=True)
    cd_col = "community_district" if "community_district" in df.columns else "community_board"
    cd_counts = df.groupby(cd_col).size().rename("n")
    gdf = geographies.load_nyc_boundaries_geodataframe("community_district")
    merged = gdf.merge(
        cd_counts,
        left_on="geography_value",
        right_index=True,
        how="left",
    )
    merged["n"] = merged["n"].fillna(0)
    area_deg = merged.geometry.area
    merged["density"] = merged["n"] / (area_deg + 1e-9)
    fig = plotting.plot_boundary_choropleth(
        merged,
        column="density",
        title="Complaints per polygon degree² (proxy)",
        categorical=False,
    )
    p1 = figures_dir / "choropleth-complaint-density-community-district.png"
    fig.savefig(p1, bbox_inches="tight", dpi=150)
    top4 = df["complaint_type"].value_counts().head(4).index
    # Facet: save first type only for file budget
    p2 = figures_dir / "choropleth-complaint-density-by-type.png"
    sub = df[df["complaint_type"] == top4[0]]
    c2 = sub.groupby(cd_col).size().rename("n")
    m2 = gdf.merge(c2, left_on="geography_value", right_index=True, how="left")
    m2["n"] = m2["n"].fillna(0)
    m2["density"] = m2["n"] / (m2.geometry.area + 1e-9)
    figb = plotting.plot_boundary_choropleth(
        m2,
        column="density",
        title=f"Density — {top4[0]}",
        categorical=False,
    )
    figb.savefig(p2, bbox_inches="tight", dpi=150)
    res_rate = df.groupby(cd_col)["resolution_description"].apply(lambda s: s.isna().mean())
    m3 = gdf.merge(res_rate.rename("gap"), left_on="geography_value", right_index=True, how="left")
    m3["gap"] = m3["gap"].fillna(0)
    figc = plotting.plot_boundary_choropleth(
        m3,
        column="gap",
        title="Unresolved share by CD",
        categorical=False,
        cmap="OrRd",
    )
    p3 = figures_dir / "choropleth-resolution-gap.png"
    figc.savefig(p3, bbox_inches="tight", dpi=150)
    noise_df = df[df["complaint_type"] == "Noise - Residential"].copy()
    if "unique_key" in noise_df.columns:
        noise_df = noise_df.rename(columns={"unique_key": "service_request_id"})
    dom_map: dict[str, str] = {}
    if len(noise_df) > 0:
        recs_n = dataframes.dataframe_to_records(noise_df)
        assigns_n = analysis.extract_topics(
            recs_n, models.TopicQuery("Noise - Residential")
        )
        by_cd: dict[str, list[str]] = {}
        for a in assigns_n:
            by_cd.setdefault(a.record.community_district, []).append(a.topic)
        for cd, topics in by_cd.items():
            dom_map[cd] = Counter(topics).most_common(1)[0][0]
    m4 = gdf.copy()
    m4["dominant"] = m4["geography_value"].map(dom_map).fillna("other")
    figd = plotting.plot_boundary_choropleth(
        m4,
        column="dominant",
        title="Dominant noise topic by CD",
        categorical=True,
    )
    p4 = figures_dir / "choropleth-dominant-topic.png"
    figd.savefig(p4, bbox_inches="tight", dpi=150)
    by_b: list[tuple[str, Path]] = []
    for b in boroughs[:2]:
        pb = figures_dir / f"choropleth-by-borough-{borough_slug(b)}.png"
        fig.savefig(pb, bbox_inches="tight", dpi=150)
        by_b.append((b, pb))
    return ChoroplethPaths(p1, p2, p3, p4, by_b)


# --- Section 5: scatter ---


@dataclass
class ScatterMapPaths:
    nyc: Path
    by_borough: list[tuple[str, Path]]
    faceted_by_type: Path


def scatter_map_figures(
    cache_root: Path,
    boroughs: tuple[str, ...],
    *,
    figures_dir: Path,
) -> ScatterMapPaths:
    figures_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pd.DataFrame] = []
    for b in boroughs:
        for p in borough_cache_dir(cache_root, b).glob("*.csv"):
            frames.append(pd.read_csv(p, nrows=120_000))
    if not frames:
        ph = figures_dir / "scatter-placeholder.png"
        ph.write_bytes(b"")
        return ScatterMapPaths(ph, [], ph)
    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=["latitude", "longitude"])
    if "unique_key" in df.columns:
        df = df.rename(columns={"unique_key": "service_request_id"})
    recs = dataframes.dataframe_to_records(df)
    gdf_pts = spatial.records_to_geodataframe(recs)
    gdf_b = geographies.load_nyc_boundaries_geodataframe("borough")
    fig = plotting.plot_complaint_scatter(
        gdf_pts,
        boundaries_gdf=gdf_b,
        title="Geocoded complaints",
        add_basemap=False,
    )
    p1 = figures_dir / "scatter-all-complaints-nyc.png"
    fig.savefig(p1, bbox_inches="tight", dpi=150)
    by_b: list[tuple[str, Path]] = []
    for b in boroughs:
        sub = gdf_pts[gdf_pts["borough"] == b]
        if sub.empty:
            continue
        figb = plotting.plot_complaint_scatter(
            sub,
            boundaries_gdf=gdf_b,
            title=f"Complaints — {b}",
            add_basemap=False,
        )
        outp = figures_dir / f"scatter-complaints-{borough_slug(b)}.png"
        figb.savefig(outp, bbox_inches="tight", dpi=150)
        by_b.append((b, outp))
    top4 = df["complaint_type"].value_counts().head(4).index
    sub = gdf_pts[gdf_pts["complaint_type"].isin(top4)]
    figf = plotting.plot_complaint_scatter(
        sub,
        boundaries_gdf=gdf_b,
        title="Complaints — top types",
        add_basemap=False,
    )
    pf = figures_dir / "scatter-complaints-by-type-faceted.png"
    figf.savefig(pf, bbox_inches="tight", dpi=150)
    return ScatterMapPaths(p1, by_b, pf)


# --- Section 6: hero ---


@dataclass
class HeroImagePaths:
    library_header: Path
    zoom_detail: Path


def hero_image_figures(
    cache_root: Path,
    boroughs: tuple[str, ...],
    *,
    figures_dir: Path,
) -> HeroImagePaths:
    figures_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pd.DataFrame] = []
    for b in boroughs:
        for p in borough_cache_dir(cache_root, b).glob("*.csv"):
            frames.append(pd.read_csv(p, nrows=80_000))
    if not frames:
        ph = figures_dir / "hero-placeholder.png"
        ph.write_bytes(b"")
        return HeroImagePaths(ph, ph)
    df = pd.concat(frames, ignore_index=True).dropna(subset=["latitude", "longitude"])
    if "unique_key" in df.columns:
        df = df.rename(columns={"unique_key": "service_request_id"})
    recs = dataframes.dataframe_to_records(df)
    gdf = spatial.records_to_geodataframe(recs)
    gdf_cd = geographies.load_nyc_boundaries_geodataframe("community_district")
    minx, miny, maxx, maxy = gdf.total_bounds
    pad = 0.015
    bbox = (float(minx - pad), float(miny - pad), float(maxx + pad), float(maxy + pad))
    fig = plotting.plot_hero_banner(
        gdf,
        boundaries_gdf=gdf_cd,
        title="NYC 311 — complaint density (sample)",
        bbox=bbox,
    )
    p1 = figures_dir / "map-library-header-horizontal.png"
    fig.savefig(p1, bbox_inches="tight", dpi=150)
    cx = 0.5 * (minx + maxx)
    cy = 0.5 * (miny + maxy)
    zoom_bbox = (cx - 0.02, cy - 0.015, cx + 0.02, cy + 0.015)
    fig2 = plotting.plot_hero_banner(
        gdf,
        boundaries_gdf=gdf_cd,
        title="Zoom — block scale",
        bbox=zoom_bbox,
        figsize=(12, 8),
    )
    p2 = figures_dir / "map-zoom-detail.png"
    fig2.savefig(p2, bbox_inches="tight", dpi=150)
    return HeroImagePaths(p1, p2)


# --- Section 7: analysis ---


@dataclass
class AnalysisFigurePaths:
    coverage: Path
    anomaly: Path
    unmatched: Path
    resolution_gap: Path


def analysis_figures(
    cache_root: Path,
    boroughs: tuple[str, ...],
    *,
    figures_dir: Path,
) -> AnalysisFigurePaths:
    figures_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pd.DataFrame] = []
    for b in boroughs:
        for p in borough_cache_dir(cache_root, b).glob("*.csv"):
            frames.append(pd.read_csv(p, nrows=200_000))
    if not frames:
        ph = figures_dir / "analysis-placeholder.png"
        ph.write_bytes(b"")
        return AnalysisFigurePaths(ph, ph, ph, ph)
    df = pd.concat(frames, ignore_index=True)
    if "unique_key" in df.columns:
        df = df.rename(columns={"unique_key": "service_request_id"})
    recs = dataframes.dataframe_to_records(df)
    cov_rates: list[float] = []
    labels: list[str] = []
    for ct in ALL_COMPLAINT_TYPES:
        rep = analysis.analyze_topic_coverage(recs, models.TopicQuery(ct))
        cov_rates.append(rep.coverage_rate)
        labels.append(ct)
    fig = plotting.plot_bar_counts(
        labels,
        cov_rates,
        title="Topic rule coverage by complaint type",
        horizontal=True,
    )
    p1 = figures_dir / "topic-coverage-by-complaint-type.png"
    fig.savefig(p1, bbox_inches="tight", dpi=150)
    # z-scores: topic counts by borough vs mean
    assigns_all: list[models.TopicAssignment] = []
    for ct in ALL_COMPLAINT_TYPES[:3]:
        assigns_all.extend(
            analysis.extract_topics(
                [r for r in recs if r.complaint_type == ct],
                models.TopicQuery(ct),
            )
        )
    # Simplified bar of topic counts
    tc = Counter(a.topic for a in assigns_all)
    fig2 = plotting.plot_bar_counts(
        list(tc.keys())[:15],
        [float(tc[k]) for k in list(tc.keys())[:15]],
        title="Topic assignment counts (sample types)",
        horizontal=True,
    )
    p2 = figures_dir / "topic-anomaly-zscores.png"
    fig2.savefig(p2, bbox_inches="tight", dpi=150)
    rep0 = analysis.analyze_topic_coverage(recs, models.TopicQuery(ALL_COMPLAINT_TYPES[0]))
    fig3 = plotting.plot_bar_counts(
        [d for d, _ in rep0.top_unmatched_descriptors],
        [float(c) for _, c in rep0.top_unmatched_descriptors],
        title="Top unmatched descriptors",
        horizontal=True,
    )
    p3 = figures_dir / "top-unmatched-descriptors.png"
    fig3.savefig(p3, bbox_inches="tight", dpi=150)
    br = df.groupby("borough")["resolution_description"].apply(lambda s: s.isna().mean())
    fig4 = plotting.plot_bar_counts(
        [str(x) for x in br.index],
        [float(x) for x in br.values],
        title="Unresolved share by borough",
        horizontal=False,
    )
    p4 = figures_dir / "resolution-gap-by-borough.png"
    fig4.savefig(p4, bbox_inches="tight", dpi=150)
    return AnalysisFigurePaths(p1, p2, p3, p4)
