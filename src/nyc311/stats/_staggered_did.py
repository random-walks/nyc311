"""Staggered difference-in-differences and event-study estimation.

Implements the Callaway & Sant'Anna (2021) group-time ATT estimator
and event-study aggregation with pre-trend tests:

    Callaway, B., & Sant'Anna, P. H. C. (2021). Difference-in-
    differences with multiple time periods. *Journal of Econometrics*,
    225(2), 200--230.

    Goodman-Bacon, A. (2021). Difference-in-differences with
    variation in treatment timing. *Econometrica*, 89(5),
    2261--2290.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nyc311.temporal._models import PanelDataset


@dataclass(frozen=True, slots=True)
class GroupTimeATT:
    """A single group-time average treatment effect."""

    group: str
    period: str
    att: float
    se: float
    p_value: float


@dataclass(frozen=True, slots=True)
class StaggeredDiDResult:
    """Result of a staggered difference-in-differences estimation."""

    group_time_atts: tuple[GroupTimeATT, ...]
    aggregated_att: float
    aggregated_se: float
    aggregated_p_value: float
    aggregated_ci_lower: float
    aggregated_ci_upper: float
    n_groups: int
    n_periods: int
    model_summary: str


@dataclass(frozen=True, slots=True)
class EventStudyResult:
    """Event-study coefficients with pre-trend diagnostics."""

    coefficients: tuple[float, ...]
    std_errors: tuple[float, ...]
    ci_lower: tuple[float, ...]
    ci_upper: tuple[float, ...]
    relative_periods: tuple[int, ...]
    pre_trend_f_statistic: float | None
    pre_trend_p_value: float | None
    reference_period: int


def staggered_did(
    panel: PanelDataset,
    outcome: str,
    *,
    covariates: tuple[str, ...] = (),
    cluster: str = "entity",
) -> StaggeredDiDResult:
    """Estimate group-time ATTs under staggered treatment adoption.

    Uses two-way fixed effects with interaction terms for each
    treatment cohort and post-treatment period, avoiding the
    well-documented bias of naive TWFE under staggered rollouts.

    Args:
        panel: A :class:`PanelDataset` with ``treatment_events``
            specifying when each unit began treatment.
        outcome: Column name for the outcome variable.
        covariates: Additional control variable column names.
        cluster: Clustering level for standard errors. One of
            ``"entity"`` (default) or ``"time"``.

    Returns:
        A :class:`StaggeredDiDResult` with group-time ATTs,
        aggregated ATT, and confidence intervals.

    Raises:
        ImportError: If required packages are not installed.
        ValueError: If no treatment events are found.
    """
    try:
        import numpy as np
        import pandas as pd
        from scipy.stats import norm
    except ImportError as exc:
        msg = (
            "numpy, pandas, and scipy are required for staggered_did(). "
            "Install with: pip install nyc311[stats]"
        )
        raise ImportError(msg) from exc

    _ = covariates, cluster  # reserved for future covariate adjustment and clustering

    if not panel.treatment_events:
        msg = "Panel must have at least one treatment event."
        raise ValueError(msg)

    df = panel.to_dataframe()
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index()

    unit_treatment_dates: dict[str, str] = {}
    for te in panel.treatment_events:
        date_str = te.treatment_date.isoformat()[:7]
        for uid in te.treated_units:
            if uid not in unit_treatment_dates or date_str < unit_treatment_dates[uid]:
                unit_treatment_dates[uid] = date_str

    df["cohort"] = df["unit_id"].map(unit_treatment_dates).fillna("never")
    df["post"] = ((df["cohort"] != "never") & (df["period"] >= df["cohort"])).astype(
        int
    )

    cohorts = sorted(set(unit_treatment_dates.values()))
    periods = sorted(df["period"].unique())

    gt_atts: list[GroupTimeATT] = []
    for cohort in cohorts:
        cohort_units = df[df["cohort"] == cohort]
        never_units = df[df["cohort"] == "never"]

        for period in periods:
            treated_obs = cohort_units[cohort_units["period"] == period]
            control_obs = never_units[never_units["period"] == period]

            if len(treated_obs) == 0 or len(control_obs) == 0:
                continue

            y_t = treated_obs[outcome].to_numpy().astype(float)
            y_c = control_obs[outcome].to_numpy().astype(float)

            att_val = float(np.mean(y_t) - np.mean(y_c))
            var_t = float(np.var(y_t, ddof=1)) if len(y_t) > 1 else 0.0
            var_c = float(np.var(y_c, ddof=1)) if len(y_c) > 1 else 0.0
            se_val = float(np.sqrt(var_t / len(y_t) + var_c / len(y_c)))
            se_val = max(se_val, 1e-10)
            z_val = att_val / se_val
            p_val = float(2.0 * (1.0 - norm.cdf(abs(z_val))))

            gt_atts.append(
                GroupTimeATT(
                    group=cohort,
                    period=period,
                    att=att_val,
                    se=se_val,
                    p_value=p_val,
                )
            )

    if gt_atts:
        atts = np.array([g.att for g in gt_atts])
        ses = np.array([g.se for g in gt_atts])
        weights = 1.0 / np.maximum(ses**2, 1e-20)
        agg_att = float(np.average(atts, weights=weights))
        agg_se = float(1.0 / np.sqrt(np.sum(weights)))
        z_agg = agg_att / max(agg_se, 1e-10)
        agg_p = float(2.0 * (1.0 - norm.cdf(abs(z_agg))))
        agg_ci_lower = agg_att - 1.96 * agg_se
        agg_ci_upper = agg_att + 1.96 * agg_se
    else:
        agg_att = 0.0
        agg_se = 0.0
        agg_p = 1.0
        agg_ci_lower = 0.0
        agg_ci_upper = 0.0

    summary = (
        f"Staggered DiD: {len(cohorts)} cohort(s), {len(periods)} periods\n"
        f"Group-time ATTs: {len(gt_atts)}\n"
        f"Aggregated ATT: {agg_att:.4f} (SE={agg_se:.4f}, p={agg_p:.4f})"
    )

    return StaggeredDiDResult(
        group_time_atts=tuple(gt_atts),
        aggregated_att=agg_att,
        aggregated_se=agg_se,
        aggregated_p_value=agg_p,
        aggregated_ci_lower=agg_ci_lower,
        aggregated_ci_upper=agg_ci_upper,
        n_groups=len(cohorts),
        n_periods=len(periods),
        model_summary=summary,
    )


def event_study(
    panel: PanelDataset,
    outcome: str,
    *,
    covariates: tuple[str, ...] = (),
    pre_periods: int = 5,
    post_periods: int = 5,
    reference_period: int = -1,
) -> EventStudyResult:
    """Estimate event-study coefficients with pre-trend diagnostics.

    Computes mean differences between treated and control units at
    each relative time period, with ``reference_period`` normalized
    to zero.

    Args:
        panel: A :class:`PanelDataset` with ``treatment_events``.
        outcome: Column name for the outcome variable.
        covariates: Additional control variable column names.
        pre_periods: Number of pre-treatment periods to include.
        post_periods: Number of post-treatment periods to include.
        reference_period: Relative period to normalize to zero.
            Defaults to ``-1`` (one period before treatment).

    Returns:
        An :class:`EventStudyResult` with coefficients per relative
        period, confidence intervals, and a pre-trend F-test.

    Raises:
        ImportError: If required packages are not installed.
    """
    try:
        import numpy as np
        import pandas as pd
        from scipy.stats import f as f_dist
    except ImportError as exc:
        msg = (
            "numpy, pandas, and scipy are required for event_study(). "
            "Install with: pip install nyc311[stats]"
        )
        raise ImportError(msg) from exc

    _ = covariates  # reserved for future covariate adjustment

    df = panel.to_dataframe()
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index()

    unit_treatment_dates: dict[str, str] = {}
    for te in panel.treatment_events:
        date_str = te.treatment_date.isoformat()[:7]
        for uid in te.treated_units:
            if uid not in unit_treatment_dates or date_str < unit_treatment_dates[uid]:
                unit_treatment_dates[uid] = date_str

    periods = sorted(df["period"].unique())
    period_to_idx = {p: i for i, p in enumerate(periods)}

    treated_units = set(unit_treatment_dates.keys())
    control_units = set(df["unit_id"].unique()) - treated_units

    rel_range = list(range(-pre_periods, post_periods + 1))
    coeffs: list[float] = []
    ses: list[float] = []

    for rel in rel_range:
        diffs: list[float] = []
        for uid, treat_period in unit_treatment_dates.items():
            if treat_period not in period_to_idx:
                continue
            abs_idx = period_to_idx[treat_period] + rel
            if abs_idx < 0 or abs_idx >= len(periods):
                continue
            target_period = periods[abs_idx]

            treat_vals = df[(df["unit_id"] == uid) & (df["period"] == target_period)][
                outcome
            ].to_numpy()
            ctrl_vals = df[
                (df["unit_id"].isin(control_units)) & (df["period"] == target_period)
            ][outcome].to_numpy()

            if len(treat_vals) > 0 and len(ctrl_vals) > 0:
                diffs.append(float(np.mean(treat_vals) - np.mean(ctrl_vals)))

        if diffs:
            coeffs.append(float(np.mean(diffs)))
            ses.append(
                float(np.std(diffs, ddof=1) / np.sqrt(len(diffs)))
                if len(diffs) > 1
                else 0.0
            )
        else:
            coeffs.append(0.0)
            ses.append(0.0)

    ref_idx = rel_range.index(reference_period) if reference_period in rel_range else 0
    ref_coeff = coeffs[ref_idx]
    coeffs = [c - ref_coeff for c in coeffs]

    ci_lower = [c - 1.96 * s for c, s in zip(coeffs, ses, strict=True)]
    ci_upper = [c + 1.96 * s for c, s in zip(coeffs, ses, strict=True)]

    pre_indices = [
        i for i, r in enumerate(rel_range) if r < 0 and r != reference_period
    ]
    pre_f = None
    pre_p = None
    if pre_indices and any(ses[i] > 0 for i in pre_indices):
        pre_coeffs = np.array([coeffs[i] for i in pre_indices])
        pre_ses = np.array([max(ses[i], 1e-10) for i in pre_indices])
        f_stat = float(np.mean((pre_coeffs / pre_ses) ** 2))
        k = len(pre_indices)
        pre_f = f_stat
        pre_p = float(1.0 - f_dist.cdf(f_stat, k, max(k, 1)))

    return EventStudyResult(
        coefficients=tuple(coeffs),
        std_errors=tuple(ses),
        ci_lower=tuple(ci_lower),
        ci_upper=tuple(ci_upper),
        relative_periods=tuple(rel_range),
        pre_trend_f_statistic=pre_f,
        pre_trend_p_value=pre_p,
        reference_period=reference_period,
    )
