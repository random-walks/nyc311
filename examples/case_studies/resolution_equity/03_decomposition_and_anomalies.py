#!/usr/bin/env python3
"""Step 3: STL seasonal decomposition and anomaly detection.

Decomposes monthly complaint totals into trend, seasonal, and residual
components (Cleveland et al., 1990), then flags anomalous observations
whose residuals exceed a z-score threshold.  Decomposition is run
city-wide and per-borough.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared.diagnostics import interpret_stl_anomalies

import pandas as pd

from nyc311.stats import detect_stl_anomalies, seasonal_decompose


def main() -> None:
    panel_path = Path(__file__).parent / "data" / "panel.parquet"
    if not panel_path.exists():
        print("Panel not found. Run 02_build_panel.py first.")
        return

    df = pd.read_parquet(panel_path)

    # ── City-wide decomposition ──────────────────────────────────────
    city_monthly = df.groupby("period")["complaint_count"].sum()
    city_monthly.index = pd.to_datetime(city_monthly.index)
    city_monthly = city_monthly.sort_index()

    print("=" * 72)
    print("City-Wide STL Decomposition (period=12)")
    print("=" * 72)

    result = seasonal_decompose(city_monthly, period=12)

    print(f"  Trend range: {result.trend.min():.0f} -- {result.trend.max():.0f}")
    print(f"  Seasonal amplitude: {result.seasonal.max() - result.seasonal.min():.0f}")
    print(f"  Residual std: {result.residual.std():.1f}")

    # ── City-wide anomaly detection ──────────────────────────────────
    print("\n" + "-" * 72)
    print("STL Anomaly Detection (city-wide)")
    print("-" * 72)

    anomaly_result = detect_stl_anomalies(city_monthly, period=12, threshold=2.0)
    print(interpret_stl_anomalies(anomaly_result))

    # ── Per-borough decomposition ────────────────────────────────────
    print("\n" + "=" * 72)
    print("Per-Borough STL Decomposition")
    print("=" * 72)

    # Parse borough from unit_id: everything before the last space
    # e.g. "MANHATTAN 01" -> "MANHATTAN", "BRONX 03" -> "BRONX"
    df_flat = df.reset_index() if "unit_id" in df.index.names else df.copy()
    df_flat["borough"] = df_flat["unit_id"].apply(
        lambda uid: " ".join(uid.split()[:-1]) if " " in uid else uid
    )

    borough_monthly = (
        df_flat.groupby(["borough", "period"])["complaint_count"].sum().reset_index()
    )

    for borough in sorted(borough_monthly["borough"].unique()):
        bdf = borough_monthly[borough_monthly["borough"] == borough].copy()
        bdf.index = pd.to_datetime(bdf["period"])
        bdf = bdf.sort_index()
        series = bdf["complaint_count"]

        if len(series) < 24:
            print(f"\n  {borough}: insufficient data ({len(series)} obs), skipping")
            continue

        try:
            b_result = seasonal_decompose(series, period=12)
        except Exception as exc:
            print(f"\n  {borough}: decomposition failed ({exc})")
            continue

        seasonal = b_result.seasonal
        peak_month = seasonal.idxmax()
        trough_month = seasonal.idxmin()

        print(f"\n  {borough}:")
        print(
            f"    Trend range: {b_result.trend.min():.0f} -- {b_result.trend.max():.0f}"
        )
        print(f"    Seasonal amplitude: {seasonal.max() - seasonal.min():.0f}")
        print(
            f"    Peak month:   {peak_month.strftime('%Y-%m') if hasattr(peak_month, 'strftime') else peak_month}"
        )
        print(
            f"    Trough month: {trough_month.strftime('%Y-%m') if hasattr(trough_month, 'strftime') else trough_month}"
        )

    # ── Figure: city-wide decomposition ──────────────────────────────
    figures_dir = Path(__file__).parent / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
        city_monthly.plot(ax=axes[0], title="Observed")
        result.trend.plot(ax=axes[1], title="Trend")
        result.seasonal.plot(ax=axes[2], title="Seasonal")
        result.residual.plot(ax=axes[3], title="Residual")
        fig.tight_layout()
        fig.savefig(figures_dir / "stl_decomposition.png", dpi=150)
        print(f"\n  Figure saved: {figures_dir / 'stl_decomposition.png'}")
        plt.close(fig)
    except ImportError:
        print("  (matplotlib not available; skipping figure)")


if __name__ == "__main__":
    main()
