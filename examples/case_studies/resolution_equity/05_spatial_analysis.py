#!/usr/bin/env python3
"""Step 5: Spatial autocorrelation analysis of resolution times.

Computes Global Moran's I and LISA cluster labels for mean resolution
time across community districts (Rey & Anselin, 2007), then derives
spatial lag factors summarizing each unit's neighborhood context.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared.diagnostics import interpret_moran

import pandas as pd

from nyc311.temporal import build_distance_weights


def main() -> None:
    panel_path = Path(__file__).parent / "data" / "panel.parquet"
    if not panel_path.exists():
        print("Panel not found. Run 02_build_panel.py first.")
        return

    df = pd.read_parquet(panel_path)

    # Compute mean resolution time per district across all periods
    mean_res = df.groupby("unit_id")["median_resolution_days"].mean().dropna().to_dict()

    if not mean_res:
        print("No resolution data available; skipping spatial analysis.")
        return

    # ── Build spatial weights from real community district boundaries ──
    from nyc311.geographies import load_nyc_boundaries
    from nyc311.temporal import centroids_from_boundaries

    boundaries = load_nyc_boundaries("community_district")
    centroids = centroids_from_boundaries(boundaries)
    print(
        f"  Loaded {len(centroids)} community district centroids from nyc_geo_toolkit"
    )

    # Only keep units present in both centroids and mean_res
    shared = sorted(set(mean_res) & set(centroids))
    mean_res = {k: mean_res[k] for k in shared}
    centroids = {k: centroids[k] for k in shared}

    weights = build_distance_weights(centroids, threshold_meters=3000.0)

    # ── Global Moran's I ─────────────────────────────────────────────
    print("=" * 72)
    print("Global Moran's I: Spatial Autocorrelation of Resolution Times")
    print("=" * 72)

    try:
        from nyc311.stats import global_morans_i, local_morans_i
    except ImportError:
        print("esda/libpysal not installed. Run: pip install nyc311[stats]")
        return

    moran = global_morans_i(mean_res, weights)
    print(interpret_moran(moran))

    # ── LISA ──────────────────────────────────────────────────────────
    print("\n" + "-" * 72)
    print("LISA Cluster Distribution")
    print("-" * 72)

    lisa = local_morans_i(mean_res, weights)
    cluster_counts: dict[str, int] = {}
    for label in lisa.cluster_labels:
        cluster_counts[label] = cluster_counts.get(label, 0) + 1

    for label, count in sorted(cluster_counts.items()):
        print(f"  {label}: {count} districts")

    # Export LISA results
    figures_dir = Path(__file__).parent / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    lisa_df = pd.DataFrame(
        {
            "unit_id": lisa.unit_ids,
            "local_I": lisa.local_statistic,
            "p_value": lisa.p_values,
            "cluster": lisa.cluster_labels,
        }
    )
    lisa_path = figures_dir / "lisa_clusters.csv"
    lisa_df.to_csv(lisa_path, index=False)
    print(f"\n  LISA results saved: {lisa_path}")

    # ── Spatial Lag Factor ───────────────────────────────────────────
    print("\n" + "=" * 72)
    print("Spatial Lag Factor (weighted neighborhood average)")
    print("=" * 72)

    spatial_lag: dict[str, float] = {}
    for uid in shared:
        neighbors = weights.get(uid, {})
        if not neighbors:
            spatial_lag[uid] = float("nan")
            continue
        total_weight = sum(neighbors.values())
        if total_weight == 0:
            spatial_lag[uid] = float("nan")
            continue
        weighted_sum = sum(w * mean_res.get(nid, 0.0) for nid, w in neighbors.items())
        spatial_lag[uid] = weighted_sum / total_weight

    # Report top/bottom districts by spatial lag factor
    valid_lags = {k: v for k, v in spatial_lag.items() if not math.isnan(v)}
    if valid_lags:
        sorted_lags = sorted(valid_lags.items(), key=lambda x: x[1], reverse=True)
        print("\n  Top 5 districts by neighborhood average resolution time:")
        for uid, lag in sorted_lags[:5]:
            own = mean_res[uid]
            print(f"    {uid}: own = {own:.2f}d, neighbors = {lag:.2f}d")

        print("\n  Bottom 5 districts:")
        for uid, lag in sorted_lags[-5:]:
            own = mean_res[uid]
            print(f"    {uid}: own = {own:.2f}d, neighbors = {lag:.2f}d")

        lag_df = pd.DataFrame(
            [
                {"unit_id": uid, "mean_resolution": mean_res[uid], "spatial_lag": lag}
                for uid, lag in sorted_lags
            ]
        )
        lag_path = figures_dir / "spatial_lag_factors.csv"
        lag_df.to_csv(lag_path, index=False)
        print(f"\n  Spatial lag factors saved: {lag_path}")
    else:
        print(
            "  No valid spatial lag factors computed (no neighbors within threshold)."
        )


if __name__ == "__main__":
    main()
