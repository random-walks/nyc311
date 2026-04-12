#!/usr/bin/env python3
"""Step 4: Equity analysis -- regression, inequality, and decomposition.

Combines three complementary methods to assess whether 311 resolution
times differ systematically across community districts:

1. **Two-way fixed effects regression** (Wooldridge, 2010) tests whether
   complaint volume predicts resolution time after controlling for
   district and time fixed effects.
2. **Theil T index** (Theil, 1967) quantifies inequality in complaint
   rates across districts, decomposed between and within boroughs.
3. **Oaxaca-Blinder decomposition** (Oaxaca, 1973; Blinder, 1973)
   decomposes the resolution-time gap between high- and low-volume
   districts into explained and unexplained components.  If a
   ``data/demographics.csv`` is provided with real ACS data, it uses
   demographic covariates; otherwise it uses complaint-volume-based
   grouping.
4. **Equity Gap Factor** -- ratio of each district's resolution time
   to the citywide median.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared.diagnostics import (
    interpret_oaxaca_blinder,
    interpret_panel_regression,
    interpret_theil,
)

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
DEMOGRAPHICS_PATH = DATA_DIR / "demographics.csv"


def _load_demographics(units: pd.Index) -> pd.DataFrame | None:
    """Load real demographics from CSV if available."""
    if not DEMOGRAPHICS_PATH.exists():
        return None
    demo = pd.read_csv(DEMOGRAPHICS_PATH, index_col="unit_id")
    # Only keep units present in the panel
    shared = sorted(set(demo.index) & set(units))
    if not shared:
        return None
    return demo.loc[shared]


def main() -> None:
    panel_path = DATA_DIR / "panel.parquet"
    if not panel_path.exists():
        print("Panel not found. Run 02_build_panel.py first.")
        return

    df = pd.read_parquet(panel_path)
    units = df.index.get_level_values("unit_id").unique()

    df["log_complaints"] = np.log1p(df["complaint_count"])

    # Load real demographics (required)
    demo = _load_demographics(units)
    if demo is None:
        msg = (
            f"demographics.csv not found at {DEMOGRAPHICS_PATH}. "
            "This file is required for the equity analysis. "
            "It should contain ACS 5-year estimates with columns: "
            "unit_id, population, pct_nonwhite, log_median_income, pct_renter."
        )
        raise FileNotFoundError(msg)

    df = df.join(demo, on="unit_id", rsuffix="_demo")
    n_matched = df.index.get_level_values("unit_id").isin(demo.index).sum()
    print(
        f"  Loaded ACS demographics for {len(demo)} districts ({n_matched} panel rows matched)"
    )

    # Ensure time index is date-like for linearmodels
    if isinstance(df.index, pd.MultiIndex):
        period_level = df.index.get_level_values(1)
        if not isinstance(period_level, pd.DatetimeIndex):
            unit_level = df.index.get_level_values(0)
            period_level = pd.DatetimeIndex(pd.to_datetime(list(period_level)))
            df.index = pd.MultiIndex.from_arrays(
                [unit_level, period_level], names=df.index.names
            )

    # ── 1. Two-way fixed effects regression ──────────────────────────
    print("\n" + "=" * 72)
    print("1. Two-Way Fixed Effects: Median Resolution Days")
    print("   Entity FE: community district | Time FE: month")
    print("   Clustered SE: district level")
    print("=" * 72)

    try:
        from linearmodels.panel import PanelOLS
    except ImportError:
        print("linearmodels not installed. Run: pip install nyc311[stats]")
        return

    if df["median_resolution_days"].isna().all():
        print("No resolution data available; skipping regression.")
        return

    y = df["median_resolution_days"].dropna()
    x_cols = ["log_complaints"]
    x = df.loc[y.index, x_cols]

    model = PanelOLS(y, x, entity_effects=True, time_effects=True)
    result = model.fit(cov_type="clustered", cluster_entity=True)

    from nyc311.stats import PanelRegressionResult

    panel_result = PanelRegressionResult(
        method="two_way_fe",
        coefficients={str(k): float(v) for k, v in result.params.items()},
        std_errors={str(k): float(v) for k, v in result.std_errors.items()},
        p_values={str(k): float(v) for k, v in result.pvalues.items()},
        r_squared=float(result.rsquared),
        n_observations=int(result.nobs),
        n_entities=int(result.entity_info.total),
        n_periods=int(result.time_info.total),
        model_summary=str(result.summary),
    )

    print(interpret_panel_regression(panel_result))

    figures_dir = Path(__file__).parent / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    coef_df = pd.DataFrame(
        {
            "coef": result.params,
            "se": result.std_errors,
            "t": result.tstats,
            "p": result.pvalues,
        }
    )
    coef_df["sig"] = coef_df["p"].apply(
        lambda p: (
            "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else ""))
        )
    )
    coef_path = figures_dir / "equity_coefficients.csv"
    coef_df.to_csv(coef_path)
    print(f"\nCoefficient table saved: {coef_path}")

    # ── 2. Theil T index on complaint rates ──────────────────────────
    print("\n" + "=" * 72)
    print("2. Theil T Index: Inequality in Complaint Rates")
    print("=" * 72)

    from nyc311.stats import theil_index

    # Use real ACS population for weighting
    unit_totals = df.groupby("unit_id")["complaint_count"].sum()
    unit_pop = demo["population"]

    shared_units = sorted(set(unit_totals.index) & set(unit_pop.index))
    complaint_rates = {uid: float(unit_totals[uid]) for uid in shared_units}
    populations = {uid: max(int(unit_pop[uid]), 1) for uid in shared_units}

    borough_map = {
        uid: " ".join(uid.split()[:-1]) if " " in uid else uid for uid in shared_units
    }

    theil_result = theil_index(
        values=complaint_rates,
        populations=populations,
        groups=borough_map,
    )

    print(interpret_theil(theil_result))

    # ── 3. Oaxaca-Blinder decomposition ──────────────────────────────
    print("\n" + "=" * 72)
    print("3. Oaxaca-Blinder Decomposition: Resolution Time Gap")
    print("=" * 72)

    from nyc311.stats import oaxaca_blinder_decomposition

    # Collapse to unit-level means
    agg_cols = {
        "median_resolution_days": ("median_resolution_days", "mean"),
        "log_complaints": ("log_complaints", "mean"),
        "pct_nonwhite": ("pct_nonwhite", "first"),
        "pct_renter": ("pct_renter", "first"),
        "log_median_income": ("log_median_income", "first"),
    }

    unit_means = df.reset_index().groupby("unit_id").agg(**agg_cols).dropna()

    # Split into high-income vs. low-income districts using real ACS data
    print("   Grouping: high-income vs. low-income districts (ACS 2022)")
    income_median = unit_means["log_median_income"].median()
    group_a = unit_means[unit_means["log_median_income"] < income_median]
    group_b = unit_means[unit_means["log_median_income"] >= income_median]
    regressors = ("log_complaints", "pct_nonwhite", "pct_renter")

    if len(group_a) >= 2 and len(group_b) >= 2:
        ob_result = oaxaca_blinder_decomposition(
            group_a=group_a,
            group_b=group_b,
            outcome="median_resolution_days",
            regressors=regressors,
        )
        print(interpret_oaxaca_blinder(ob_result))
    else:
        print("Insufficient groups for decomposition (need >= 2 per group).")

    # ── 4. Equity Gap Factor ─────────────────────────────────────────
    print("\n" + "=" * 72)
    print("4. Equity Gap Factor (per-district)")
    print("=" * 72)

    citywide_median = df["median_resolution_days"].median()
    if pd.notna(citywide_median) and citywide_median > 0:
        unit_res = df.groupby("unit_id")["median_resolution_days"].median().dropna()
        equity_gap = (unit_res / citywide_median).sort_values(ascending=False)

        print(f"  City-wide median resolution: {citywide_median:.2f} days")
        print("\n  Top 5 slowest-resolving districts (EGF > 1.0 = slower than city):")
        for uid, egf in equity_gap.head(5).items():
            print(f"    {uid}: EGF = {egf:.3f}")
        print("\n  Top 5 fastest-resolving districts (EGF < 1.0 = faster than city):")
        for uid, egf in equity_gap.tail(5).items():
            print(f"    {uid}: EGF = {egf:.3f}")

        egf_path = figures_dir / "equity_gap_factors.csv"
        equity_gap.to_frame("equity_gap_factor").to_csv(egf_path)
        print(f"\n  Equity gap factors saved: {egf_path}")
    else:
        print("  No valid resolution data for equity gap calculation.")


if __name__ == "__main__":
    main()
