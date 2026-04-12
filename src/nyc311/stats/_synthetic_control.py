"""Synthetic control method for comparative case studies.

Constructs a data-driven counterfactual from donor units:

    Abadie, A., Diamond, A., & Hainmueller, J. (2010). Synthetic
    control methods for comparative case studies: Estimating the
    effect of California's Tobacco Control Program. *Journal of the
    American Statistical Association*, 105(490), 493--505.

    Abadie, A. (2021). Using synthetic controls: Feasibility,
    data requirements, and methodological aspects. *Journal of
    Economic Literature*, 59(2), 391--425.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from nyc311.temporal._models import PanelDataset


@dataclass(frozen=True, slots=True)
class SyntheticControlResult:
    """Result of a synthetic control analysis."""

    treated_unit: str
    donor_weights: dict[str, float]
    counterfactual: tuple[float, ...]
    observed: tuple[float, ...]
    treatment_effect: tuple[float, ...]
    att: float
    periods: tuple[str, ...]
    pre_treatment_mspe: float
    placebo_p_value: float | None
    model_summary: str


def synthetic_control(
    panel: PanelDataset,
    treated_unit: str,
    outcome: str,
    *,
    predictors: tuple[str, ...] = (),
    n_placebo_runs: int = 0,
) -> SyntheticControlResult:
    """Estimate a treatment effect using the synthetic control method.

    Constructs a weighted combination of untreated donor units that
    best reproduces the treated unit's pre-treatment trajectory, then
    measures the post-treatment divergence as the treatment effect.

    Args:
        panel: A :class:`PanelDataset` with treatment information.
        treated_unit: The unit ID of the treated unit.
        outcome: Column name for the outcome variable.
        predictors: Additional predictor columns for matching.
        n_placebo_runs: Number of in-space placebos for inference.
            When ``> 0``, each donor unit is iteratively treated and
            the ratio of post/pre MSPE is used to compute a p-value.
            Defaults to ``0`` (no placebos).

    Returns:
        A :class:`SyntheticControlResult` with donor weights,
        counterfactual series, treatment effects, and optionally a
        placebo p-value.

    Raises:
        ImportError: If pysyncon is not installed.
        ValueError: If the treated unit is not found in the panel.
    """
    try:
        import numpy as np
        import pandas as pd
    except ImportError as exc:
        msg = (
            "numpy and pandas are required for synthetic_control(). "
            "Install with: pip install nyc311[stats]"
        )
        raise ImportError(msg) from exc

    _ = predictors  # reserved for future matching on covariates

    df = panel.to_dataframe()
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index()

    if treated_unit not in df["unit_id"].to_numpy():
        msg = f"treated_unit {treated_unit!r} not found in panel."
        raise ValueError(msg)

    treatment_event = None
    for te in panel.treatment_events:
        if treated_unit in te.treated_units:
            treatment_event = te
            break

    if treatment_event is None:
        msg = f"No treatment event found for unit {treated_unit!r}."
        raise ValueError(msg)

    treatment_date_str = treatment_event.treatment_date.isoformat()[:7]
    periods = sorted(df["period"].unique())
    pre_periods = [p for p in periods if p < treatment_date_str]
    post_periods = [p for p in periods if p >= treatment_date_str]

    donor_ids = [
        uid
        for uid in panel.unit_ids
        if uid != treated_unit and uid not in treatment_event.treated_units
    ]

    pivot = df.pivot_table(
        index="period", columns="unit_id", values=outcome, aggfunc="mean"
    )
    pivot = pivot.reindex(periods)

    treated_pre = pivot.loc[pre_periods, treated_unit].to_numpy().astype(float)
    donor_pre = pivot.loc[pre_periods, donor_ids].to_numpy().astype(float)

    valid_donors = ~np.isnan(donor_pre).any(axis=0)
    donor_ids_clean = [donor_ids[i] for i in range(len(donor_ids)) if valid_donors[i]]
    donor_pre = donor_pre[:, valid_donors]

    from scipy.optimize import minimize

    def _loss(w: Any) -> float:
        synthetic = donor_pre @ w
        return float(np.sum((treated_pre - synthetic) ** 2))

    n_donors = len(donor_ids_clean)
    w0 = np.ones(n_donors) / n_donors
    bounds = [(0.0, 1.0)] * n_donors
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}

    res = minimize(_loss, w0, method="SLSQP", bounds=bounds, constraints=constraints)
    w_star = res.x

    treated_full = pivot.loc[periods, treated_unit].to_numpy().astype(float)
    donor_full = pivot.loc[periods, donor_ids_clean].to_numpy().astype(float)
    counterfactual = donor_full @ w_star
    effect = treated_full - counterfactual

    pre_mspe = float(np.mean((treated_pre - donor_pre @ w_star) ** 2))
    post_mask = [p in post_periods for p in periods]
    att = float(np.mean(effect[np.array(post_mask)]))

    donor_weights = {
        uid: float(w_star[i])
        for i, uid in enumerate(donor_ids_clean)
        if w_star[i] > 1e-4
    }

    placebo_p = None
    if n_placebo_runs > 0 and len(donor_ids_clean) > 0:
        treated_ratio = _mspe_ratio(effect, pre_periods, post_periods, periods)
        more_extreme = 0
        for placebo_unit in donor_ids_clean[:n_placebo_runs]:
            placebo_pre = pivot.loc[pre_periods, placebo_unit].to_numpy().astype(float)
            other_donors = [d for d in donor_ids_clean if d != placebo_unit]
            placebo_donor_pre = (
                pivot.loc[pre_periods, other_donors].to_numpy().astype(float)
            )

            n_pd = len(other_donors)
            pw0 = np.ones(n_pd) / n_pd

            def _ploss(
                w: Any, _pp: Any = placebo_pre, _dp: Any = placebo_donor_pre
            ) -> float:
                return float(np.sum((_pp - _dp @ w) ** 2))

            pbounds = [(0.0, 1.0)] * n_pd
            pcons = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
            pres = minimize(
                _ploss, pw0, method="SLSQP", bounds=pbounds, constraints=pcons
            )

            placebo_full = pivot.loc[periods, placebo_unit].to_numpy().astype(float)
            placebo_donor_full = (
                pivot.loc[periods, other_donors].to_numpy().astype(float)
            )
            placebo_effect = placebo_full - placebo_donor_full @ pres.x

            pr = _mspe_ratio(placebo_effect, pre_periods, post_periods, periods)
            if pr >= treated_ratio:
                more_extreme += 1

        placebo_p = (more_extreme + 1) / (n_placebo_runs + 1)

    summary_lines = [
        f"Synthetic Control: {treated_unit}",
        f"Pre-treatment periods: {len(pre_periods)}",
        f"Post-treatment periods: {len(post_periods)}",
        f"Donors used: {len(donor_weights)}",
        f"Pre-treatment MSPE: {pre_mspe:.6f}",
        f"ATT: {att:.4f}",
    ]
    if placebo_p is not None:
        summary_lines.append(f"Placebo p-value: {placebo_p:.4f}")

    return SyntheticControlResult(
        treated_unit=treated_unit,
        donor_weights=donor_weights,
        counterfactual=tuple(float(c) for c in counterfactual),
        observed=tuple(float(o) for o in treated_full),
        treatment_effect=tuple(float(e) for e in effect),
        att=att,
        periods=tuple(str(p) for p in periods),
        pre_treatment_mspe=pre_mspe,
        placebo_p_value=placebo_p,
        model_summary="\n".join(summary_lines),
    )


def _mspe_ratio(
    effect: Any,
    pre_periods: list[str],
    post_periods: list[str],
    all_periods: list[str],
) -> float:
    """Compute the ratio of post/pre mean squared prediction error."""
    import numpy as np

    pre_idx = [i for i, p in enumerate(all_periods) if p in pre_periods]
    post_idx = [i for i, p in enumerate(all_periods) if p in post_periods]

    pre_mspe = float(np.mean(effect[pre_idx] ** 2))
    post_mspe = float(np.mean(effect[post_idx] ** 2))

    return post_mspe / pre_mspe if pre_mspe > 0 else float("inf")
