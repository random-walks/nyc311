#!/usr/bin/env python3
"""Minimal no-jellycell showcase: PanelDataset → ff.Panel → DiD → pandas."""

from __future__ import annotations

from datetime import date

import pandas as pd
from factor_factory.engines.did import estimate as did_estimate

from nyc311.temporal import PanelDataset, PanelObservation, TreatmentEvent


def build_synthetic_panel() -> PanelDataset:
    """A 6-unit x 24-period panel with a known ATT of -5 on MANHATTAN 03."""
    units = (
        "BRONX 01",
        "BROOKLYN 01",
        "MANHATTAN 03",
        "QUEENS 04",
        "STATEN ISLAND 01",
        "MANHATTAN 10",
    )
    periods = tuple(f"2024-{m:02d}" for m in range(1, 13)) + tuple(
        f"2025-{m:02d}" for m in range(1, 13)
    )
    event = TreatmentEvent(
        name="rat_containerization_pilot",
        description="(synthetic) pilot begins 2025-01 in MANHATTAN 03",
        treated_units=("MANHATTAN 03",),
        treatment_date=date(2025, 1, 1),
        geography="community_district",
    )

    rows: list[PanelObservation] = []
    for u_idx, u in enumerate(units):
        for i, p in enumerate(periods):
            is_treated = u == "MANHATTAN 03" and i >= 12
            count = int(50 + u_idx * 1.5 + i * 0.2 + (-5 if is_treated else 0))
            # median_resolution_days drops 5 days post-treatment on the
            # treated unit — gives the showcase a parallel resolution-time
            # signal. (See §"What's also in the panel" in README.)
            median_res = 7.0 + (-5.0 if is_treated else 0.0)
            rows.append(
                PanelObservation(
                    unit_id=u,
                    period=p,
                    complaint_count=count,
                    complaint_counts_by_type={"Rodent": count},
                    resolution_rate=0.9,
                    median_resolution_days=median_res,
                    treatment=is_treated,
                    treatment_date=date(2025, 1, 1) if u == "MANHATTAN 03" else None,
                    population=100_000,
                )
            )
    return PanelDataset(
        observations=tuple(rows),
        unit_type="community_district",
        periods=periods,
        treatment_events=(event,),
    )


def main() -> None:
    dataset = build_synthetic_panel()
    print(
        f"-- built {len(dataset.unit_ids)} units x {len(dataset.periods)} periods PanelDataset --"
    )

    panel = dataset.to_factor_factory_panel()
    print("-- adapted to factor_factory.tidy.Panel --")
    print(f"   outcome_col={panel.outcome_col}, dimension={panel.dimension}")

    # Showcase 1: DiD on complaint volume.
    print("-- fitting DiD (TWFE) on complaint_count --")
    results = did_estimate(panel, methods=("twfe",), outcome="complaint_count")
    df = pd.DataFrame([results[0].to_dict()])[
        ["method", "att", "se", "ci_95_lower", "ci_95_upper", "p_value", "n"]
    ]
    print(df.to_string(index=True))

    # Showcase 2: same engine, different outcome column. The adapter
    # exposes every numeric panel column to the engine — swap `outcome=`
    # to pivot from volume to resolution latency without rebuilding the
    # panel. This is the v1.0.1 closed_date / median_resolution_days
    # workflow consumers were asking for.
    print("\n-- fitting DiD (TWFE) on median_resolution_days --")
    results_latency = did_estimate(
        panel, methods=("twfe",), outcome="median_resolution_days"
    )
    df_latency = pd.DataFrame([results_latency[0].to_dict()])[
        ["method", "att", "se", "ci_95_lower", "ci_95_upper", "p_value", "n"]
    ]
    print(df_latency.to_string(index=True))


if __name__ == "__main__":
    main()
