#!/usr/bin/env python3
"""Step 5: Spatial autocorrelation analysis of resolution times.

Computes Global Moran's I and LISA cluster labels for mean resolution
time across community districts (Rey & Anselin, 2007).
"""

from pathlib import Path

import pandas as pd

from nyc311.temporal import build_distance_weights


def main() -> None:
    panel_path = Path(__file__).parent / "data" / "panel.parquet"
    if not panel_path.exists():
        print("Panel not found. Run 02_build_panel.py first.")
        return

    df = pd.read_parquet(panel_path)

    # Compute mean resolution time per district across all periods
    mean_res = (
        df.groupby("unit_id")["median_resolution_days"]
        .mean()
        .dropna()
        .to_dict()
    )

    if not mean_res:
        print("No resolution data available; skipping spatial analysis.")
        return

    # --- Build spatial weights from community district boundaries -----------
    try:
        from nyc311.geographies import load_nyc_boundaries
        from nyc311.temporal import centroids_from_boundaries

        boundaries = load_nyc_boundaries("community_district")
        centroids = centroids_from_boundaries(boundaries)
    except Exception as exc:
        print(f"Could not load boundaries: {exc}")
        print("Using synthetic centroids for demonstration.")
        import numpy as np

        rng = np.random.default_rng(42)
        centroids = {
            uid: (40.7 + rng.uniform(-0.1, 0.1), -74.0 + rng.uniform(-0.1, 0.1))
            for uid in mean_res
        }

    # Only keep units present in both centroids and mean_res
    shared = sorted(set(mean_res) & set(centroids))
    mean_res = {k: mean_res[k] for k in shared}
    centroids = {k: centroids[k] for k in shared}

    weights = build_distance_weights(centroids, threshold_meters=3000.0)

    # --- Global Moran's I ---------------------------------------------------
    try:
        from nyc311.stats import global_morans_i, local_morans_i
    except ImportError:
        print("esda/libpysal not installed. Run: pip install nyc311[stats]")
        return

    moran = global_morans_i(mean_res, weights)
    print("Global Moran's I")
    print(f"  I = {moran.statistic:.4f}")
    print(f"  E[I] = {moran.expected:.4f}")
    print(f"  z = {moran.z_score:.4f}")
    print(f"  p = {moran.p_value:.4f}")
    if moran.p_value < 0.05:
        print("  -> Significant spatial autocorrelation detected.")
    else:
        print("  -> No significant spatial autocorrelation at alpha=0.05.")

    # --- LISA ---------------------------------------------------------------
    lisa = local_morans_i(mean_res, weights)
    cluster_counts = {}
    for label in lisa.cluster_labels:
        cluster_counts[label] = cluster_counts.get(label, 0) + 1

    print("\nLISA Cluster Distribution")
    for label, count in sorted(cluster_counts.items()):
        print(f"  {label}: {count} districts")

    # Export
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
    print(f"\nLISA results saved: {lisa_path}")


if __name__ == "__main__":
    main()
