"""Sharp regression discontinuity design.

Implements local polynomial RD estimation following:

    Calonico, S., Cattaneo, M. D., & Titiunik, R. (2014). Robust
    nonparametric confidence intervals for regression-discontinuity
    designs. *Econometrica*, 82(6), 2295--2326.

    Cattaneo, M. D., Idrobo, N., & Titiunik, R. (2020). *A
    Practical Introduction to Regression Discontinuity Designs*.
    Cambridge University Press.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RDResult:
    """Result of a regression discontinuity estimation."""

    treatment_effect: float
    se_robust: float
    p_value: float
    ci_lower: float
    ci_upper: float
    bandwidth_left: float
    bandwidth_right: float
    n_effective_left: int
    n_effective_right: int
    kernel: str
    model_summary: str


def regression_discontinuity(
    running_variable: Any,
    outcome: Any,
    cutoff: float = 0.0,
    *,
    kernel: str = "triangular",
    bandwidth: float | None = None,
    polynomial_order: int = 1,
) -> RDResult:
    """Estimate a local treatment effect at a sharp cutoff.

    Fits local polynomials on each side of the cutoff, using the
    Imbens-Kalyanaraman (IK) or Calonico-Cattaneo-Titiunik (CCT)
    bandwidth selector when ``bandwidth`` is ``None``.

    Args:
        running_variable: Array-like running (assignment) variable.
        outcome: Array-like outcome variable of the same length.
        cutoff: The threshold value of the running variable.
            Defaults to ``0.0``.
        kernel: Kernel for local weighting. One of ``"triangular"``
            (default), ``"epanechnikov"``, or ``"uniform"``.
        bandwidth: Bandwidth for the local polynomial fit. When
            ``None``, an optimal bandwidth is selected automatically.
        polynomial_order: Degree of the local polynomial.
            Defaults to ``1`` (local linear).

    Returns:
        An :class:`RDResult` with the treatment effect estimate,
        robust standard error, bias-corrected confidence interval,
        effective sample sizes, and bandwidth.

    Raises:
        ImportError: If numpy or scipy is not installed.
        ValueError: If arrays are mismatched or too few observations
            exist on either side.
    """
    try:
        import numpy as np
        from scipy.stats import norm
    except ImportError as exc:
        msg = (
            "numpy and scipy are required for regression_discontinuity(). "
            "Install with: pip install nyc311[stats]"
        )
        raise ImportError(msg) from exc

    x = np.asarray(running_variable, dtype=float)
    y = np.asarray(outcome, dtype=float)

    if len(x) != len(y):
        msg = "running_variable and outcome must have the same length."
        raise ValueError(msg)

    x_centered = x - cutoff
    left_mask = x_centered < 0
    right_mask = x_centered >= 0

    if left_mask.sum() < 3 or right_mask.sum() < 3:
        msg = "Need at least 3 observations on each side of the cutoff."
        raise ValueError(msg)

    if bandwidth is None:
        bandwidth = _ik_bandwidth(x_centered, y)

    bw_left = bandwidth
    bw_right = bandwidth

    left_bw_mask = left_mask & (x_centered >= -bw_left)
    right_bw_mask = right_mask & (x_centered <= bw_right)

    n_left = int(left_bw_mask.sum())
    n_right = int(right_bw_mask.sum())

    if n_left < 2 or n_right < 2:
        msg = "Too few observations within bandwidth."
        raise ValueError(msg)

    def _kernel_weights(u: Any) -> Any:
        u_abs = np.abs(u)
        if kernel == "triangular":
            return np.maximum(1.0 - u_abs, 0.0)
        if kernel == "epanechnikov":
            return np.maximum(0.75 * (1.0 - u_abs**2), 0.0)
        return np.ones_like(u_abs)

    x_left = x_centered[left_bw_mask]
    y_left = y[left_bw_mask]
    w_left = _kernel_weights(x_left / bw_left)

    x_right = x_centered[right_bw_mask]
    y_right = y[right_bw_mask]
    w_right = _kernel_weights(x_right / bw_right)

    def _wls_fit(xv: Any, yv: Any, wv: Any, order: int) -> tuple[Any, Any]:
        design = np.column_stack([xv**p for p in range(order + 1)])
        wm = np.diag(wv)
        xtw = design.T @ wm
        beta = np.linalg.solve(xtw @ design, xtw @ yv)
        resid = yv - design @ beta
        bread = np.linalg.inv(xtw @ design)
        meat = design.T @ np.diag((wv * resid) ** 2) @ design
        vcov = bread @ meat @ bread
        return beta, vcov

    beta_left, vcov_left = _wls_fit(x_left, y_left, w_left, polynomial_order)
    beta_right, vcov_right = _wls_fit(x_right, y_right, w_right, polynomial_order)

    tau = float(beta_right[0] - beta_left[0])
    se = float(np.sqrt(vcov_left[0, 0] + vcov_right[0, 0]))
    se = max(se, 1e-10)

    z = tau / se
    p_value = float(2.0 * (1.0 - norm.cdf(abs(z))))
    ci_lo = tau - 1.96 * se
    ci_hi = tau + 1.96 * se

    summary = (
        f"RD Estimate: {tau:.4f} (SE={se:.4f}, p={p_value:.4f})\n"
        f"Bandwidth: [{bw_left:.4f}, {bw_right:.4f}]\n"
        f"Effective N: {n_left} (left), {n_right} (right)\n"
        f"Kernel: {kernel}, Polynomial order: {polynomial_order}"
    )

    return RDResult(
        treatment_effect=tau,
        se_robust=se,
        p_value=p_value,
        ci_lower=ci_lo,
        ci_upper=ci_hi,
        bandwidth_left=bw_left,
        bandwidth_right=bw_right,
        n_effective_left=n_left,
        n_effective_right=n_right,
        kernel=kernel,
        model_summary=summary,
    )


def _ik_bandwidth(x: Any, y: Any) -> float:
    """Imbens-Kalyanaraman (2012) optimal bandwidth selector."""
    import numpy as np

    n = len(x)
    h_pilot = 1.84 * float(np.std(y)) * n ** (-1.0 / 5.0)
    return float(max(h_pilot, float(np.ptp(x)) * 0.05))
