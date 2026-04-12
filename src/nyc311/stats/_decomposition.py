"""Seasonal decomposition of complaint time series.

Wraps ``statsmodels.tsa.seasonal.STL``:

    Cleveland, R. B., Cleveland, W. S., McRae, J. E., &
    Terpenning, I. J. (1990). STL: A seasonal-trend decomposition
    procedure based on loess. *Journal of Official Statistics*, 6(1),
    3--33.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DecompositionResult:
    """Seasonal + trend + residual decomposition."""

    trend: Any
    seasonal: Any
    residual: Any
    period: int


def seasonal_decompose(
    series: Any,
    *,
    period: int | None = None,
) -> DecompositionResult:
    """Decompose ``series`` into trend, seasonal, and residual components.

    Wraps :class:`statsmodels.tsa.seasonal.STL`. The series must be
    indexed by a ``DatetimeIndex``.

    Args:
        series: A ``pandas.Series`` indexed by a ``DatetimeIndex``.
        period: Seasonal period in observations. When ``None``, the
            period is inferred from the index frequency (monthly → 12,
            weekly → 52, daily → 7, quarterly → 4, yearly → 1).

    Returns:
        A :class:`DecompositionResult` exposing the trend, seasonal, and
        residual ``pandas.Series`` plus the period actually used.

    Raises:
        ImportError: If statsmodels or pandas is not installed. Install
            the optional stats extra with ``pip install nyc311[stats]``.
        TypeError: If ``series`` does not use a ``DatetimeIndex``.
    """
    try:
        import pandas as pd
        from statsmodels.tsa.seasonal import STL
    except ImportError as exc:
        message = (
            "statsmodels and pandas are required for seasonal_decompose(). "
            "Install with: pip install nyc311[stats]"
        )
        raise ImportError(message) from exc

    if not isinstance(series.index, pd.DatetimeIndex):
        msg = "series must have a DatetimeIndex."
        raise TypeError(msg)

    if period is None:
        freq = pd.infer_freq(series.index)
        period = _infer_period(freq)

    result = STL(series.dropna(), period=period).fit()
    return DecompositionResult(
        trend=result.trend,
        seasonal=result.seasonal,
        residual=result.resid,
        period=period,
    )


_FREQ_TO_PERIOD: dict[str, int] = {
    "D": 7,
    "W": 52,
    "M": 12,
    "MS": 12,
    "ME": 12,
    "Q": 4,
    "QS": 4,
    "QE": 4,
    "Y": 1,
    "YS": 1,
    "YE": 1,
    "A": 1,
}


def _infer_period(freq: str | None) -> int:
    if freq is None:
        return 12  # default to monthly
    for prefix, period in _FREQ_TO_PERIOD.items():
        if freq.startswith(prefix):
            return period
    return 12
