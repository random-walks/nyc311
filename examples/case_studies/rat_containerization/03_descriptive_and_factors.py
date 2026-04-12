#!/usr/bin/env python3
"""Step 3: Descriptive analysis and factor pipeline on real rodent data.

Runs the nyc311 factor pipeline over every (community district, month)
cell in the panel, computing complaint volume, response rate, topic
concentration, and recurrence rate.  Also profiles the data by borough,
top complaint descriptors, and resolution statistics.
"""

from __future__ import annotations

import pickle
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"


def run() -> dict:
    """Run descriptive analysis and factor pipeline on real rodent data."""
    from nyc311.factors import (
        ComplaintVolumeFactor,
        FactorContext,
        Pipeline,
        RecurrenceFactor,
        ResponseRateFactor,
        TopicConcentrationFactor,
    )
    from nyc311.io import load_service_requests

    # ── Load raw records for factor pipeline ─────────────────────────
    cache_dir = DATA_DIR / "cache"
    csv_files = sorted(cache_dir.glob("*.csv"))
    all_records = []
    for csv_path in csv_files:
        all_records.extend(load_service_requests(csv_path))

    print(f"  Total rodent complaints: {len(all_records):,}")

    # ── Borough breakdown ────────────────────────────────────────────
    borough_counts = Counter(r.borough for r in all_records)
    print("\n  Complaints by borough:")
    for boro, cnt in borough_counts.most_common():
        print(f"    {boro}: {cnt:,} ({cnt / len(all_records):.1%})")

    # ── Top descriptors ──────────────────────────────────────────────
    descriptor_counts = Counter(r.descriptor for r in all_records)
    print("\n  Top 10 complaint descriptors:")
    for desc, cnt in descriptor_counts.most_common(10):
        res_count = sum(
            1
            for r in all_records
            if r.descriptor == desc and r.resolution_description is not None
        )
        res_rate = res_count / cnt if cnt > 0 else 0
        print(f"    {desc}: {cnt:,} ({res_rate:.0%} resolved)")

    # ── Resolution statistics ────────────────────────────────────────
    resolved = [r for r in all_records if r.resolution_description is not None]
    print(
        f"\n  Overall resolution rate: {len(resolved):,}/{len(all_records):,} "
        f"({len(resolved) / len(all_records):.1%})"
    )

    # ── Factor pipeline ──────────────────────────────────────────────
    panel = pickle.loads((DATA_DIR / "panel.pkl").read_bytes())

    # Group records by (community_district, period)
    grouped: dict[tuple[str, str], list] = defaultdict(list)
    for rec in all_records:
        period = pd.Timestamp(rec.created_date).to_period("M")
        key = (rec.community_district, str(period))
        grouped[key].append(rec)

    contexts = []
    for obs in panel.observations:
        recs = grouped.get((obs.unit_id, obs.period), [])
        contexts.append(
            FactorContext(
                geography="community_district",
                geography_value=obs.unit_id,
                complaints=tuple(recs),
                time_window_start=date(2023, 1, 1),
                time_window_end=date(2024, 12, 31),
                total_population=obs.population,
            )
        )

    pipeline = (
        Pipeline()
        .add(ComplaintVolumeFactor())
        .add(ResponseRateFactor())
        .add(TopicConcentrationFactor())
        .add(RecurrenceFactor())
    )

    result = pipeline.run(contexts)
    df = result.to_dataframe()

    print(
        f"\n  Factor pipeline: {len(contexts)} contexts, {len(result.columns)} factors"
    )
    print(f"    Mean complaint volume: {df['complaint_volume'].mean():.1f}")
    print(f"    Mean response rate: {df['response_rate'].mean():.3f}")
    print(f"    Mean topic concentration (HHI): {df['topic_concentration'].mean():.4f}")
    print(f"    Mean recurrence rate: {df['recurrence_rate'].mean():.3f}")

    # Top/bottom districts by mean volume from the panel directly
    panel_df = panel.to_dataframe()
    unit_vol = panel_df.groupby("unit_id")["complaint_count"].mean().sort_values()
    print("\n  Top 5 districts by mean monthly rodent complaints:")
    for uid, vol in unit_vol.nlargest(5).items():
        print(f"    {uid}: {vol:.1f}")
    print("\n  Bottom 5 districts:")
    for uid, vol in unit_vol.nsmallest(5).items():
        print(f"    {uid}: {vol:.1f}")

    return {
        "n_records": len(all_records),
        "n_resolved": len(resolved),
        "resolution_rate": len(resolved) / len(all_records),
        "borough_counts": dict(borough_counts),
        "top_descriptors": dict(descriptor_counts.most_common(10)),
        "mean_volume": float(df["complaint_volume"].mean()),
        "mean_response_rate": float(df["response_rate"].mean()),
        "mean_topic_concentration": float(df["topic_concentration"].mean()),
        "mean_recurrence_rate": float(df["recurrence_rate"].mean()),
    }


if __name__ == "__main__":
    print("Step 3: Descriptive Analysis + Factor Pipeline\n")
    run()
