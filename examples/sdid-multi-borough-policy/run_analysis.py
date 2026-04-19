#!/usr/bin/env python3
"""SDID multi-borough rollout case study — end-to-end.

A self-contained showcase for
:func:`factor_factory.engines.sdid.estimate` over an nyc311
PanelDataset. Uses synthetic data so it runs offline in seconds.
"""

from __future__ import annotations

import json
import random
from datetime import date
from pathlib import Path

from factor_factory.engines.did import estimate as did_estimate
from factor_factory.engines.sdid import estimate as sdid_estimate
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


_BOROUGHS: tuple[str, ...] = (
    "MANHATTAN",
    "BROOKLYN",
    "BRONX",
    "QUEENS",
    "STATEN ISLAND",
)

# Month-index (from start) when each borough adopts the (fake) rollout.
# SDID (Arkhangelsky et al. 2021) requires a single common treatment date
# across all treated units, so Manhattan / Brooklyn / Bronx synchronize on
# month 18. Queens and Staten Island are donor (never-treated) controls.
_COMMON_ADOPTION_MONTH: int = 18
_TREATED_BOROUGHS: tuple[str, ...] = ("MANHATTAN", "BROOKLYN", "BRONX")
_ADOPTION: dict[str, int | None] = {
    b: _COMMON_ADOPTION_MONTH if b in _TREATED_BOROUGHS else None for b in _BOROUGHS
}


def _build_synthetic_panel(seed: int = 20260419) -> PanelDataset:
    """A 5-borough x 36-month resolution-rate panel with staggered adoption."""
    rng = random.Random(seed)
    periods = tuple(f"{2023 + (m // 12)}-{(m % 12) + 1:02d}" for m in range(36))

    baseline_rate = 0.80
    treatment_lift = 0.05
    borough_fe = {b: rng.uniform(-0.05, 0.05) for b in _BOROUGHS}
    period_trend = 0.002

    observations: list[PanelObservation] = []
    for b in _BOROUGHS:
        adopt = _ADOPTION[b]
        for idx, p in enumerate(periods):
            treated = adopt is not None and idx >= adopt
            rate = (
                baseline_rate
                + borough_fe[b]
                + idx * period_trend
                + (treatment_lift if treated else 0.0)
                + rng.uniform(-0.01, 0.01)
            )
            n = 1_500 + int(rng.uniform(-100, 100))
            observations.append(
                PanelObservation(
                    unit_id=b,
                    period=p,
                    complaint_count=n,
                    complaint_counts_by_type={"Rodent": n},
                    resolution_rate=max(0.0, min(1.0, rate)),
                    median_resolution_days=7.0 + rng.uniform(-0.5, 0.5),
                    treatment=treated,
                    treatment_date=(
                        date(
                            2023 + (adopt // 12),
                            (adopt % 12) + 1,
                            1,
                        )
                        if adopt is not None
                        else None
                    ),
                    population=1_000_000,
                )
            )

    common_date = date(
        2023 + (_COMMON_ADOPTION_MONTH // 12),
        (_COMMON_ADOPTION_MONTH % 12) + 1,
        1,
    )
    treatment_events = (
        TreatmentEvent(
            name="synchronized_311_rollout",
            description=(
                "(fake) synchronized expanded 311 intake rollout across "
                "Manhattan, Brooklyn, and the Bronx"
            ),
            treated_units=_TREATED_BOROUGHS,
            treatment_date=common_date,
            geography="borough",
        ),
    )

    return PanelDataset(
        observations=tuple(observations),
        unit_type="borough",
        periods=periods,
        treatment_events=treatment_events,
    )


def main() -> None:
    """Run the full SDID multi-borough case study."""
    ARTIFACTS.mkdir(exist_ok=True)
    MANUSCRIPTS.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)

    print("=" * 64)
    print("  SDID multi-borough 311 rollout — synthetic case study")
    print("=" * 64)

    # Step 1: synthetic panel
    print("\n-- Step 1: Build synthetic 5-borough x 36-month panel --\n")
    dataset = _build_synthetic_panel()
    print(
        f"  {len(dataset.unit_ids)} boroughs x {len(dataset.periods)} "
        f"months ({len(dataset.observations)} observations)"
    )
    treated = [ev.name for ev in dataset.treatment_events]
    print(f"  Treated: {', '.join(treated)}")

    # Step 2: adapter → factor-factory Panel
    print("\n-- Step 2: Adapter: PanelDataset → factor_factory.tidy.Panel --\n")
    panel = dataset.to_factor_factory_panel(outcome_col="resolution_rate")
    print(
        f"  Panel: {panel.summary()['n_units']} units, "
        f"{panel.summary()['n_periods']} periods, "
        f"outcome={panel.outcome_col}"
    )
    panel.to_parquet(DATA / "panel.parquet")

    # Step 3: TWFE baseline
    print("\n-- Step 3: TWFE DiD baseline --\n")
    did_results = did_estimate(panel, methods=("twfe",), outcome="resolution_rate")
    did_record = did_results[0].to_dict()
    print(
        f"  TWFE ATT: {did_record['att']:+.4f} "
        f"(SE={did_record['se']:.4f}, p={did_record['p_value']:.3f})"
    )
    (ARTIFACTS / "did_results.json").write_text(
        json.dumps([did_record], indent=2, default=str)
    )

    # Step 4: SDID (the headline)
    print("\n-- Step 4: Synthetic DiD (Arkhangelsky et al. 2021) --\n")
    sdid_results = sdid_estimate(panel, methods=("sdid",), outcome="resolution_rate")
    sdid_records = sdid_results.to_records()
    sdid_record = sdid_records[0]
    print(
        f"  SDID ATT: {sdid_record['att']:+.4f} "
        f"(n_treated={sdid_record.get('n_treated', 'n/a')}, "
        f"n_control={sdid_record.get('n_control', 'n/a')})"
    )
    (ARTIFACTS / "sdid_results.json").write_text(
        json.dumps(sdid_records, indent=2, default=str)
    )

    # Step 5: tearsheets
    print("\n-- Step 5: Render jellycell tearsheets --\n")
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
        except Exception as exc:  # noqa: BLE001
            print(f"  tearsheet {renderer.__name__} FAILED: {exc}")

    print("\n" + "=" * 64)
    print(f"  SDID case study complete. Tearsheets in {MANUSCRIPTS}")
    print("=" * 64)


if __name__ == "__main__":
    main()
