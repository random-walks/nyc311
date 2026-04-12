#!/usr/bin/env python3
"""End-to-end analysis runner for the resolution equity case study.

Fetches real NYC 311 data from Socrata, builds panels, runs all statistical
analyses, and prints structured results that feed into the findings README.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 1. Fetch real data from Socrata
# ---------------------------------------------------------------------------

def fetch_data(cache_dir: Path) -> list:
    """Fetch 311 data per-borough, 2020-01 through 2024-12."""
    from nyc311.io._cache import cached_fetch
    from nyc311.models import GeographyFilter, ServiceRequestFilter, SocrataConfig
    from nyc311.models._constants import SUPPORTED_BOROUGHS

    config = SocrataConfig(
        page_size=5_000,
        max_pages=40,  # up to 200k rows per borough = ~1M total
        request_timeout_seconds=120.0,
        created_date_sort="desc",  # recent first for best coverage
    )

    filters_base = ServiceRequestFilter(
        start_date=date(2020, 1, 1),
        end_date=date(2024, 12, 31),
    )

    all_paths = []
    for borough in SUPPORTED_BOROUGHS:
        filters = ServiceRequestFilter(
            start_date=filters_base.start_date,
            end_date=filters_base.end_date,
            geography=GeographyFilter(geography="borough", value=borough),
        )
        print(f"  Fetching {borough} ...", end=" ", flush=True)
        path = cached_fetch(config, filters, cache_dir=cache_dir)
        size_mb = path.stat().st_size / 1_048_576
        print(f"{size_mb:.1f} MB")
        all_paths.append(path)

    return all_paths


def load_all_records(csv_paths: list[Path]) -> list:
    """Load records from cached CSVs."""
    from nyc311.io import load_service_requests_from_csv
    from nyc311.models import ServiceRequestFilter

    all_records = []
    for p in csv_paths:
        records = load_service_requests_from_csv(
            p, filters=ServiceRequestFilter()
        )
        all_records.extend(records)
    return all_records


# ---------------------------------------------------------------------------
# 2. Build panel
# ---------------------------------------------------------------------------

def build_panel(records: list) -> dict:
    """Build community-district x month panel and return summary stats."""
    from nyc311.temporal import build_complaint_panel

    panel = build_complaint_panel(
        records,
        geography="community_district",
        freq="ME",
    )

    df = panel.to_dataframe()

    # Summary stats
    stats = {
        "n_records": len(records),
        "n_units": len(panel.unit_ids),
        "n_periods": len(panel.periods),
        "n_observations": len(panel.observations),
        "period_range": f"{panel.periods[0]} to {panel.periods[-1]}" if panel.periods else "N/A",
        "mean_complaints_per_cell": float(df["complaint_count"].mean()),
        "median_complaints_per_cell": float(df["complaint_count"].median()),
        "mean_resolution_rate": float(df["resolution_rate"].mean()),
        "std_resolution_rate": float(df["resolution_rate"].std()),
    }

    return {"panel": panel, "df": df, "stats": stats}


# ---------------------------------------------------------------------------
# 3. Time series construction
# ---------------------------------------------------------------------------

def build_city_timeseries(df: pd.DataFrame) -> pd.Series:
    """Aggregate panel to city-wide monthly complaint totals."""
    city = df.groupby("period")["complaint_count"].sum()
    city.index = pd.to_datetime(city.index)
    return city.sort_index()


# ---------------------------------------------------------------------------
# 4. STL Seasonal Decomposition
# ---------------------------------------------------------------------------

def run_stl(city_series: pd.Series) -> dict:
    """Run STL decomposition and return key metrics."""
    from nyc311.stats import seasonal_decompose

    result = seasonal_decompose(city_series, period=12)
    trend = result.trend.dropna()
    seasonal = result.seasonal.dropna()
    resid = result.residual.dropna()

    # Find peak and trough months for seasonality
    monthly_seasonal = seasonal.groupby(seasonal.index.month).mean()
    peak_month = int(monthly_seasonal.idxmax())
    trough_month = int(monthly_seasonal.idxmin())

    month_names = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December",
    }

    return {
        "trend_start": float(trend.iloc[0]),
        "trend_end": float(trend.iloc[-1]),
        "trend_pct_change": float((trend.iloc[-1] - trend.iloc[0]) / trend.iloc[0] * 100),
        "seasonal_amplitude": float(seasonal.max() - seasonal.min()),
        "seasonal_peak_month": month_names[peak_month],
        "seasonal_trough_month": month_names[trough_month],
        "seasonal_peak_value": float(monthly_seasonal.max()),
        "seasonal_trough_value": float(monthly_seasonal.min()),
        "residual_std": float(resid.std()),
        "residual_mean": float(resid.mean()),
    }


# ---------------------------------------------------------------------------
# 5. Changepoint Detection
# ---------------------------------------------------------------------------

def run_changepoints(city_series: pd.Series) -> dict:
    """Run PELT changepoint detection."""
    from nyc311.stats import detect_changepoints

    result = detect_changepoints(city_series, method="pelt")

    known_events = {
        "COVID-19 lockdown (NYC PAUSE)": date(2020, 3, 22),
        "Phase 1 reopening": date(2020, 6, 8),
        "Phase 4 reopening": date(2020, 7, 20),
        "Omicron wave peak": date(2022, 1, 15),
        "Rat containerization mandate": date(2024, 3, 1),
    }

    breakpoints_annotated = []
    for bp_date in result.breakpoint_dates:
        nearest = None
        min_delta = 120
        for name, ev_date in known_events.items():
            delta = abs((bp_date - ev_date).days)
            if delta < min_delta:
                min_delta = delta
                nearest = name
        breakpoints_annotated.append({
            "date": bp_date.isoformat(),
            "nearest_event": nearest,
            "days_from_event": min_delta if nearest else None,
        })

    return {
        "n_segments": result.n_segments,
        "n_breakpoints": len(result.breakpoints),
        "penalty": float(result.penalty),
        "breakpoints": breakpoints_annotated,
    }


# ---------------------------------------------------------------------------
# 6. Factor Pipeline
# ---------------------------------------------------------------------------

def run_factor_pipeline(panel, records: list) -> dict:
    """Run the factor pipeline over panel contexts."""
    from nyc311.factors import (
        ComplaintVolumeFactor,
        Pipeline,
        FactorContext,
        ResponseRateFactor,
        TopicConcentrationFactor,
        RecurrenceFactor,
    )

    # Build contexts from panel observations
    # Group records by (community_district, period)
    from collections import defaultdict
    grouped = defaultdict(list)
    for rec in records:
        period = pd.Timestamp(rec.created_date).to_period("M")
        key = (rec.community_district, str(period))
        grouped[key].append(rec)

    contexts = []
    for obs in panel.observations:
        recs = grouped.get((obs.unit_id, obs.period), [])
        ctx = FactorContext(
            geography="community_district",
            geography_value=obs.unit_id,
            complaints=tuple(recs),
            time_window_start=date(2020, 1, 1),
            time_window_end=date(2024, 12, 31),
            total_population=None,
        )
        contexts.append(ctx)

    pipeline = (
        Pipeline()
        .add(ComplaintVolumeFactor())
        .add(ResponseRateFactor())
        .add(TopicConcentrationFactor())
        .add(RecurrenceFactor())
    )

    result = pipeline.run(contexts)
    df = result.to_dataframe()

    return {
        "n_contexts": len(contexts),
        "factors_computed": list(result.columns.keys()),
        "mean_volume": float(df["complaint_volume"].mean()),
        "mean_response_rate": float(df["response_rate"].mean()),
        "mean_topic_concentration": float(df["topic_concentration"].mean()),
        "mean_recurrence_rate": float(df["recurrence_rate"].mean()),
        "top_5_by_volume": df.nlargest(5, "complaint_volume")["complaint_volume"].to_dict(),
        "bottom_5_response_rate": df.nsmallest(5, "response_rate")["response_rate"].to_dict(),
    }


# ---------------------------------------------------------------------------
# 7. Geographic variation analysis
# ---------------------------------------------------------------------------

def analyze_geographic_variation(df: pd.DataFrame) -> dict:
    """Analyze cross-district variation in complaints and resolution."""
    unit_stats = df.groupby("unit_id").agg({
        "complaint_count": ["mean", "std", "sum"],
        "resolution_rate": ["mean", "std"],
    })
    unit_stats.columns = ["_".join(c) for c in unit_stats.columns]

    top_volume = unit_stats.nlargest(10, "complaint_count_mean")
    bottom_volume = unit_stats.nsmallest(10, "complaint_count_mean")

    top_resolution = unit_stats.nlargest(10, "resolution_rate_mean")
    bottom_resolution = unit_stats.nsmallest(10, "resolution_rate_mean")

    # Borough-level aggregation
    borough_map = {}
    for uid in unit_stats.index:
        parts = uid.rsplit(" ", 1)
        borough_map[uid] = parts[0] if len(parts) > 1 else uid

    unit_stats["borough"] = [borough_map.get(uid, uid) for uid in unit_stats.index]
    borough_stats = unit_stats.groupby("borough").agg({
        "complaint_count_mean": "mean",
        "resolution_rate_mean": "mean",
    })

    return {
        "top_10_volume_districts": {
            k: round(v, 1) for k, v in
            top_volume["complaint_count_mean"].head(10).to_dict().items()
        },
        "bottom_10_volume_districts": {
            k: round(v, 1) for k, v in
            bottom_volume["complaint_count_mean"].head(10).to_dict().items()
        },
        "top_10_resolution_districts": {
            k: round(v, 4) for k, v in
            top_resolution["resolution_rate_mean"].head(10).to_dict().items()
        },
        "bottom_10_resolution_districts": {
            k: round(v, 4) for k, v in
            bottom_resolution["resolution_rate_mean"].head(10).to_dict().items()
        },
        "borough_mean_complaints": {
            k: round(v, 1) for k, v in
            borough_stats["complaint_count_mean"].to_dict().items()
        },
        "borough_mean_resolution": {
            k: round(v, 4) for k, v in
            borough_stats["resolution_rate_mean"].to_dict().items()
        },
        "overall_cv_complaints": float(
            unit_stats["complaint_count_mean"].std() /
            unit_stats["complaint_count_mean"].mean()
        ),
        "overall_cv_resolution": float(
            unit_stats["resolution_rate_mean"].std() /
            unit_stats["resolution_rate_mean"].mean()
        ),
    }


# ---------------------------------------------------------------------------
# 8. Complaint type analysis
# ---------------------------------------------------------------------------

def analyze_complaint_types(records: list) -> dict:
    """Analyze distribution and trends by complaint type."""
    from collections import Counter

    type_counts = Counter(r.complaint_type for r in records)
    total = len(records)

    top_20 = type_counts.most_common(20)

    # Resolution rate by type
    type_resolved = Counter()
    type_total = Counter()
    for r in records:
        type_total[r.complaint_type] += 1
        if r.resolution_description is not None:
            type_resolved[r.complaint_type] += 1

    type_resolution = {}
    for ct, cnt in top_20:
        res_count = type_resolved.get(ct, 0)
        type_resolution[ct] = round(res_count / cnt, 4) if cnt > 0 else 0.0

    return {
        "total_complaint_types": len(type_counts),
        "top_20_types": dict(top_20),
        "top_20_shares": {ct: round(cnt / total * 100, 2) for ct, cnt in top_20},
        "top_20_resolution_rates": type_resolution,
        "concentration_top5": round(
            sum(cnt for _, cnt in top_20[:5]) / total * 100, 2
        ),
        "concentration_top10": round(
            sum(cnt for _, cnt in top_20[:10]) / total * 100, 2
        ),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    output_dir = Path(__file__).parent / "data"
    cache_dir = output_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    # 1. Fetch data
    print("=" * 72)
    print("STEP 1: Fetching NYC 311 data (2020-2024)")
    print("=" * 72)
    csv_paths = fetch_data(cache_dir)

    print("\nLoading records into memory ...")
    records = load_all_records(csv_paths)
    print(f"  Total records loaded: {len(records):,}")

    # Date range
    dates = [r.created_date for r in records]
    print(f"  Date range: {min(dates)} to {max(dates)}")

    # 2. Build panel
    print("\n" + "=" * 72)
    print("STEP 2: Building balanced panel")
    print("=" * 72)
    panel_data = build_panel(records)
    panel = panel_data["panel"]
    df = panel_data["df"]
    results["panel"] = panel_data["stats"]
    for k, v in panel_data["stats"].items():
        print(f"  {k}: {v}")

    # 3. City time series
    print("\n" + "=" * 72)
    print("STEP 3: STL Seasonal Decomposition")
    print("=" * 72)
    city_series = build_city_timeseries(df)
    stl_results = run_stl(city_series)
    results["stl"] = stl_results
    for k, v in stl_results.items():
        print(f"  {k}: {v}")

    # 4. Changepoint detection
    print("\n" + "=" * 72)
    print("STEP 4: Changepoint Detection (PELT)")
    print("=" * 72)
    cp_results = run_changepoints(city_series)
    results["changepoints"] = cp_results
    print(f"  Segments: {cp_results['n_segments']}")
    print(f"  Penalty: {cp_results['penalty']:.2f}")
    for bp in cp_results["breakpoints"]:
        label = f" <- {bp['nearest_event']} ({bp['days_from_event']}d)" if bp["nearest_event"] else ""
        print(f"  Break: {bp['date']}{label}")

    # 5. Factor pipeline
    print("\n" + "=" * 72)
    print("STEP 5: Factor Pipeline")
    print("=" * 72)
    factor_results = run_factor_pipeline(panel, records)
    results["factors"] = factor_results
    print(f"  Contexts: {factor_results['n_contexts']}")
    print(f"  Mean volume: {factor_results['mean_volume']:.1f}")
    print(f"  Mean response rate: {factor_results['mean_response_rate']:.4f}")
    print(f"  Mean topic concentration (HHI): {factor_results['mean_topic_concentration']:.4f}")
    print(f"  Mean recurrence rate: {factor_results['mean_recurrence_rate']:.4f}")

    # 6. Geographic variation
    print("\n" + "=" * 72)
    print("STEP 6: Geographic Variation Analysis")
    print("=" * 72)
    geo_results = analyze_geographic_variation(df)
    results["geographic"] = geo_results
    print(f"  CV (complaints): {geo_results['overall_cv_complaints']:.3f}")
    print(f"  CV (resolution): {geo_results['overall_cv_resolution']:.3f}")
    print("  Borough mean monthly complaints:")
    for boro, val in sorted(geo_results["borough_mean_complaints"].items()):
        res = geo_results["borough_mean_resolution"].get(boro, 0)
        print(f"    {boro}: {val:.0f} complaints, {res:.1%} resolution rate")

    # 7. Complaint type analysis
    print("\n" + "=" * 72)
    print("STEP 7: Complaint Type Analysis")
    print("=" * 72)
    type_results = analyze_complaint_types(records)
    results["complaint_types"] = type_results
    print(f"  Unique complaint types: {type_results['total_complaint_types']}")
    print(f"  Top 5 concentration: {type_results['concentration_top5']}%")
    print(f"  Top 10 concentration: {type_results['concentration_top10']}%")
    print("  Top 10 types:")
    for ct, cnt in list(type_results["top_20_types"].items())[:10]:
        share = type_results["top_20_shares"][ct]
        res = type_results["top_20_resolution_rates"][ct]
        print(f"    {ct}: {cnt:,} ({share}%, res={res:.1%})")

    # Save results
    results_path = output_dir / "analysis_results.json"

    # Make JSON-serializable
    def make_serializable(obj):
        if isinstance(obj, dict):
            return {str(k): make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [make_serializable(i) for i in obj]
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    results_path.write_text(
        json.dumps(make_serializable(results), indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\n\nFull results saved to: {results_path}")


if __name__ == "__main__":
    main()
