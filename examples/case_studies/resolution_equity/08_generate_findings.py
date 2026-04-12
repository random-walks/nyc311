#!/usr/bin/env python3
"""Step 8: Compile analysis results into FINDINGS.md.

Reads the panel parquet and CSV outputs from prior steps directly,
re-running key computations to capture accurate metrics for the
findings document.  This avoids stale JSON intermediaries.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared.diagnostics import (
    compile_findings_md,
    format_p_value,
    interpret_moran,
    interpret_stl_anomalies,
    interpret_theil,
)

DATA_DIR = Path(__file__).parent / "data"
FIGURES_DIR = Path(__file__).parent / "figures"
FINDINGS_PATH = Path(__file__).parent / "FINDINGS.md"
DEMOGRAPHICS_PATH = DATA_DIR / "demographics.csv"


def main() -> None:
    panel_path = DATA_DIR / "panel.parquet"
    if not panel_path.exists():
        print("Panel not found. Run the pipeline first.")
        return

    df = pd.read_parquet(panel_path)
    sections: list[tuple[str, str]] = []

    # Count records from cached CSVs
    cache_dir = DATA_DIR / "cache"
    n_records = 0
    if cache_dir.exists():
        from nyc311.io import load_service_requests

        for csv_path in sorted(cache_dir.glob("*.csv")):
            n_records += len(load_service_requests(csv_path))

    n_units = df.index.get_level_values("unit_id").nunique()
    n_periods = df.index.get_level_values("period").nunique()
    periods = sorted(df.index.get_level_values("period").unique())

    # ── Data Summary ─────────────────────────────────────────────────
    sections.append(
        (
            "Data Summary",
            f"The analysis examines **{n_records:,} NYC 311 service requests** "
            f"covering {periods[0]} to {periods[-1]}. "
            f"The balanced panel contains **{n_units} community districts** "
            f"observed over **{n_periods} monthly periods** "
            f"({len(df):,} total observations).\n\n"
            f"Mean monthly complaints per district: "
            f"{df['complaint_count'].mean():.1f} "
            f"(median: {df['complaint_count'].median():.1f}). "
            f"Mean resolution rate: "
            f"{df['resolution_rate'].mean():.1%} "
            f"(SD = {df['resolution_rate'].std():.3f}).",
        )
    )

    # ── Seasonal Decomposition ───────────────────────────────────────
    from nyc311.stats import detect_stl_anomalies, seasonal_decompose

    city_monthly = df.groupby("period")["complaint_count"].sum()
    city_monthly.index = pd.to_datetime(city_monthly.index)
    city_monthly = city_monthly.sort_index()

    decomp = seasonal_decompose(city_monthly, period=12)
    trend = decomp.trend.dropna()
    seasonal = decomp.seasonal.dropna()
    monthly_seasonal = seasonal.groupby(seasonal.index.month).mean()
    month_names = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December",
    }
    peak = month_names[int(monthly_seasonal.idxmax())]
    trough = month_names[int(monthly_seasonal.idxmin())]
    amplitude = seasonal.max() - seasonal.min()

    anomalies = detect_stl_anomalies(city_monthly, threshold=2.0)

    sections.append(
        (
            "Seasonal Decomposition and Anomalies",
            f"STL decomposition reveals complaints peak in **{peak}** and "
            f"trough in **{trough}**, with a seasonal amplitude of "
            f"**{amplitude:,.0f}** complaints. "
            f"The trend moved from {trend.iloc[0]:,.0f} to "
            f"{trend.iloc[-1]:,.0f} over the study period.\n\n"
            f"{interpret_stl_anomalies(anomalies)}",
        )
    )

    # ── Equity Analysis ──────────────────────────────────────────────
    try:
        from linearmodels.panel import PanelOLS

        df_eq = df.copy()
        df_eq["log_complaints"] = np.log1p(df_eq["complaint_count"])

        # Ensure datetime index
        if isinstance(df_eq.index, pd.MultiIndex):
            period_level = df_eq.index.get_level_values(1)
            if not isinstance(period_level, pd.DatetimeIndex):
                unit_level = df_eq.index.get_level_values(0)
                period_level = pd.DatetimeIndex(pd.to_datetime(list(period_level)))
                df_eq.index = pd.MultiIndex.from_arrays(
                    [unit_level, period_level], names=df_eq.index.names
                )

        y = df_eq["median_resolution_days"].dropna()
        x = df_eq.loc[y.index, ["log_complaints"]]
        model = PanelOLS(y, x, entity_effects=True, time_effects=True)
        result = model.fit(cov_type="clustered", cluster_entity=True)

        r2 = float(result.rsquared)
        coef_lines = []
        sig_vars = []
        for var in result.params.index:
            c = float(result.params[var])
            se = float(result.std_errors[var])
            pv = float(result.pvalues[var])
            coef_lines.append(
                f"  - **{var}**: coeff = {c:+.4f}, SE = {se:.4f}, {format_p_value(pv)}"
            )
            if pv < 0.05:
                sig_vars.append(str(var))

        equity_text = (
            f"Two-way fixed effects panel regression with entity and time "
            f"fixed effects, clustered SE at the district level "
            f"(N = {int(result.nobs)}, R-sq = **{r2:.4f}**).\n\n"
            + "\n".join(coef_lines)
        )
        if sig_vars:
            equity_text += (
                f"\n\nHigher complaint volume significantly predicts longer "
                f"resolution times. A 1-unit increase in log complaints is "
                f"associated with {float(result.params.iloc[0]):+.1f} additional "
                f"days of median resolution time."
            )
    except Exception as exc:
        equity_text = f"Panel regression could not be estimated: {exc}"

    # Add Theil + Oaxaca-Blinder if demographics available
    if DEMOGRAPHICS_PATH.exists():
        from nyc311.stats import oaxaca_blinder_decomposition, theil_index

        demo = pd.read_csv(DEMOGRAPHICS_PATH, index_col="unit_id")
        units_in_both = sorted(
            set(df.index.get_level_values("unit_id").unique()) & set(demo.index)
        )

        # Theil
        unit_totals = df.groupby("unit_id")["complaint_count"].sum()
        populations = {
            uid: int(demo.loc[uid, "population"])
            for uid in units_in_both
            if uid in unit_totals.index
        }
        values = {uid: float(unit_totals[uid]) for uid in populations}
        borough_map = {uid: " ".join(uid.split()[:-1]) for uid in populations}
        theil_result = theil_index(
            values=values, populations=populations, groups=borough_map
        )
        equity_text += f"\n\n{interpret_theil(theil_result)}"

        # Oaxaca-Blinder
        df_ob = df.copy()
        df_ob["log_complaints"] = np.log1p(df_ob["complaint_count"])
        df_ob = df_ob.join(
            demo[["pct_nonwhite", "log_median_income", "pct_renter"]], on="unit_id"
        )
        unit_means = (
            df_ob.reset_index()
            .groupby("unit_id")
            .agg(
                median_resolution_days=("median_resolution_days", "mean"),
                log_complaints=("log_complaints", "mean"),
                pct_nonwhite=("pct_nonwhite", "first"),
                pct_renter=("pct_renter", "first"),
                log_median_income=("log_median_income", "first"),
            )
            .dropna()
        )
        med_inc = unit_means["log_median_income"].median()
        low = unit_means[unit_means["log_median_income"] < med_inc]
        high = unit_means[unit_means["log_median_income"] >= med_inc]
        if len(low) >= 2 and len(high) >= 2:
            ob = oaxaca_blinder_decomposition(
                low,
                high,
                "median_resolution_days",
                ("log_complaints", "pct_nonwhite", "pct_renter"),
            )
            total_nz = max(abs(ob.total_gap), 1e-10)
            equity_text += (
                f"\n\n**Oaxaca-Blinder decomposition** (low- vs. high-income "
                f"districts): total gap = {ob.total_gap:+.2f} days. "
                f"Explained = {ob.explained:+.2f} "
                f"({ob.explained / total_nz * 100:.0f}%), "
                f"Unexplained = {ob.unexplained:+.2f} "
                f"({ob.unexplained / total_nz * 100:.0f}%)."
            )

    sections.append(("Equity Analysis", equity_text))

    # ── Spatial Analysis ─────────────────────────────────────────────
    try:
        from nyc311.geographies import load_nyc_boundaries
        from nyc311.stats import global_morans_i, local_morans_i
        from nyc311.temporal import build_distance_weights, centroids_from_boundaries

        mean_res = (
            df.groupby("unit_id")["median_resolution_days"].mean().dropna().to_dict()
        )
        boundaries = load_nyc_boundaries("community_district")
        centroids = centroids_from_boundaries(boundaries)
        shared = sorted(set(mean_res) & set(centroids))
        mean_res_shared = {k: mean_res[k] for k in shared}
        centroids_shared = {k: centroids[k] for k in shared}
        weights = build_distance_weights(centroids_shared, threshold_meters=3000.0)

        moran = global_morans_i(mean_res_shared, weights)
        lisa = local_morans_i(mean_res_shared, weights)
        cluster_counts: dict[str, int] = {}
        for label in lisa.cluster_labels:
            cluster_counts[label] = cluster_counts.get(label, 0) + 1

        lisa_str = "; ".join(f"{k}: {v}" for k, v in sorted(cluster_counts.items()))
        spatial_text = (
            f"{interpret_moran(moran)}\n\nLISA cluster distribution: {lisa_str}."
        )
    except Exception as exc:
        spatial_text = f"Spatial analysis could not be completed: {exc}"

    sections.append(("Spatial Analysis", spatial_text))

    # ── Policy Evaluation ────────────────────────────────────────────
    from nyc311.stats import detect_changepoints, interrupted_time_series

    cp = detect_changepoints(city_monthly, method="pelt")
    bp_text = (
        "\n".join(f"  - {d.isoformat()}" for d in cp.breakpoint_dates) or "  (none)"
    )

    its = interrupted_time_series(city_monthly, intervention_date=date(2024, 3, 1))

    sections.append(
        (
            "Policy Evaluation",
            f"**Changepoint detection** (PELT): {len(cp.breakpoints)} "
            f"break(s) dividing the series into {cp.n_segments} segment(s).\n"
            f"{bp_text}\n\n"
            f"**Interrupted time series** (intervention: March 2024 rat mandate):\n"
            f"  - Pre-intervention trend: {its.pre_trend:+.1f}/period\n"
            f"  - Level change: {its.level_change:+,.0f} ({format_p_value(its.p_value_level)})\n"
            f"  - Trend change: {its.trend_change:+,.0f} ({format_p_value(its.p_value_trend)})\n"
            f"  - Post-intervention trend: {its.post_trend:+,.0f}/period",
        )
    )

    # ── Reporting Bias ───────────────────────────────────────────────
    try:
        from nyc311.stats import latent_reporting_bias_em

        unit_totals = df.groupby("unit_id")["complaint_count"].sum()
        unit_pop = df.groupby("unit_id").size()  # obs count as proxy
        shared_units = sorted(set(unit_totals.index) & set(unit_pop.index))
        counts = {uid: int(unit_totals[uid]) for uid in shared_units}
        pops = {uid: max(int(unit_pop[uid]), 1) for uid in shared_units}

        covs = None
        if DEMOGRAPHICS_PATH.exists():
            demo = pd.read_csv(DEMOGRAPHICS_PATH, index_col="unit_id")
            shared_demo = sorted(set(shared_units) & set(demo.index))
            if shared_demo:
                counts = {uid: counts[uid] for uid in shared_demo}
                pops = {uid: int(demo.loc[uid, "population"]) for uid in shared_demo}
                covs = {
                    uid: {
                        c: float(demo.loc[uid, c])
                        for c in ["pct_nonwhite", "log_median_income", "pct_renter"]
                    }
                    for uid in shared_demo
                }

        em = latent_reporting_bias_em(counts, pops, covs)
        rho_vals = list(em.reporting_probabilities.values())
        conv = "converged" if em.converged else "did not converge"
        reporting_text = (
            f"Latent EM {conv} after {em.n_iterations} iterations. "
            f"Reporting probabilities: {min(rho_vals):.3f} -- "
            f"{max(rho_vals):.3f} (mean = {sum(rho_vals) / len(rho_vals):.3f})."
        )
        if max(rho_vals) - min(rho_vals) < 0.01:
            reporting_text += (
                "\n\nThe near-uniform reporting probabilities suggest the "
                "model cannot distinguish reporting heterogeneity with the "
                "available covariates. More granular data (per complaint "
                "type, with additional covariates) would be needed."
            )
    except Exception as exc:
        reporting_text = f"Reporting bias estimation failed: {exc}"

    sections.append(("Reporting Bias", reporting_text))

    # ── Limitations ──────────────────────────────────────────────────
    sections.append(
        (
            "Limitations",
            "- Demographic covariates are from ACS 2022 PUMA-level estimates "
            "mapped to community districts. Some CDs share PUMAs and thus "
            "have identical demographic values.\n"
            "- The reporting bias EM model assumes a Poisson-logistic "
            "structure that may not hold for all complaint types.\n"
            "- Spatial weights use a 3 km distance threshold; results are "
            "sensitive to this choice.\n"
            "- Clustered standard errors with ~70 clusters may under-reject; "
            "wild bootstrap inference is recommended for robustness.",
        )
    )

    # ── References ───────────────────────────────────────────────────
    sections.append(
        (
            "References",
            "- Cleveland et al. (1990). STL decomposition. *J. Official Statistics*.\n"
            "- Killick et al. (2012). PELT changepoint detection. *JASA*.\n"
            "- O'Brien et al. (2015). Ecometrics. *Sociological Methodology*.\n"
            "- Rey & Anselin (2007). PySAL. *Review of Regional Studies*.\n"
            "- Theil (1967). *Economics and Information Theory*.\n"
            "- Wooldridge (2010). *Econometric Analysis of Cross Section and Panel Data*.",
        )
    )

    md = compile_findings_md(
        title="Resolution Equity in NYC 311 Service Delivery: Findings",
        date_str=date.today().isoformat(),
        toolkit_version="v0.4.0",
        sections=sections,
    )

    FINDINGS_PATH.write_text(md, encoding="utf-8")
    print(f"  FINDINGS.md written to {FINDINGS_PATH}")
    print(f"  ({len(sections)} sections)")


if __name__ == "__main__":
    main()
