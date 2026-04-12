#!/usr/bin/env python3
"""Step 4: Two-way fixed effects regression for resolution equity.

Tests whether community district demographics predict median resolution
time after controlling for complaint volume, type concentration, and
district + time fixed effects (Wooldridge, 2010).

**Hypothesis**: Demographic characteristics should not predict resolution
time after controlling for complaint volume and type.  Significant
coefficients on income or racial composition indicators would suggest
systemic inequity in 311 service delivery.
"""

from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    panel_path = Path(__file__).parent / "data" / "panel.parquet"
    if not panel_path.exists():
        print("Panel not found. Run 02_build_panel.py first.")
        return

    df = pd.read_parquet(panel_path)

    # --- Feature engineering ------------------------------------------------
    # For demonstration, generate synthetic demographic covariates.
    # In production, these would come from ACS 5-year estimates joined to
    # community districts.
    rng = np.random.default_rng(42)
    units = df.index.get_level_values("unit_id").unique()
    demo = pd.DataFrame(
        {
            "pct_nonwhite": rng.uniform(0.2, 0.9, len(units)),
            "log_median_income": rng.normal(10.8, 0.4, len(units)),
            "pct_renter": rng.uniform(0.3, 0.8, len(units)),
        },
        index=units,
    )
    demo.index.name = "unit_id"

    df = df.join(demo, on="unit_id")
    df["log_complaints"] = np.log1p(df["complaint_count"])

    # --- Fixed effects regression -------------------------------------------
    try:
        from linearmodels.panel import PanelOLS
    except ImportError:
        print("linearmodels not installed. Run: pip install nyc311[stats]")
        return

    if df["median_resolution_days"].isna().all():
        print("No resolution data available; skipping regression.")
        return

    y = df["median_resolution_days"].dropna()
    x_cols = ["log_complaints", "pct_nonwhite", "log_median_income", "pct_renter"]
    x = df.loc[y.index, x_cols]

    model = PanelOLS(y, x, entity_effects=True, time_effects=True)
    result = model.fit(cov_type="clustered", cluster_entity=True)

    print("=" * 72)
    print("Two-Way Fixed Effects: Median Resolution Days")
    print("  Entity FE: community district | Time FE: month")
    print("  Clustered SE: district level")
    print("=" * 72)
    print(result.summary)

    # --- Coefficient table --------------------------------------------------
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
        lambda p: "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else ""))
    )
    coef_path = figures_dir / "equity_coefficients.csv"
    coef_df.to_csv(coef_path)
    print(f"\nCoefficient table saved: {coef_path}")


if __name__ == "__main__":
    main()
