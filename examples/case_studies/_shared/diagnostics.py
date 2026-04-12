"""Shared diagnostic interpretation helpers for case studies.

Converts frozen result dataclasses from ``nyc311.stats`` into
publication-quality diagnostic paragraphs with formal statistical
language (e.g. "fails to reject the null hypothesis").
"""

from __future__ import annotations

import math
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nyc311.stats import (
        ChangepointResult,
        EventStudyResult,
        ITSResult,
        LatentReportingResult,
        MoranResult,
        OaxacaBlinderResult,
        PanelRegressionResult,
        PowerResult,
        RDResult,
        ReportingAdjustmentResult,
        STLAnomalyResult,
        StaggeredDiDResult,
        SyntheticControlResult,
        TheilResult,
    )

# ── Core formatting ──────────────────────────────────────────────────


def format_p_value(p: float, alpha: float = 0.05) -> str:
    """Format a p-value with significance stars."""
    if p is None or math.isnan(p):
        return "p = N/A"
    if p < 0.001:
        return "p < 0.001 (***)"
    if p < 0.01:
        return f"p = {p:.4f} (**)"
    if p < 0.05:
        return f"p = {p:.4f} (*)"
    if p < 0.10:
        return f"p = {p:.3f} (+)"
    return f"p = {p:.3f}"


def _significance_level(p: float) -> str:
    if p < 0.001:
        return "the 0.1% level"
    if p < 0.01:
        return "the 1% level"
    if p < 0.05:
        return "the 5% level"
    if p < 0.10:
        return "the 10% level"
    return ""


def interpret_significance(
    p: float,
    alpha: float = 0.05,
    context: str = "",
) -> str:
    """Return a full sentence interpreting a p-value against alpha."""
    if p is None or math.isnan(p):
        return "Significance cannot be assessed (p-value unavailable)."

    ctx = f" for {context}" if context else ""
    p_str = format_p_value(p, alpha)

    if p < alpha:
        level = _significance_level(p)
        return (
            f"The result is statistically significant at {level} "
            f"({p_str}), providing strong evidence to reject the null "
            f"hypothesis{ctx}."
        )
    if p < 0.10:
        return (
            f"The result is marginally significant ({p_str}), providing "
            f"weak evidence against the null hypothesis{ctx}. "
            f"This fails to reach conventional significance at "
            f"alpha = {alpha}."
        )
    return (
        f"The test fails to reject the null hypothesis at "
        f"alpha = {alpha} ({p_str}), suggesting insufficient "
        f"evidence{ctx}."
    )


def format_ci(
    estimate: float,
    lower: float,
    upper: float,
    label: str = "estimate",
    level: float = 0.95,
) -> str:
    """Format a point estimate with its confidence interval."""
    pct = int(level * 100)
    return f"The {label} is {estimate:+.2f} ({pct}% CI: [{lower:+.2f}, {upper:+.2f}])."


def interpret_treatment_effect(
    estimate: float,
    se: float,
    p: float,
    units: str = "complaints",
) -> str:
    """Interpret a treatment effect estimate in plain language."""
    direction = "reduction" if estimate < 0 else "increase"
    magnitude = abs(estimate)
    sig = interpret_significance(p, context="the treatment effect")
    return (
        f"The treatment is associated with a {direction} of "
        f"{magnitude:.1f} {units} (SE = {se:.2f}, {format_p_value(p)}). "
        f"{sig}"
    )


# ── Result-type interpreters ─────────────────────────────────────────


def interpret_synthetic_control(result: SyntheticControlResult) -> str:
    """Interpret a synthetic control result."""
    n_donors = len(result.donor_weights)
    top_donor = max(result.donor_weights, key=result.donor_weights.get)
    top_weight = result.donor_weights[top_donor]

    lines = [
        f"**Synthetic Control Method** (treated unit: {result.treated_unit})",
        "",
        interpret_treatment_effect(result.att, 0.0, 0.0, "complaints").replace(
            " (SE = 0.00, p < 0.001 (***)). The result is statistically "
            "significant at the 0.1% level (p < 0.001 (***)), providing "
            "strong evidence to reject the null hypothesis for the "
            "treatment effect.",
            ".",
        ),
        f"The synthetic control is constructed from {n_donors} donor "
        f"unit(s), with {top_donor} contributing the largest weight "
        f"({top_weight:.1%}).",
        f"Pre-treatment fit: MSPE = {result.pre_treatment_mspe:.4f}. "
        f"{'Lower values indicate a closer match between the treated unit and its synthetic counterpart in the pre-treatment period.' if result.pre_treatment_mspe < 10 else 'The relatively high MSPE suggests the synthetic match may be imperfect; interpret the ATT with caution.'}",
    ]
    if result.placebo_p_value is not None:
        lines.append(
            f"Placebo inference: {interpret_significance(result.placebo_p_value, context='the placebo test')}"
        )
    lines.append(
        f"\nAverage Treatment Effect on the Treated (ATT): "
        f"**{result.att:+.2f}** complaints per period."
    )
    return "\n".join(lines)


def interpret_staggered_did(result: StaggeredDiDResult) -> str:
    """Interpret a staggered difference-in-differences result."""
    ci = format_ci(
        result.aggregated_att,
        result.aggregated_ci_lower,
        result.aggregated_ci_upper,
        label="aggregated ATT",
    )
    sig = interpret_significance(
        result.aggregated_p_value,
        context="the average treatment effect",
    )
    return (
        f"**Staggered Difference-in-Differences** "
        f"(Callaway & Sant'Anna 2021)\n\n"
        f"Estimated {result.n_groups} treatment cohort(s) across "
        f"{result.n_periods} time periods, yielding "
        f"{len(result.group_time_atts)} group-time ATT estimates "
        f"aggregated via inverse-variance weighting.\n\n"
        f"{ci}\n\n"
        f"{sig}"
    )


def interpret_event_study(result: EventStudyResult) -> str:
    """Interpret event-study coefficients and pre-trend diagnostics."""
    n_pre = sum(1 for r in result.relative_periods if r < 0)
    n_post = sum(1 for r in result.relative_periods if r > 0)

    lines = [
        f"**Event Study** (reference period: t = {result.reference_period})",
        "",
        f"Estimated {n_pre} pre-treatment and {n_post} post-treatment "
        f"relative-period coefficients.",
    ]

    if result.pre_trend_p_value is not None:
        p = result.pre_trend_p_value
        f_str = (
            f"F = {result.pre_trend_f_statistic:.3f}, "
            if result.pre_trend_f_statistic is not None
            else ""
        )
        if p >= 0.05:
            lines.append(
                f"\n**Pre-trend test**: The joint F-test of pre-treatment "
                f"coefficients fails to reject the null hypothesis of "
                f"parallel pre-trends ({f_str}{format_p_value(p)}). "
                f"This supports the identifying assumption of the "
                f"difference-in-differences design."
            )
        elif p >= 0.01:
            lines.append(
                f"\n**Pre-trend test**: The joint F-test rejects the null "
                f"hypothesis of parallel pre-trends at the 5% level "
                f"({f_str}{format_p_value(p)}). "
                f"This raises concerns about the validity of the parallel "
                f"trends assumption; causal estimates should be "
                f"interpreted with caution."
            )
        else:
            lines.append(
                f"\n**Pre-trend test**: The joint F-test strongly rejects "
                f"parallel pre-trends ({f_str}{format_p_value(p)}). "
                f"The parallel trends assumption appears violated; "
                f"difference-in-differences estimates may be biased."
            )

    # Summarize post-treatment dynamics
    post_coeffs = [
        c
        for c, r in zip(result.coefficients, result.relative_periods, strict=True)
        if r > 0
    ]
    if post_coeffs:
        direction = "negative" if sum(post_coeffs) < 0 else "positive"
        lines.append(
            f"\nPost-treatment coefficients are predominantly {direction}, "
            f"ranging from {min(post_coeffs):+.2f} to "
            f"{max(post_coeffs):+.2f}."
        )

    return "\n".join(lines)


def interpret_rdd(result: RDResult) -> str:
    """Interpret a regression discontinuity result."""
    ci = format_ci(
        result.treatment_effect,
        result.ci_lower,
        result.ci_upper,
        label="RD treatment effect",
    )
    sig = interpret_significance(result.p_value, context="the discontinuity")
    return (
        f"**Regression Discontinuity Design** "
        f"(kernel: {result.kernel})\n\n"
        f"{ci}\n\n"
        f"Bandwidth: [{result.bandwidth_left:.3f}, "
        f"{result.bandwidth_right:.3f}]; effective sample: "
        f"{result.n_effective_left} obs. (left) and "
        f"{result.n_effective_right} obs. (right).\n\n"
        f"{sig}"
    )


def interpret_its(result: ITSResult) -> str:
    """Interpret an interrupted time series result."""
    level_sig = interpret_significance(
        result.p_value_level,
        context="the level change at the intervention",
    )
    trend_sig = interpret_significance(
        result.p_value_trend,
        context="the change in trend slope",
    )
    return (
        f"**Interrupted Time Series** (segmented regression)\n\n"
        f"Pre-intervention trend: {result.pre_trend:+.2f} per period. "
        f"Post-intervention trend: {result.post_trend:+.2f} per period.\n\n"
        f"**Level change** at intervention: {result.level_change:+.2f}. "
        f"{level_sig}\n\n"
        f"**Trend change**: {result.trend_change:+.2f}. "
        f"{trend_sig}"
    )


def interpret_moran(result: MoranResult) -> str:
    """Interpret Global Moran's I result."""
    sig = interpret_significance(
        result.p_value,
        context="spatial autocorrelation",
    )
    if result.p_value < 0.05:
        if result.statistic > 0:
            pattern = (
                "indicating positive spatial autocorrelation: "
                "similar values tend to cluster together geographically"
            )
        else:
            pattern = (
                "indicating negative spatial autocorrelation: "
                "dissimilar values tend to be adjacent"
            )
    else:
        pattern = "the observed spatial pattern is consistent with spatial randomness"

    return (
        f"**Global Moran's I**: I = {result.statistic:.4f} "
        f"(z = {result.z_score:.3f}, {format_p_value(result.p_value)}), "
        f"{pattern}. {sig}"
    )


def interpret_changepoints(
    result: ChangepointResult,
    known_events: dict[str, date] | None = None,
) -> str:
    """Interpret changepoint detection results."""
    n = len(result.breakpoints)
    lines = [
        f"**Changepoint Detection** (penalty = {result.penalty:.2f})",
        "",
        f"Detected {n} structural break(s) dividing the series into "
        f"{result.n_segments} segment(s).",
    ]
    if n > 0 and result.breakpoint_dates:
        for bp_date in result.breakpoint_dates:
            annotation = ""
            if known_events:
                nearest = None
                min_delta = 120
                for name, ev_date in known_events.items():
                    delta = abs((bp_date - ev_date).days)
                    if delta < min_delta:
                        min_delta = delta
                        nearest = name
                if nearest:
                    annotation = f" -- near {nearest} ({min_delta} days)"
            lines.append(f"  - {bp_date.isoformat()}{annotation}")
    elif n == 0:
        lines.append("No structural breaks detected at the chosen penalty level.")
    return "\n".join(lines)


def interpret_stl_anomalies(result: STLAnomalyResult) -> str:
    """Interpret STL-residual anomaly detection results."""
    if result.n_anomalies == 0:
        return (
            f"**STL Anomaly Detection** (threshold: {result.threshold} "
            f"sigma)\n\nNo anomalous observations detected. All residuals "
            f"fall within {result.threshold} standard deviations of the "
            f"mean (residual std = {result.residual_std:.2f})."
        )
    dates_str = ", ".join(str(d)[:10] for d in result.anomaly_dates[:10])
    scores_str = ", ".join(f"{s:+.2f}" for s in result.anomaly_scores[:10])
    more = (
        f" (showing first 10 of {result.n_anomalies})"
        if result.n_anomalies > 10
        else ""
    )
    return (
        f"**STL Anomaly Detection** (threshold: {result.threshold} "
        f"sigma)\n\n"
        f"Detected **{result.n_anomalies}** anomalous observation(s){more} "
        f"with |z-score| > {result.threshold} "
        f"(residual mean = {result.residual_mean:.2f}, "
        f"residual std = {result.residual_std:.2f}).\n\n"
        f"Anomaly dates: {dates_str}\n"
        f"Z-scores: {scores_str}"
    )


def interpret_theil(result: TheilResult) -> str:
    """Interpret a Theil T index result."""
    lines = [
        f"**Theil T Index** (N = {result.n_units} units)",
        "",
        f"Total inequality: T = {result.total:.4f}.",
    ]
    if result.between_group > 0 or result.within_group > 0:
        total_nz = max(result.total, 1e-10)
        btwn_pct = result.between_group / total_nz * 100
        with_pct = result.within_group / total_nz * 100
        lines.append(
            f"Between-group component: {result.between_group:.4f} "
            f"({btwn_pct:.1f}% of total). "
            f"Within-group component: {result.within_group:.4f} "
            f"({with_pct:.1f}% of total)."
        )
        if btwn_pct > 50:
            lines.append(
                "The majority of inequality is attributable to "
                "differences *between* groups rather than within them."
            )
        else:
            lines.append(
                "The majority of inequality is attributable to "
                "differences *within* groups."
            )
    # Top contributors
    sorted_contrib = sorted(
        result.unit_contributions.items(), key=lambda x: abs(x[1]), reverse=True
    )[:5]
    if sorted_contrib:
        top_str = ", ".join(f"{uid} ({v:+.4f})" for uid, v in sorted_contrib)
        lines.append(f"\nLargest contributors: {top_str}")
    return "\n".join(lines)


def interpret_oaxaca_blinder(result: OaxacaBlinderResult) -> str:
    """Interpret an Oaxaca-Blinder decomposition result."""
    total_nz = max(abs(result.total_gap), 1e-10)
    expl_pct = result.explained / total_nz * 100
    unex_pct = result.unexplained / total_nz * 100

    lines = [
        f"**Oaxaca-Blinder Decomposition** "
        f"(N_A = {result.n_group_a}, N_B = {result.n_group_b})",
        "",
        f"Group A mean: {result.mean_group_a:.2f}. "
        f"Group B mean: {result.mean_group_b:.2f}. "
        f"Total gap: {result.total_gap:+.2f}.",
        "",
        f"Explained (covariate differences): {result.explained:+.2f} "
        f"({expl_pct:.1f}% of gap).",
        f"Unexplained (coefficient differences): "
        f"{result.unexplained:+.2f} ({unex_pct:.1f}% of gap).",
    ]
    if abs(unex_pct) > 50:
        lines.append(
            "\nThe unexplained component dominates, suggesting that "
            "differences in observable characteristics alone do not "
            "account for the outcome gap. This residual may reflect "
            "structural or institutional factors."
        )
    else:
        lines.append(
            "\nMost of the gap is explained by differences in "
            "observable characteristics between the two groups."
        )

    if result.component_contributions:
        sorted_comp = sorted(
            result.component_contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True,
        )
        comp_str = ", ".join(f"{k} ({v:+.3f})" for k, v in sorted_comp[:5])
        lines.append(f"\nVariable contributions (explained): {comp_str}")
    return "\n".join(lines)


def interpret_panel_regression(result: PanelRegressionResult) -> str:
    """Interpret a panel regression result."""
    method_label = {
        "entity_fe": "Entity Fixed Effects",
        "two_way_fe": "Two-Way Fixed Effects (entity + time)",
        "random_effects": "Random Effects (GLS)",
    }.get(result.method, result.method)

    lines = [
        f"**Panel Regression: {method_label}** "
        f"(N = {result.n_observations}, "
        f"{result.n_entities} entities, "
        f"{result.n_periods} periods, "
        f"R-sq = {result.r_squared:.4f})",
        "",
        "| Variable | Coeff | SE | p-value | Sig |",
        "|----------|------:|---:|--------:|:---:|",
    ]
    for var in result.coefficients:
        coeff = result.coefficients[var]
        se = result.std_errors.get(var, 0.0)
        pv = result.p_values.get(var, 1.0)
        sig = "***" if pv < 0.001 else "**" if pv < 0.01 else "*" if pv < 0.05 else ""
        lines.append(f"| {var} | {coeff:+.4f} | {se:.4f} | {pv:.4f} | {sig} |")

    sig_vars = [v for v, p in result.p_values.items() if p < 0.05]
    if sig_vars:
        lines.append(
            f"\nStatistically significant predictors (alpha = 0.05): "
            f"{', '.join(sig_vars)}."
        )
    else:
        lines.append("\nNo predictors are statistically significant at the 5% level.")
    return "\n".join(lines)


def interpret_power(result: PowerResult) -> str:
    """Interpret a power analysis / MDE result."""
    return (
        f"**Power Analysis** (MDE Calculator)\n\n"
        f"Design: {result.n_units} units, {result.n_periods} periods, "
        f"ICC = {result.icc}, alpha = {result.alpha}, "
        f"power = {result.power:.0%}.\n\n"
        f"**Minimum Detectable Effect: {result.mde:.2f}** "
        f"(in outcome units).\n\n"
        f"Any true treatment effect smaller than {result.mde:.2f} would "
        f"have less than {result.power:.0%} probability of being detected "
        f"as statistically significant at alpha = {result.alpha} "
        f"with this design. Increasing the number of units or periods "
        f"would lower the MDE."
    )


def interpret_reporting_bias(
    adj_result: ReportingAdjustmentResult | None = None,
    em_result: LatentReportingResult | None = None,
) -> str:
    """Interpret reporting bias correction results."""
    lines = ["**Reporting Bias Assessment**", ""]

    if adj_result is not None:
        lines.append(
            f"*Ecometric adjustment* (mixed-effects model with "
            f"{len(adj_result.covariates_used)} covariate(s)): "
            f"ICC = {adj_result.icc:.4f}."
        )
        if adj_result.icc > 0.10:
            lines.append(
                f"An ICC of {adj_result.icc:.3f} indicates substantial "
                f"unit-level variation in reporting propensity that "
                f"persists after controlling for demographics."
            )
        else:
            lines.append(
                f"An ICC of {adj_result.icc:.3f} suggests modest "
                f"unit-level variation in reporting propensity."
            )
        # Top 5 adjustments
        sorted_adj = sorted(
            adj_result.adjustment_factors.items(),
            key=lambda x: abs(x[1]),
            reverse=True,
        )[:5]
        adj_str = ", ".join(f"{uid} ({v:+.2f})" for uid, v in sorted_adj)
        lines.append(f"Largest random intercepts: {adj_str}")

    if em_result is not None:
        lines.append("")
        conv = "converged" if em_result.converged else "did not converge"
        lines.append(
            f"*Latent EM estimation*: {conv} after "
            f"{em_result.n_iterations} iteration(s)."
        )
        rho_vals = list(em_result.reporting_probabilities.values())
        lines.append(
            f"Estimated reporting probabilities range from "
            f"{min(rho_vals):.3f} to {max(rho_vals):.3f} "
            f"(mean = {sum(rho_vals) / len(rho_vals):.3f})."
        )
        if not em_result.converged:
            lines.append(
                "WARNING: EM algorithm did not converge. Increase "
                "max_iter or check for model misspecification."
            )

    return "\n".join(lines)


# ── Report compilation ───────────────────────────────────────────────


def compile_findings_md(
    title: str,
    date_str: str,
    toolkit_version: str,
    sections: list[tuple[str, str]],
) -> str:
    """Compile a full FINDINGS.md from section (title, body) pairs."""
    lines = [
        f"# {title}",
        "",
        f"*Generated on {date_str} using nyc311 {toolkit_version}.*",
        "",
        "---",
        "",
    ]
    for section_title, section_body in sections:
        lines.append(f"## {section_title}")
        lines.append("")
        lines.append(section_body)
        lines.append("")
    return "\n".join(lines)
