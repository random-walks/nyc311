#!/usr/bin/env python3
"""Step 5: Spatial analysis of rodent complaint patterns.

Tests for spatial clustering of rodent complaints using Global Moran's I
and LISA, then computes the Theil inequality index and equity gap factor
across community districts.  Uses real boundaries from ``nyc_geo_toolkit``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared.diagnostics import interpret_moran, interpret_theil

DATA_DIR = Path(__file__).parent / "data"
DEMOGRAPHICS_PATH = DATA_DIR / "demographics.csv"


def run() -> dict:
    """Run spatial analysis on the rodent complaint panel."""
    from nyc311.geographies import load_nyc_boundaries
    from nyc311.stats import global_morans_i, local_morans_i, theil_index
    from nyc311.temporal import build_distance_weights, centroids_from_boundaries

    df = pd.read_parquet(DATA_DIR / "panel.parquet")
    results: dict = {}

    # ── Mean rodent complaints per district ──────────────────────────
    mean_complaints = df.groupby("unit_id")["complaint_count"].mean().to_dict()

    # ── Load real boundaries and centroids ───────────────────────────
    boundaries = load_nyc_boundaries("community_district")
    centroids = centroids_from_boundaries(boundaries)
    print(f"  Loaded {len(centroids)} community district centroids")

    shared = sorted(set(mean_complaints) & set(centroids))
    mean_complaints = {k: mean_complaints[k] for k in shared}
    centroids = {k: centroids[k] for k in shared}

    weights = build_distance_weights(centroids, threshold_meters=3000.0)

    # ── Global Moran's I ─────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("Global Moran's I: Spatial Clustering of Rodent Complaints")
    print("=" * 72)

    moran = global_morans_i(mean_complaints, weights)
    print(interpret_moran(moran))

    results["moran_i"] = float(moran.statistic)
    results["moran_p"] = float(moran.p_value)
    results["moran_z"] = float(moran.z_score)

    # ── LISA ──────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("LISA Cluster Analysis")
    print("=" * 72)

    lisa = local_morans_i(mean_complaints, weights)
    cluster_counts: dict[str, int] = {}
    for label in lisa.cluster_labels:
        cluster_counts[label] = cluster_counts.get(label, 0) + 1

    for label, count in sorted(cluster_counts.items()):
        print(f"  {label}: {count} districts")

    # Show HH hotspots
    hh_districts = [
        uid
        for uid, label in zip(lisa.unit_ids, lisa.cluster_labels, strict=True)
        if label == "HH"
    ]
    if hh_districts:
        print(f"\n  Rodent hotspots (HH clusters): {', '.join(hh_districts)}")

    results["lisa_clusters"] = cluster_counts

    # ── Theil inequality index ───────────────────────────────────────
    print("\n" + "=" * 72)
    print("Theil T Index: Inequality in Rodent Complaint Rates")
    print("=" * 72)

    # Load real populations from demographics.csv
    if DEMOGRAPHICS_PATH.exists():
        demo = pd.read_csv(DEMOGRAPHICS_PATH, index_col="unit_id")
        pop_shared = sorted(set(shared) & set(demo.index))
        populations = {uid: int(demo.loc[uid, "population"]) for uid in pop_shared}
        values = {uid: mean_complaints[uid] for uid in pop_shared}
    else:
        # Fall back to using complaint counts as self-weights
        populations = dict.fromkeys(shared, 1)
        values = mean_complaints
        pop_shared = shared

    borough_map = {
        uid: " ".join(uid.split()[:-1]) if " " in uid else uid for uid in pop_shared
    }

    theil_result = theil_index(
        values=values,
        populations=populations,
        groups=borough_map,
    )
    print(interpret_theil(theil_result))

    results["theil_total"] = theil_result.total
    results["theil_between"] = theil_result.between_group
    results["theil_within"] = theil_result.within_group

    # ── Equity Gap Factor ────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("Equity Gap Factor (rodent complaints vs. city median)")
    print("=" * 72)

    unit_medians = df.groupby("unit_id")["complaint_count"].median()
    citywide_median = unit_medians.median()
    if citywide_median > 0:
        egf = (unit_medians / citywide_median).sort_values(ascending=False)
        print(f"  City-wide median: {citywide_median:.0f} complaints/month")
        print("\n  Top 5 highest-burden districts:")
        for uid, val in egf.head(5).items():
            print(f"    {uid}: EGF = {val:.2f} ({unit_medians[uid]:.0f}/mo)")
        print("\n  Bottom 5 lowest-burden districts:")
        for uid, val in egf.tail(5).items():
            print(f"    {uid}: EGF = {val:.2f} ({unit_medians[uid]:.0f}/mo)")

    return results


if __name__ == "__main__":
    print("Step 5: Spatial Analysis\n")
    run()
