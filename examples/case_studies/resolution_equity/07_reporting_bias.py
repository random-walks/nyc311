#!/usr/bin/env python3
"""Step 7: Latent reporting bias estimation via EM.

Uses ``latent_reporting_bias_em()`` to separate observed complaint counts
into estimated true complaint rates and unit-level reporting probabilities.
Units with low reporting probabilities may be under-reporting relative
to their true underlying conditions (O'Brien et al., 2015).

If a ``data/demographics.csv`` with real ACS covariates is present, it
is used to improve the EM estimation.  Otherwise the model runs without
covariates (estimating a baseline reporting probability).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared.diagnostics import interpret_reporting_bias

from nyc311.stats import latent_reporting_bias_em

DATA_DIR = Path(__file__).parent / "data"
DEMOGRAPHICS_PATH = DATA_DIR / "demographics.csv"


def main() -> None:
    panel_path = DATA_DIR / "panel.parquet"
    if not panel_path.exists():
        print("Panel not found. Run 02_build_panel.py first.")
        return

    df = pd.read_parquet(panel_path)

    # ── Per-unit aggregation ─────────────────────────────────────────
    unit_totals = df.groupby("unit_id")["complaint_count"].sum()

    # Use real population if available; otherwise use complaint counts as proxy
    if "population" in df.columns and not df["population"].isna().all():
        unit_pop = df.groupby("unit_id")["population"].first().dropna()
        pop_source = "panel population data"
    else:
        # Use total observations as a population-proportional proxy
        unit_pop = df.groupby("unit_id").size()
        pop_source = "observation count proxy (no population data in panel)"
    print(f"  Population source: {pop_source}")

    shared_units = sorted(set(unit_totals.index) & set(unit_pop.index))
    complaint_counts = {uid: int(unit_totals[uid]) for uid in shared_units}
    populations = {uid: max(int(unit_pop[uid]), 1) for uid in shared_units}
    n = len(shared_units)

    # ── Load real demographics (required) ───────────────────────────
    if not DEMOGRAPHICS_PATH.exists():
        msg = (
            f"demographics.csv not found at {DEMOGRAPHICS_PATH}. "
            "This file is required for reporting bias estimation. "
            "It should contain ACS 5-year estimates with columns: "
            "unit_id, population, pct_nonwhite, log_median_income, pct_renter."
        )
        raise FileNotFoundError(msg)

    demo = pd.read_csv(DEMOGRAPHICS_PATH, index_col="unit_id")
    # Use ACS population for the EM model (overrides panel proxy)
    shared_demo = sorted(set(shared_units) & set(demo.index))
    populations = {uid: int(demo.loc[uid, "population"]) for uid in shared_demo}
    complaint_counts = {uid: complaint_counts[uid] for uid in shared_demo}
    n = len(shared_demo)

    cov_cols = ["pct_nonwhite", "log_median_income", "pct_renter"]
    covariates: dict[str, dict[str, float]] = {
        uid: {col: float(demo.loc[uid, col]) for col in cov_cols} for uid in shared_demo
    }
    print(f"  Loaded ACS demographics for {n} districts ({len(cov_cols)} covariates)")

    # ── Run EM estimation ────────────────────────────────────────────
    print(f"\nRunning latent_reporting_bias_em on {n} units ...")
    em_result = latent_reporting_bias_em(
        complaint_counts,
        populations,
        covariates,
    )

    # ── Diagnostic interpretation ────────────────────────────────────
    print("\n" + "=" * 72)
    print(interpret_reporting_bias(em_result=em_result))
    print("=" * 72)

    # ── Top / bottom reporting probabilities ──────────────────────────
    rho = em_result.reporting_probabilities
    sorted_by_rho = sorted(rho.items(), key=lambda x: x[1])

    print("\nTop 5 units with HIGHEST estimated reporting probability:")
    for uid, prob in sorted_by_rho[-5:][::-1]:
        true_rate = em_result.estimated_true_rates.get(uid, float("nan"))
        print(f"  {uid:>20s}  rho = {prob:.4f}  true_rate = {true_rate:.2f}")

    print("\nTop 5 units with LOWEST estimated reporting probability:")
    for uid, prob in sorted_by_rho[:5]:
        true_rate = em_result.estimated_true_rates.get(uid, float("nan"))
        print(f"  {uid:>20s}  rho = {prob:.4f}  true_rate = {true_rate:.2f}")


if __name__ == "__main__":
    main()
