"""Panel regression wrappers for 311 panel datasets.

Wraps ``linearmodels``:

    Wooldridge, J. M. (2010). *Econometric analysis of cross section
    and panel data* (2nd ed.). MIT Press.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from nyc311.temporal import PanelDataset


@dataclass(frozen=True, slots=True)
class PanelRegressionResult:
    """Summary of a panel regression fit."""

    method: str
    coefficients: dict[str, float]
    std_errors: dict[str, float]
    p_values: dict[str, float]
    r_squared: float
    n_observations: int
    n_entities: int
    n_periods: int
    model_summary: str


def _prepare_panel_data(
    panel: PanelDataset,
    outcome: str,
    regressors: tuple[str, ...],
) -> Any:
    """Convert PanelDataset to linearmodels-compatible MultiIndex DataFrame."""
    try:
        import pandas as pd
    except ImportError as exc:
        message = (
            "pandas is required for panel regressions. "
            "Install with: pip install nyc311[stats]"
        )
        raise ImportError(message) from exc

    df = panel.to_dataframe()
    required = [outcome, *regressors]
    missing = [c for c in required if c not in df.columns]
    if missing:
        msg = f"Missing columns in panel: {', '.join(missing)}"
        raise ValueError(msg)

    # Ensure MultiIndex is set correctly for linearmodels
    if not isinstance(df.index, pd.MultiIndex):
        msg = "Panel DataFrame must have a (unit_id, period) MultiIndex."
        raise ValueError(msg)

    return df[required].dropna()


def panel_fixed_effects(
    panel: PanelDataset,
    outcome: str,
    regressors: tuple[str, ...],
    *,
    time_effects: bool = False,
    cluster: Literal["entity", "time", "both"] = "entity",
) -> PanelRegressionResult:
    """Estimate a fixed-effects panel regression.

    Parameters
    ----------
    panel:
        A :class:`~nyc311.temporal.PanelDataset`.
    outcome:
        Name of the dependent variable column.
    regressors:
        Names of independent variable columns.
    time_effects:
        Include time fixed effects (two-way FE).
    cluster:
        Cluster standard errors by entity, time, or both.

    Returns
    -------
    PanelRegressionResult
    """
    try:
        from linearmodels.panel import PanelOLS
    except ImportError as exc:
        message = (
            "linearmodels is required for panel regressions. "
            "Install with: pip install nyc311[stats]"
        )
        raise ImportError(message) from exc

    df = _prepare_panel_data(panel, outcome, regressors)
    y = df[outcome]
    x = df[list(regressors)]

    cov_type_map = {
        "entity": "clustered",
        "time": "clustered",
        "both": "clustered",
    }
    cluster_entity = cluster in ("entity", "both")
    cluster_time = cluster in ("time", "both")

    model = PanelOLS(
        y,
        x,
        entity_effects=True,
        time_effects=time_effects,
    )
    result = model.fit(
        cov_type=cov_type_map[cluster],
        cluster_entity=cluster_entity,
        cluster_time=cluster_time,
    )

    return PanelRegressionResult(
        method="two_way_fe" if time_effects else "entity_fe",
        coefficients={k: float(v) for k, v in result.params.items()},
        std_errors={k: float(v) for k, v in result.std_errors.items()},
        p_values={k: float(v) for k, v in result.pvalues.items()},
        r_squared=float(result.rsquared),
        n_observations=int(result.nobs),
        n_entities=int(result.entity_info.total),
        n_periods=int(result.time_info.total),
        model_summary=str(result.summary),
    )


def panel_random_effects(
    panel: PanelDataset,
    outcome: str,
    regressors: tuple[str, ...],
) -> PanelRegressionResult:
    """Estimate a random-effects panel regression.

    Parameters
    ----------
    panel:
        A :class:`~nyc311.temporal.PanelDataset`.
    outcome:
        Name of the dependent variable column.
    regressors:
        Names of independent variable columns.

    Returns
    -------
    PanelRegressionResult
    """
    try:
        from linearmodels.panel import RandomEffects
    except ImportError as exc:
        message = (
            "linearmodels is required for panel regressions. "
            "Install with: pip install nyc311[stats]"
        )
        raise ImportError(message) from exc

    df = _prepare_panel_data(panel, outcome, regressors)
    y = df[outcome]
    x = df[list(regressors)]

    model = RandomEffects(y, x)
    result = model.fit()

    return PanelRegressionResult(
        method="random_effects",
        coefficients={k: float(v) for k, v in result.params.items()},
        std_errors={k: float(v) for k, v in result.std_errors.items()},
        p_values={k: float(v) for k, v in result.pvalues.items()},
        r_squared=float(result.rsquared),
        n_observations=int(result.nobs),
        n_entities=int(result.entity_info.total),
        n_periods=int(result.time_info.total),
        model_summary=str(result.summary),
    )
