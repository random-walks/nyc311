#!/usr/bin/env python3
"""Four-way mediation decomposition case study — end-to-end.

A self-contained showcase for
:class:`factor_factory.engines.mediation.four_way.FourWayMediationEngine`
on an nyc311 PanelDataset. Uses synthetic data so it runs offline.

Causal structure:

    pilot (treatment) → triage_time_days (mediator) → resolution_rate (outcome)
                     └──── direct effect of pilot on resolution ────┘

Reference: VanderWeele, T. J. (2014). A unification of mediation
and interaction: a 4-way decomposition. *Epidemiology*, 25(5), 749-761.
"""

from __future__ import annotations

import json
import random
from datetime import date
from pathlib import Path

from factor_factory.engines.mediation import estimate as mediation_estimate
from factor_factory.jellycell import tearsheets

from nyc311.temporal import (
    PanelDataset,
    PanelObservation,
    TreatmentEvent,
)

HERE = Path(__file__).parent
DATA = HERE / "data"
ARTIFACTS = HERE / "artifacts"
MANUSCRIPTS = HERE / "manuscripts"

# Causal-model coefficients for the synthetic data.
# True Controlled Direct Effect of treatment on outcome: +0.03
# True Pure Indirect Effect through triage_time_days: ≈ -0.05 * treatment-induced-change-in-triage
# With treatment lowering triage by 2 days and outcome response of -0.02 per day:
#     PIE ≈ 0.04
# Total effect should be roughly +0.07.
_ALPHA_TREATMENT_ON_MEDIATOR = -2.0  # days
_BETA_TREATMENT_ON_OUTCOME = +0.03  # direct
_BETA_MEDIATOR_ON_OUTCOME = -0.02  # per day of triage
_BASELINE_RESOLUTION = 0.75
_BASELINE_TRIAGE = 12.0


def _build_synthetic_panel(seed: int = 20260420) -> PanelDataset:
    """Build a balanced panel with mediator + outcome wired to a cascade.

    30 community districts x 12 monthly periods. Half the districts are
    treated with the pilot from period 6 onwards.
    """
    rng = random.Random(seed)
    n_districts = 30
    units = tuple(f"CD-{i:02d}" for i in range(n_districts))
    periods = tuple(f"2025-{m:02d}" for m in range(1, 13))

    treated_units = units[::2]  # even-indexed districts treated
    treatment_date = date(2025, 6, 1)
    treatment_period_idx = 5  # 0-indexed: June is index 5

    event = TreatmentEvent(
        name="operational_pilot",
        description=(
            "(fake) 311 operational pilot: streamlined intake intended to "
            "reduce triage time and therefore raise resolution rate"
        ),
        treated_units=treated_units,
        treatment_date=treatment_date,
        geography="community_district",
    )

    observations: list[PanelObservation] = []
    for u in units:
        unit_fe = rng.uniform(-0.02, 0.02)
        for i, p in enumerate(periods):
            is_treated = (u in treated_units) and (i >= treatment_period_idx)
            treatment_flag = 1.0 if is_treated else 0.0

            # Mediator: triage time in days
            triage = (
                _BASELINE_TRIAGE
                + _ALPHA_TREATMENT_ON_MEDIATOR * treatment_flag
                + rng.gauss(0, 0.5)
            )

            # Outcome: resolution rate
            resolution = (
                _BASELINE_RESOLUTION
                + unit_fe
                + _BETA_TREATMENT_ON_OUTCOME * treatment_flag
                + _BETA_MEDIATOR_ON_OUTCOME * (triage - _BASELINE_TRIAGE)
                + rng.gauss(0, 0.01)
            )
            resolution = max(0.0, min(1.0, resolution))

            complaint_count = 100 + int(rng.uniform(-10, 10))

            observations.append(
                PanelObservation(
                    unit_id=u,
                    period=p,
                    complaint_count=complaint_count,
                    complaint_counts_by_type={"HEAT/HOT WATER": complaint_count},
                    resolution_rate=resolution,
                    median_resolution_days=triage,
                    treatment=is_treated,
                    treatment_date=treatment_date if u in treated_units else None,
                    population=80_000,
                    covariates={"triage_time_days": triage},
                )
            )

    return PanelDataset(
        observations=tuple(observations),
        unit_type="community_district",
        periods=periods,
        treatment_events=(event,),
    )


def main() -> None:
    """Run the full mediation cascade case study."""
    ARTIFACTS.mkdir(exist_ok=True)
    MANUSCRIPTS.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)

    print("=" * 64)
    print("  Mediation cascade (four-way decomposition) — synthetic")
    print("=" * 64)

    # Step 1: synthetic panel
    print("\n-- Step 1: Build synthetic cascade panel --\n")
    dataset = _build_synthetic_panel()
    print(
        f"  {len(dataset.unit_ids)} districts x "
        f"{len(dataset.periods)} months "
        f"({len(dataset.observations)} observations)"
    )
    print(
        f"  Treated: {len(dataset.treatment_events[0].treated_units)} / {len(dataset.unit_ids)}"
    )

    # Step 2: adapter → factor-factory Panel
    print("\n-- Step 2: Adapter: PanelDataset → factor_factory.tidy.Panel --\n")
    panel = dataset.to_factor_factory_panel(outcome_col="resolution_rate")
    print(f"  Panel columns: {sorted(panel.df.columns)}")
    panel.to_parquet(DATA / "panel.parquet")

    # Step 3: mediation (four-way)
    print("\n-- Step 3: Four-way mediation decomposition --\n")
    results = mediation_estimate(
        panel,
        methods=("four_way",),
        outcome="resolution_rate",
        treatment="treatment",
        mediator="triage_time_days",
        n_bootstrap=200,
    )
    records = results.to_records()
    record = records[0]

    print(f"  Total effect: {record.get('total_effect'):+.4f}")
    print(f"  CDE (direct, mediator held):      {record.get('cde'):+.4f}")
    print(f"  INTref (reference interaction):   {record.get('int_ref'):+.4f}")
    print(f"  INTmed (mediated interaction):    {record.get('int_med'):+.4f}")
    print(f"  PIE (pure indirect via mediator): {record.get('pie'):+.4f}")
    pm = record.get("proportion_mediated")
    if pm is not None:
        print(f"  Proportion mediated:              {pm:.1%}")

    (ARTIFACTS / "mediation_results.json").write_text(
        json.dumps(records, indent=2, default=str)
    )

    # Step 4: tearsheets
    print("\n-- Step 4: Render jellycell tearsheets --\n")
    project_dir = str(HERE)
    for renderer in (
        tearsheets.methodology,
        tearsheets.diagnostics,
        tearsheets.findings,
        tearsheets.audit,
        tearsheets.manuscript,
    ):
        try:
            path = renderer(project_dir, overwrite=True)
            print(f"  {path.name}")
        except Exception as exc:
            print(f"  tearsheet {renderer.__name__} FAILED: {exc}")

    print("\n" + "=" * 64)
    print(f"  Mediation case study complete. Tearsheets in {MANUSCRIPTS}")
    print("=" * 64)


if __name__ == "__main__":
    main()
