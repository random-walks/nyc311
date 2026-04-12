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
    """Convert a panel dataset to a ``linearmodels``-ready DataFrame.

    Args:
        panel: The :class:`~nyc311.temporal.PanelDataset` to convert.
        outcome: Name of the dependent variable column. Must exist in
            the dataframe produced by :meth:`PanelDataset.to_dataframe`.
        regressors: Names of independent variable columns.

    Returns:
        A ``pandas.DataFrame`` indexed by ``(unit_id, period)`` with
        only the requested outcome and regressor columns and rows
        containing missing values dropped.

    Raises:
        ImportError: If pandas is not installed.
        ValueError: If any requested column is missing or the panel
            does not produce a ``MultiIndex`` DataFrame.
    """
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

    # linearmodels requires the time level of the MultiIndex to be numeric
    # or date-like. PanelDataset stores periods as ISO-style strings (e.g.
    # "2024-01" for monthly), so coerce them to a DatetimeIndex on the
    # second level of the MultiIndex before handing the frame off.
    unit_level = df.index.get_level_values(0)
    period_level = df.index.get_level_values(1)
    if not isinstance(period_level, pd.DatetimeIndex):
        period_level = pd.DatetimeIndex(pd.to_datetime(list(period_level)))
        df = df.copy()
        df.index = pd.MultiIndex.from_arrays(
            [unit_level, period_level],
            names=df.index.names,
        )

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

    Wraps :class:`linearmodels.panel.PanelOLS` with entity fixed effects
    by default and optional two-way fixed effects.

    Args:
        panel: A :class:`~nyc311.temporal.PanelDataset` providing the
            data, entities, and periods.
        outcome: Name of the dependent variable column.
        regressors: Names of independent variable columns.
        time_effects: When ``True``, include time fixed effects in
            addition to entity fixed effects (two-way FE).
        cluster: Cluster standard errors by ``"entity"`` (default),
            ``"time"``, or ``"both"``.

    Returns:
        A :class:`PanelRegressionResult` with coefficients, standard
        errors, p-values, R-squared, observation counts, and the full
        ``linearmodels`` summary string.

    Raises:
        ImportError: If ``linearmodels`` or pandas is not installed.
            Install the optional stats extra with
            ``pip install nyc311[stats]``.
        ValueError: If ``outcome`` or any of ``regressors`` is missing
            from the panel.
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
        coefficients={str(k): float(v) for k, v in result.params.items()},
        std_errors={str(k): float(v) for k, v in result.std_errors.items()},
        p_values={str(k): float(v) for k, v in result.pvalues.items()},
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

    Wraps :class:`linearmodels.panel.RandomEffects`.

    Args:
        panel: A :class:`~nyc311.temporal.PanelDataset` providing the
            data, entities, and periods.
        outcome: Name of the dependent variable column.
        regressors: Names of independent variable columns.

    Returns:
        A :class:`PanelRegressionResult` with coefficients, standard
        errors, p-values, R-squared, observation counts, and the full
        ``linearmodels`` summary string.

    Raises:
        ImportError: If ``linearmodels`` or pandas is not installed.
            Install the optional stats extra with
            ``pip install nyc311[stats]``.
        ValueError: If ``outcome`` or any of ``regressors`` is missing
            from the panel.
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
        coefficients={str(k): float(v) for k, v in result.params.items()},
        std_errors={str(k): float(v) for k, v in result.std_errors.items()},
        p_values={str(k): float(v) for k, v in result.pvalues.items()},
        r_squared=float(result.rsquared),
        n_observations=int(result.nobs),
        n_entities=int(result.entity_info.total),
        n_periods=int(result.time_info.total),
        model_summary=str(result.summary),
    )
