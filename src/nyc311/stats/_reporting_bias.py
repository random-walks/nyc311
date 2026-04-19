"""Reporting-bias correction for 311 complaint analysis.

Implements two approaches:

1. **Ecometric adjustment** via mixed-effects regression, following:

    O'Brien, D. T. (2015). Custodians and publicists: Why the
    promise of 311 has not been fully realized. *Environment and
    Planning B*, 42(1), 5--19.

2. **Latent reporting-bias EM** inspired by:

    Agostini, A., Chen, Y., Lim, S., Silverman, J. D., & Neill,
    D. B. (2025). A latent variable model for estimating true
    heating complaint rates from NYC 311 data. *Annals of Applied
    Statistics* (forthcoming).

.. note::

    As of v1.0.0 factor-factory's ``engines.reporting_bias`` ships a
    unified latent-EM adapter and is the preferred backend when
    moving work into the engine-family interface. See
    :func:`factor_factory.engines.reporting_bias.estimate`. This
    module remains available for backwards compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nyc311.temporal._models import PanelDataset


@dataclass(frozen=True, slots=True)
class ReportingAdjustmentResult:
    """Result of ecometric reporting-rate adjustment."""

    raw_rates: dict[str, float]
    adjusted_rates: dict[str, float]
    adjustment_factors: dict[str, float]
    covariates_used: tuple[str, ...]
    icc: float
    model_summary: str


@dataclass(frozen=True, slots=True)
class LatentReportingResult:
    """Result of latent reporting-bias EM estimation."""

    estimated_true_rates: dict[str, float]
    reporting_probabilities: dict[str, float]
    observed_rates: dict[str, float]
    n_iterations: int
    converged: bool
    log_likelihood_trace: tuple[float, ...]


def reporting_rate_adjustment(
    panel: PanelDataset,
    outcome: str,
    demographic_covariates: tuple[str, ...],
) -> ReportingAdjustmentResult:
    """Adjust complaint rates for neighborhood reporting propensity.

    Fits a mixed-effects model with unit random intercepts:

        outcome ~ covariates + (1 | unit_id)

    The random intercepts capture unit-level reporting propensity
    after controlling for demographic covariates.

    Args:
        panel: A :class:`PanelDataset` with covariates attached.
        outcome: Column name for the complaint rate to adjust.
        demographic_covariates: Column names for demographic controls
            (e.g. median income, population density).

    Returns:
        A :class:`ReportingAdjustmentResult` with raw and adjusted
        rates, random intercepts, ICC, and model summary.

    Raises:
        ImportError: If statsmodels or pandas is not installed.
    """
    try:
        from statsmodels.regression.mixed_linear_model import MixedLM
    except ImportError as exc:
        msg = (
            "statsmodels and pandas are required for "
            "reporting_rate_adjustment(). "
            "Install with: pip install nyc311[stats]"
        )
        raise ImportError(msg) from exc

    df = panel.to_dataframe()
    df = df.reset_index()

    formula_parts = [outcome, "~", " + ".join(demographic_covariates)]
    formula = " ".join(formula_parts)

    model = MixedLM.from_formula(
        formula,
        groups="unit_id",
        data=df,
    )
    result = model.fit(reml=True)  # pylint: disable=unexpected-keyword-arg

    unit_ids = sorted(df["unit_id"].unique())
    raw_rates: dict[str, float] = {}
    for uid in unit_ids:
        mask = df["unit_id"] == uid
        raw_rates[uid] = float(df.loc[mask, outcome].mean())

    re = result.random_effects
    adjustment_factors: dict[str, float] = {}
    for uid in unit_ids:
        adjustment_factors[uid] = float(re[uid].iloc[0]) if uid in re else 0.0

    group_var = (
        float(result.cov_re.iloc[0, 0])
        if hasattr(result.cov_re, "iloc")
        else float(result.cov_re)
    )
    resid_var = float(result.scale)
    icc = group_var / (group_var + resid_var) if (group_var + resid_var) > 0 else 0.0

    adjusted_rates: dict[str, float] = {}
    for uid in unit_ids:
        adjusted_rates[uid] = raw_rates[uid] - adjustment_factors[uid]

    return ReportingAdjustmentResult(
        raw_rates=raw_rates,
        adjusted_rates=adjusted_rates,
        adjustment_factors=adjustment_factors,
        covariates_used=demographic_covariates,
        icc=icc,
        model_summary=str(result.summary()),
    )


def latent_reporting_bias_em(
    complaint_counts: dict[str, int],
    populations: dict[str, int],
    covariates: dict[str, dict[str, float]] | None = None,
    *,
    max_iter: int = 200,
    tol: float = 1e-6,
) -> LatentReportingResult:
    """Estimate true complaint rates via expectation-maximization.

    Models observed counts as a product of a latent true rate and a
    reporting probability.  The EM algorithm iterates between
    estimating true rates (M-step, Poisson MLE) and reporting
    probabilities (M-step, logistic on covariates).

    Args:
        complaint_counts: Mapping ``{unit_id: observed_count}``.
        populations: Mapping ``{unit_id: population}``.
        covariates: Optional mapping
            ``{unit_id: {covariate_name: value}}``.  When ``None``,
            a uniform reporting probability is assumed.
        max_iter: Maximum EM iterations.
        tol: Convergence tolerance on log-likelihood change.

    Returns:
        A :class:`LatentReportingResult` with estimated true rates,
        reporting probabilities, and convergence diagnostics.

    Raises:
        ImportError: If numpy or scipy is not installed.
    """
    try:
        import numpy as np
        from scipy.special import expit
    except ImportError as exc:
        msg = (
            "numpy and scipy are required for latent_reporting_bias_em(). "
            "Install with: pip install nyc311[stats]"
        )
        raise ImportError(msg) from exc

    unit_ids = sorted(complaint_counts)
    n = len(unit_ids)

    y = np.array([complaint_counts[uid] for uid in unit_ids], dtype=float)
    pop = np.array([populations[uid] for uid in unit_ids], dtype=float)

    observed_rates = y / np.maximum(pop, 1.0)

    lambda_hat = observed_rates.copy() + 1e-8
    rho_hat = np.full(n, 0.5)

    if covariates is not None:
        cov_names = sorted(next(iter(covariates.values())).keys())
        x = np.column_stack(
            [
                np.array([covariates[uid][c] for uid in unit_ids], dtype=float)
                for c in cov_names
            ]
        )
        x = np.column_stack([np.ones(n), x])
        beta = np.zeros(x.shape[1])
    else:
        x = None
        beta = None

    ll_trace: list[float] = []
    converged = False

    for _iteration in range(max_iter):
        expected_true = y / np.maximum(rho_hat, 1e-10)
        lambda_hat = expected_true / np.maximum(pop, 1.0)
        lambda_hat = np.maximum(lambda_hat, 1e-10)

        if x is not None and beta is not None:
            for _ in range(5):
                rho_pred = expit(x @ beta)
                residual = (y / np.maximum(lambda_hat * pop, 1e-10)) - rho_pred
                grad = x.T @ residual
                hess = -x.T @ (np.diag(rho_pred * (1 - rho_pred)) @ x)
                try:
                    step = np.linalg.solve(hess, grad)
                    beta = beta - step
                except np.linalg.LinAlgError:
                    break
            rho_hat = expit(x @ beta)
        else:
            rho_hat = np.clip(y / np.maximum(lambda_hat * pop, 1e-10), 0.01, 0.99)

        ll = float(
            np.sum(
                y * np.log(np.maximum(lambda_hat * pop * rho_hat, 1e-10))
                - lambda_hat * pop * rho_hat
            )
        )
        ll_trace.append(ll)

        if len(ll_trace) > 1 and abs(ll_trace[-1] - ll_trace[-2]) < tol:
            converged = True
            break

    return LatentReportingResult(
        estimated_true_rates={
            uid: float(lambda_hat[i]) for i, uid in enumerate(unit_ids)
        },
        reporting_probabilities={
            uid: float(rho_hat[i]) for i, uid in enumerate(unit_ids)
        },
        observed_rates={
            uid: float(observed_rates[i]) for i, uid in enumerate(unit_ids)
        },
        n_iterations=len(ll_trace),
        converged=converged,
        log_likelihood_trace=tuple(ll_trace),
    )
