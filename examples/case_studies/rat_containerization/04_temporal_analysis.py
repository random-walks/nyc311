#!/usr/bin/env python3
"""Step 4: Temporal decomposition, anomaly detection, and changepoints.

Runs STL decomposition on the city-wide rodent complaint series,
detects anomalous months via residual z-scores, and identifies
structural breaks using PELT changepoint detection.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared.diagnostics import interpret_changepoints, interpret_stl_anomalies

DATA_DIR = Path(__file__).parent / "data"


def run() -> dict:
    """Run temporal analysis on the rodent complaint panel."""
    from nyc311.stats import (
        detect_changepoints,
        detect_stl_anomalies,
        seasonal_decompose,
    )

    df = pd.read_parquet(DATA_DIR / "panel.parquet")

    # ── City-wide monthly series ─────────────────────────────────────
    city_monthly = df.groupby("period")["complaint_count"].sum()
    city_monthly.index = pd.to_datetime(city_monthly.index)
    city_monthly = city_monthly.sort_index()

    print(f"  City-wide monthly rodent complaints: {len(city_monthly)} periods")
    print(f"  Range: {city_monthly.min():,} -- {city_monthly.max():,}")
    print(f"  Mean: {city_monthly.mean():,.0f}, Std: {city_monthly.std():,.0f}")

    results: dict = {}

    # ── STL Decomposition ────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("STL Seasonal Decomposition (period=12)")
    print("=" * 72)

    decomp = seasonal_decompose(city_monthly, period=12)
    trend = decomp.trend.dropna()
    seasonal = decomp.seasonal.dropna()

    monthly_seasonal = seasonal.groupby(seasonal.index.month).mean()
    month_names = {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }
    peak_month = month_names[int(monthly_seasonal.idxmax())]
    trough_month = month_names[int(monthly_seasonal.idxmin())]

    print(f"  Trend: {trend.iloc[0]:,.0f} -> {trend.iloc[-1]:,.0f}")
    print(f"  Seasonal amplitude: {seasonal.max() - seasonal.min():,.0f}")
    print(f"  Peak month: {peak_month}, Trough month: {trough_month}")

    results["stl"] = {
        "trend_start": float(trend.iloc[0]),
        "trend_end": float(trend.iloc[-1]),
        "seasonal_amplitude": float(seasonal.max() - seasonal.min()),
        "peak_month": peak_month,
        "trough_month": trough_month,
    }

    # ── STL Anomaly Detection ────────────────────────────────────────
    print("\n" + "=" * 72)
    print("STL Anomaly Detection")
    print("=" * 72)

    anomalies = detect_stl_anomalies(city_monthly, threshold=2.0)
    print(interpret_stl_anomalies(anomalies))

    results["anomalies"] = {
        "n_anomalies": anomalies.n_anomalies,
        "dates": [str(d)[:10] for d in anomalies.anomaly_dates],
        "scores": list(anomalies.anomaly_scores),
    }

    # ── Changepoint Detection ────────────────────────────────────────
    print("\n" + "=" * 72)
    print("PELT Changepoint Detection")
    print("=" * 72)

    known_events = {
        "Rat containerization pilot (Manhattan)": date(2024, 6, 1),
        "Citywide containerization mandate": date(2024, 11, 12),
    }

    cp_result = detect_changepoints(city_monthly, method="pelt")
    print(interpret_changepoints(cp_result, known_events))

    results["changepoints"] = {
        "n_segments": cp_result.n_segments,
        "n_breakpoints": len(cp_result.breakpoints),
        "breakpoint_dates": [d.isoformat() for d in cp_result.breakpoint_dates],
    }

    # ── Per-borough trends ───────────────────────────────────────────
    print("\n" + "=" * 72)
    print("Per-Borough Monthly Trends")
    print("=" * 72)

    df_flat = df.reset_index() if isinstance(df.index, pd.MultiIndex) else df
    df_flat["borough"] = df_flat["unit_id"].str.rsplit(" ", n=1).str[0]
    borough_monthly = df_flat.groupby(["borough", "period"])["complaint_count"].sum()

    for borough in sorted(borough_monthly.index.get_level_values(0).unique()):
        series = borough_monthly.loc[borough]
        pre = series.iloc[: len(series) // 2].mean()
        post = series.iloc[len(series) // 2 :].mean()
        change = ((post - pre) / pre * 100) if pre > 0 else 0
        print(
            f"  {borough:>20s}: mean={series.mean():6.0f}  "
            f"1st half={pre:6.0f}  2nd half={post:6.0f}  "
            f"change={change:+.1f}%"
        )

    return results


if __name__ == "__main__":
    print("Step 4: Temporal Analysis\n")
    run()
