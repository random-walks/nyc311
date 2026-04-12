"""Interrupted time series analysis for policy evaluation.

Implements the segmented regression model described in:

    Bernal, J. L., Cummins, S., & Gasparrini, A. (2017). Interrupted
    time series regression for the evaluation of public health
    interventions: a tutorial. *International Journal of Epidemiology*,
    46(1), 348--355.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True, slots=True)
class ITSResult:
    """Result of a segmented interrupted-time-series regression."""

    pre_trend: float
    post_trend: float
    level_change: float
    trend_change: float
    p_value_level: float
    p_value_trend: float
    model_summary: str


def interrupted_time_series(
    series: Any,
    intervention_date: date,
    *,
    covariates: Any | None = None,
) -> ITSResult:
    """Fit a segmented regression for *intervention_date*.

    Parameters
    ----------
    series:
        A ``pandas.Series`` with a ``DatetimeIndex``.
    intervention_date:
        The date the intervention began.
    covariates:
        Optional ``pandas.DataFrame`` of exogenous regressors aligned to *series*.

    Returns
    -------
    ITSResult
    """
    try:
        import numpy as np
        import pandas as pd
        from statsmodels.regression.linear_model import OLS
        from statsmodels.tools import add_constant
    except ImportError as exc:
        message = (
            "statsmodels and pandas are required for interrupted_time_series(). "
            "Install with: pip install nyc311[stats]"
        )
        raise ImportError(message) from exc

    if not isinstance(series.index, pd.DatetimeIndex):
        msg = "series must have a DatetimeIndex."
        raise TypeError(msg)

    df = pd.DataFrame({"y": series})
    df["time"] = np.arange(len(df))
    df["intervention"] = (df.index >= pd.Timestamp(intervention_date)).astype(int)
    df["time_after"] = df["time"] * df["intervention"]

    exog_cols = ["time", "intervention", "time_after"]
    if covariates is not None:
        for col in covariates.columns:
            df[col] = covariates[col].to_numpy()
            exog_cols.append(col)

    exog = add_constant(df[exog_cols])
    model = OLS(df["y"], exog, missing="drop").fit()

    pre_trend = float(model.params["time"])
    trend_change = float(model.params["time_after"])
    post_trend = pre_trend + trend_change
    level_change = float(model.params["intervention"])
    p_level = float(model.pvalues["intervention"])
    p_trend = float(model.pvalues["time_after"])

    return ITSResult(
        pre_trend=pre_trend,
        post_trend=post_trend,
        level_change=level_change,
        trend_change=trend_change,
        p_value_level=p_level,
        p_value_trend=p_trend,
        model_summary=str(model.summary()),
    )
