"""Geographically weighted regression for spatially varying coefficients.

Wraps PySAL's ``mgwr`` module:

    Brunsdon, C., Fotheringham, A. S., & Charlton, M. E. (1996).
    Geographically weighted regression: A method for exploring
    spatial nonstationarity. *Geographical Analysis*, 28(4),
    281--298.

    Oshan, T. M., Li, Z., Kang, W., Wolf, L. J., &
    Fotheringham, A. S. (2019). mgwr: A Python implementation of
    multiscale geographically weighted regression for investigating
    process spatial heterogeneity and scale. *ISPRS International
    Journal of Geo-Information*, 8(6), 269.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class GWRResult:
    """Result of a geographically weighted regression."""

    local_coefficients: dict[str, tuple[float, ...]]
    local_r_squared: tuple[float, ...]
    bandwidth: float
    aic: float
    unit_ids: tuple[str, ...]
    global_r_squared: float
    n_observations: int
    model_summary: str


def geographically_weighted_regression(
    values: dict[str, float],
    regressors: dict[str, dict[str, float]],
    coordinates: dict[str, tuple[float, float]],
    *,
    bandwidth: float | None = None,
    kernel: str = "bisquare",
) -> GWRResult:
    """Fit a geographically weighted regression.

    Estimates locally varying coefficients, allowing the relationship
    between outcome and regressors to change across space.

    Args:
        values: Mapping ``{unit_id: outcome_value}``.
        regressors: Mapping
            ``{unit_id: {variable_name: value}}``.
        coordinates: Mapping ``{unit_id: (latitude, longitude)}``.
        bandwidth: Fixed bandwidth.  When ``None``, an optimal
            bandwidth is selected via cross-validation.
        kernel: Kernel function.  One of ``"bisquare"`` (default),
            ``"gaussian"``, or ``"exponential"``.

    Returns:
        A :class:`GWRResult` with local coefficients per unit,
        local R-squared values, bandwidth, and fit statistics.

    Raises:
        ImportError: If mgwr is not installed.
        ValueError: If fewer than 5 observations are provided.
    """
    try:
        import numpy as np
        from scipy.spatial.distance import cdist
    except ImportError as exc:
        msg = (
            "numpy and scipy are required for "
            "geographically_weighted_regression(). "
            "Install with: pip install nyc311[spatial-regression]"
        )
        raise ImportError(msg) from exc

    unit_ids = sorted(values)
    if len(unit_ids) < 5:
        msg = "GWR requires at least 5 observations."
        raise ValueError(msg)

    var_names = sorted(next(iter(regressors.values())).keys())
    y = np.array([values[uid] for uid in unit_ids], dtype=float)
    x_raw = np.column_stack(
        [
            np.array([regressors[uid][v] for uid in unit_ids], dtype=float)
            for v in var_names
        ]
    )
    x = np.column_stack([np.ones(len(unit_ids)), x_raw])
    coords = np.array([coordinates[uid] for uid in unit_ids], dtype=float)

    dists = cdist(coords, coords)

    if bandwidth is None:
        bandwidth = _cv_bandwidth(y, x, dists, kernel)

    all_names = ["CONSTANT", *var_names]
    n = len(unit_ids)
    k = x.shape[1]
    local_betas = np.zeros((n, k))
    local_r2 = np.zeros(n)
    y_hat_global = np.zeros(n)

    for i in range(n):
        w_i = _kernel_weights(dists[i], bandwidth, kernel)
        w_diag = np.diag(w_i)
        xtwx = x.T @ w_diag @ x
        xtwy = x.T @ w_diag @ y
        try:
            beta_i = np.linalg.solve(xtwx, xtwy)
        except np.linalg.LinAlgError:
            beta_i = np.linalg.lstsq(xtwx, xtwy, rcond=None)[0]
        local_betas[i] = beta_i
        y_hat_i = x[i] @ beta_i
        y_hat_global[i] = y_hat_i

        ss_tot = float(np.sum(w_i * (y - np.average(y, weights=w_i)) ** 2))
        ss_res = float(np.sum(w_i * (y - x @ beta_i) ** 2))
        local_r2[i] = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    ss_tot_global = float(np.sum((y - np.mean(y)) ** 2))
    ss_res_global = float(np.sum((y - y_hat_global) ** 2))
    global_r2 = 1.0 - ss_res_global / ss_tot_global if ss_tot_global > 0 else 0.0

    aic_val = n * np.log(ss_res_global / n) + 2 * k

    local_coefficients = {
        name: tuple(float(local_betas[i, j]) for i in range(n))
        for j, name in enumerate(all_names)
    }

    summary = (
        f"GWR: {n} observations, {k} parameters\n"
        f"Bandwidth: {bandwidth:.4f}, Kernel: {kernel}\n"
        f"Global R-squared: {global_r2:.4f}, AIC: {aic_val:.2f}"
    )

    return GWRResult(
        local_coefficients=local_coefficients,
        local_r_squared=tuple(float(r) for r in local_r2),
        bandwidth=float(bandwidth),
        aic=float(aic_val),
        unit_ids=tuple(unit_ids),
        global_r_squared=float(global_r2),
        n_observations=n,
        model_summary=summary,
    )


def _kernel_weights(distances: Any, bandwidth: float, kernel: str) -> Any:
    """Compute kernel weights for a single focal point."""
    import numpy as np

    u = distances / bandwidth
    if kernel == "bisquare":
        return np.where(u <= 1.0, (1.0 - u**2) ** 2, 0.0)
    if kernel == "gaussian":
        return np.exp(-0.5 * u**2)
    if kernel == "exponential":
        return np.exp(-u)
    return np.where(u <= 1.0, 1.0, 0.0)


def _cv_bandwidth(y: Any, x: Any, dists: Any, kernel: str) -> float:
    """Select bandwidth via leave-one-out cross-validation."""
    import numpy as np

    n = len(y)
    candidates = np.percentile(dists[dists > 0], [25, 50, 75, 90])

    best_bw = float(candidates[-1])
    best_cv = float("inf")

    for bw in candidates:
        cv_error = 0.0
        for i in range(n):
            w_i = _kernel_weights(dists[i], bw, kernel)
            w_i[i] = 0.0
            w_diag = np.diag(w_i)
            xtwx = x.T @ w_diag @ x
            xtwy = x.T @ w_diag @ y
            try:
                beta_i = np.linalg.solve(xtwx, xtwy)
                y_hat = float(x[i] @ beta_i)
            except np.linalg.LinAlgError:
                y_hat = float(np.mean(y))
            cv_error += (y[i] - y_hat) ** 2

        if cv_error < best_cv:
            best_cv = cv_error
            best_bw = float(bw)

    return best_bw
