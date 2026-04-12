"""Power analysis and minimum detectable effect for panel experiments.

Standard cluster-randomized trial power formula adapted for balanced
panel designs used in NYC 311 policy evaluations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PowerResult:
    """Result of a power / minimum detectable effect calculation."""

    mde: float
    alpha: float
    power: float
    n_units: int
    n_periods: int
    icc: float
    variance_explained: float


def minimum_detectable_effect(
    n_units: int,
    n_periods: int,
    *,
    icc: float = 0.05,
    alpha: float = 0.05,
    power: float = 0.80,
    proportion_treated: float = 0.5,
    outcome_variance: float = 1.0,
    r_squared: float = 0.0,
) -> PowerResult:
    """Compute the minimum detectable effect for a panel experiment.

    Uses the standard cluster-RCT MDE formula:

        MDE = (z_{alpha/2} + z_{beta}) * sqrt(2 * sigma^2 * DE / (N_t * T))

    where DE = 1 + (T - 1) * ICC is the design effect.

    Args:
        n_units: Total number of geographic units (clusters).
        n_periods: Number of time periods observed.
        icc: Intra-cluster correlation coefficient.  Defaults to
            ``0.05``.
        alpha: Significance level.  Defaults to ``0.05``.
        power: Statistical power (1 - beta).  Defaults to ``0.80``.
        proportion_treated: Fraction of units assigned to treatment.
            Defaults to ``0.5``.
        outcome_variance: Variance of the outcome variable.  Defaults
            to ``1.0``.
        r_squared: Proportion of variance explained by covariates.
            Defaults to ``0.0`` (no covariates).

    Returns:
        A :class:`PowerResult` with the computed MDE and all design
        parameters.

    Raises:
        ImportError: If scipy is not installed.  Install with
            ``pip install nyc311[stats]``.
        ValueError: If any parameter is out of its valid range.
    """
    try:
        from scipy.stats import norm
    except ImportError as exc:
        msg = "scipy is required for minimum_detectable_effect(). Install with: pip install nyc311[stats]"
        raise ImportError(msg) from exc

    if n_units < 2:
        msg = "n_units must be at least 2."
        raise ValueError(msg)
    if n_periods < 1:
        msg = "n_periods must be at least 1."
        raise ValueError(msg)
    if not 0.0 < proportion_treated < 1.0:
        msg = "proportion_treated must be in (0, 1)."
        raise ValueError(msg)

    z_alpha = float(norm.ppf(1.0 - alpha / 2.0))
    z_beta = float(norm.ppf(power))

    design_effect = 1.0 + (n_periods - 1) * icc
    n_treated = n_units * proportion_treated
    adjusted_var = outcome_variance * (1.0 - r_squared)

    mde = (z_alpha + z_beta) * (
        (2.0 * adjusted_var * design_effect / (n_treated * n_periods)) ** 0.5
    )

    return PowerResult(
        mde=float(mde),
        alpha=alpha,
        power=power,
        n_units=n_units,
        n_periods=n_periods,
        icc=icc,
        variance_explained=r_squared,
    )
