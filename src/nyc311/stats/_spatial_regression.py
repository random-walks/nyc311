"""Spatial lag and spatial error regression models.

Wraps PySAL's ``spreg`` module for maximum-likelihood estimation:

    Anselin, L. (1988). *Spatial Econometrics: Methods and Models*.
    Kluwer Academic Publishers.

    LeSage, J. P., & Pace, R. K. (2009). *Introduction to Spatial
    Econometrics*. CRC Press.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from nyc311.temporal._models import PanelDataset


@dataclass(frozen=True, slots=True)
class SpatialLagResult:
    """Result of a spatial lag (SAR) model."""

    coefficients: dict[str, float]
    std_errors: dict[str, float]
    p_values: dict[str, float]
    rho: float
    rho_p_value: float
    log_likelihood: float
    aic: float
    n_observations: int
    model_summary: str


@dataclass(frozen=True, slots=True)
class SpatialErrorResult:
    """Result of a spatial error (SEM) model."""

    coefficients: dict[str, float]
    std_errors: dict[str, float]
    p_values: dict[str, float]
    lam: float
    lam_p_value: float
    log_likelihood: float
    aic: float
    n_observations: int
    model_summary: str


def _extract_cross_section(
    panel: PanelDataset,
    outcome: str,
    regressors: tuple[str, ...],
    period: str | None,
) -> Any:
    """Extract a cross-sectional DataFrame from a panel."""
    df = panel.to_dataframe()
    if period is not None:
        df = df.xs(period, level="period")
    else:
        df = df.groupby(level="unit_id").mean(numeric_only=True)

    cols = [outcome, *regressors]
    return df[cols].dropna()


def spatial_lag_model(
    panel: PanelDataset,
    weights: dict[str, dict[str, float]],
    outcome: str,
    regressors: tuple[str, ...],
    *,
    period: str | None = None,
) -> SpatialLagResult:
    """Fit a spatial lag (SAR) model via maximum likelihood.

    Estimates: y = rho * W @ y + X @ beta + epsilon

    Args:
        panel: A :class:`PanelDataset` containing the outcome and
            regressor columns.
        weights: Nested dict ``{unit_a: {unit_b: weight}}`` of spatial
            weights (row-standardized).
        outcome: Column name for the dependent variable.
        regressors: Column names for the independent variables.
        period: If given, extract only this period as a cross-section.
            If ``None``, collapse across periods via group means.

    Returns:
        A :class:`SpatialLagResult` with estimated coefficients, the
        spatial autoregressive parameter (rho), and fit statistics.

    Raises:
        ImportError: If spreg or libpysal is not installed.
    """
    try:
        import numpy as np
        from libpysal.weights import W
        from spreg import ML_Lag
    except ImportError as exc:
        msg = (
            "spreg and libpysal are required for spatial_lag_model(). "
            "Install with: pip install nyc311[stats]"
        )
        raise ImportError(msg) from exc

    df = _extract_cross_section(panel, outcome, regressors, period)
    unit_ids = list(df.index)

    neighbors = {uid: list(weights.get(str(uid), {}).keys()) for uid in unit_ids}
    weight_vals = {uid: list(weights.get(str(uid), {}).values()) for uid in unit_ids}
    w = W(neighbors, weight_vals)

    y = np.asarray(df[outcome].values, dtype=float).reshape(-1, 1)
    x = np.column_stack([np.asarray(df[r].values, dtype=float) for r in regressors])

    model = ML_Lag(y, x, w, name_y=outcome, name_x=list(regressors))

    var_names = ["CONSTANT", *regressors]
    n_betas = len(var_names)
    coefficients = {var_names[i]: float(model.betas[i][0]) for i in range(n_betas)}
    std_errors = {var_names[i]: float(model.std_err[i]) for i in range(n_betas)}  # pylint: disable=no-member
    p_values = {var_names[i]: float(model.z_stat[i][1]) for i in range(n_betas)}  # pylint: disable=no-member

    rho = float(model.betas[n_betas][0])
    rho_p = float(model.z_stat[n_betas][1])  # pylint: disable=no-member

    return SpatialLagResult(
        coefficients=coefficients,
        std_errors=std_errors,
        p_values=p_values,
        rho=rho,
        rho_p_value=rho_p,
        log_likelihood=float(model.logll),
        aic=float(model.aic),
        n_observations=int(model.n),
        model_summary=str(model.summary),  # pylint: disable=no-member
    )


def spatial_error_model(
    panel: PanelDataset,
    weights: dict[str, dict[str, float]],
    outcome: str,
    regressors: tuple[str, ...],
    *,
    period: str | None = None,
) -> SpatialErrorResult:
    """Fit a spatial error (SEM) model via maximum likelihood.

    Estimates: y = X @ beta + u,  u = lambda * W @ u + epsilon

    Args:
        panel: A :class:`PanelDataset` containing the outcome and
            regressor columns.
        weights: Nested dict ``{unit_a: {unit_b: weight}}`` of spatial
            weights (row-standardized).
        outcome: Column name for the dependent variable.
        regressors: Column names for the independent variables.
        period: If given, extract only this period as a cross-section.
            If ``None``, collapse across periods via group means.

    Returns:
        A :class:`SpatialErrorResult` with estimated coefficients, the
        spatial error parameter (lambda), and fit statistics.

    Raises:
        ImportError: If spreg or libpysal is not installed.
    """
    try:
        import numpy as np
        from libpysal.weights import W
        from spreg import ML_Error
    except ImportError as exc:
        msg = (
            "spreg and libpysal are required for spatial_error_model(). "
            "Install with: pip install nyc311[stats]"
        )
        raise ImportError(msg) from exc

    df = _extract_cross_section(panel, outcome, regressors, period)
    unit_ids = list(df.index)

    neighbors = {uid: list(weights.get(str(uid), {}).keys()) for uid in unit_ids}
    weight_vals = {uid: list(weights.get(str(uid), {}).values()) for uid in unit_ids}
    w = W(neighbors, weight_vals)

    y = np.asarray(df[outcome].values, dtype=float).reshape(-1, 1)
    x = np.column_stack([np.asarray(df[r].values, dtype=float) for r in regressors])

    model = ML_Error(y, x, w, name_y=outcome, name_x=list(regressors))

    var_names = ["CONSTANT", *regressors]
    n_betas = len(var_names)
    coefficients = {var_names[i]: float(model.betas[i][0]) for i in range(n_betas)}
    std_errors = {var_names[i]: float(model.std_err[i]) for i in range(n_betas)}  # pylint: disable=no-member
    p_values = {var_names[i]: float(model.z_stat[i][1]) for i in range(n_betas)}  # pylint: disable=no-member

    lam = float(model.betas[n_betas][0])
    lam_p = float(model.z_stat[n_betas][1])  # pylint: disable=no-member

    return SpatialErrorResult(
        coefficients=coefficients,
        std_errors=std_errors,
        p_values=p_values,
        lam=lam,
        lam_p_value=lam_p,
        log_likelihood=float(model.logll),
        aic=float(model.aic),
        n_observations=int(model.n),
        model_summary=str(model.summary),  # pylint: disable=no-member
    )
