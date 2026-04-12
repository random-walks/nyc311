#!/usr/bin/env python3
"""Step 5: Regression discontinuity at the mandate zone boundary.

Uses real lat/lon coordinates from Rodent complaints and real community
district boundaries from ``nyc_geo_toolkit`` to compute each complaint's
signed distance from the treated zone.  A sharp RD design exploits the
boundary between pilot-zone (Manhattan) and control districts.

Calonico, Cattaneo, & Titiunik (2014).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared.diagnostics import interpret_rdd

if TYPE_CHECKING:
    from nyc311.stats import RDResult

DATA_DIR = Path(__file__).parent / "data"

# Manhattan CDs in the pilot zone (from 02_build_panel.py)
TREATED_CDS = {
    "MANHATTAN 01",
    "MANHATTAN 02",
    "MANHATTAN 03",
    "MANHATTAN 04",
    "MANHATTAN 05",
    "MANHATTAN 06",
    "MANHATTAN 07",
    "MANHATTAN 08",
    "MANHATTAN 09",
}


def run() -> RDResult | None:
    """Compute signed distance from treated zone and run RDD."""
    import numpy as np

    from nyc311.geographies import load_nyc_boundaries
    from nyc311.io import load_service_requests
    from nyc311.stats import regression_discontinuity
    from nyc311.temporal import centroids_from_boundaries
    from nyc_geo_toolkit import haversine_distance_meters

    # 1. Load real complaint records with coordinates
    cache_dir = DATA_DIR / "cache"
    csv_files = sorted(cache_dir.glob("*.csv"))
    if not csv_files:
        print("No cached CSV files. Run 01_fetch_data.py first.")
        return None

    all_records = []
    for csv_path in csv_files:
        all_records.extend(load_service_requests(csv_path))

    geo_records = [
        r for r in all_records if r.latitude is not None and r.longitude is not None
    ]
    print(f"  {len(geo_records):,} geocoded complaints (of {len(all_records):,} total)")

    if len(geo_records) < 10:
        print("  Too few geocoded records for RDD. Skipping.")
        return None

    # 2. Load real community district boundaries and compute treated-zone centroid
    boundaries = load_nyc_boundaries("community_district")
    centroids = centroids_from_boundaries(boundaries)

    treated_centroids = [centroids[cd] for cd in TREATED_CDS if cd in centroids]
    if not treated_centroids:
        print("  No treated-zone centroids found. Skipping.")
        return None

    treated_lat = np.mean([c[0] for c in treated_centroids])
    treated_lon = np.mean([c[1] for c in treated_centroids])
    print(f"  Treated-zone centroid: ({treated_lat:.4f}, {treated_lon:.4f})")

    # 3. Compute signed distance for each complaint
    #    Negative = inside treated zone, Positive = outside
    distances = []
    counts = []
    for r in geo_records:
        dist_m = haversine_distance_meters(
            r.latitude, r.longitude, treated_lat, treated_lon
        )
        dist_km = dist_m / 1000.0
        # Sign: negative if complaint is in a treated CD, positive otherwise
        in_treated = r.community_district in TREATED_CDS
        signed_dist = -dist_km if in_treated else dist_km
        distances.append(signed_dist)
        counts.append(1.0)  # complaint indicator

    distances_arr = np.array(distances)

    # 4. Bin complaints into distance bands and compute mean complaint density
    #    to create a smoother outcome variable
    bin_width = 0.5  # km
    max_dist = 15.0
    bin_edges = np.arange(-max_dist, max_dist + bin_width, bin_width)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    binned_counts = []
    binned_dists = []
    for i in range(len(bin_edges) - 1):
        mask = (distances_arr >= bin_edges[i]) & (distances_arr < bin_edges[i + 1])
        n = mask.sum()
        if n > 0:
            binned_dists.append(bin_centers[i])
            binned_counts.append(float(n))

    if len(binned_dists) < 6:
        print("  Too few distance bins with data. Skipping RDD.")
        return None

    x = np.array(binned_dists)
    y = np.array(binned_counts)

    print(f"  Distance bins: {len(x)} (range: {x.min():.1f} to {x.max():.1f} km)")
    print(f"  Complaints inside treated zone: {(distances_arr < 0).sum():,}")
    print(f"  Complaints outside treated zone: {(distances_arr >= 0).sum():,}")

    # 5. Run regression discontinuity
    result = regression_discontinuity(x, y, cutoff=0.0)

    print()
    print(interpret_rdd(result))
    return result


if __name__ == "__main__":
    print("Step 5: Spatial Discontinuity (RDD)\n")
    run()
