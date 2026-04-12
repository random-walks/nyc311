"""Changepoint detection for structural breaks in complaint series.

Wraps the ``ruptures`` library implementing:

    Killick, R., Fearnhead, P., & Eckley, I. A. (2012). Optimal
    detection of changepoints with a linear computational cost. *JASA*,
    107(500), 1590--1598.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class ChangepointResult:
    """Detected structural breaks in a time series."""

    breakpoints: tuple[int, ...]
    breakpoint_dates: tuple[date, ...]
    n_segments: int
    penalty: float


def detect_changepoints(
    series: Any,
    *,
    method: Literal["pelt", "binseg"] = "pelt",
    penalty: float | None = None,
    min_segment_size: int = 5,
) -> ChangepointResult:
    """Detect structural breaks in a complaint time series.

    Parameters
    ----------
    series:
        A ``pandas.Series`` with a ``DatetimeIndex``.
    method:
        Detection algorithm (``"pelt"`` or ``"binseg"``).
    penalty:
        PELT penalty; if ``None`` uses ``log(n) * variance`` (BIC-like).
    min_segment_size:
        Minimum observations between changepoints.

    Returns
    -------
    ChangepointResult
    """
    try:
        import numpy as np
        import pandas as pd
        import ruptures as rpt
    except ImportError as exc:
        message = (
            "ruptures and pandas are required for detect_changepoints(). "
            "Install with: pip install nyc311[stats]"
        )
        raise ImportError(message) from exc

    if not isinstance(series.index, pd.DatetimeIndex):
        msg = "series must have a DatetimeIndex."
        raise TypeError(msg)

    signal = series.dropna().to_numpy().astype(float)
    n = len(signal)

    if penalty is None:
        penalty = float(np.log(n) * np.var(signal)) if n > 1 else 1.0

    if method == "pelt":
        algo = rpt.Pelt(model="l2", min_size=min_segment_size).fit(signal)
    else:
        algo = rpt.Binseg(model="l2", min_size=min_segment_size).fit(signal)

    raw_breaks: list[int] = algo.predict(pen=penalty)
    # ruptures returns the *end* of each segment; the last element equals n
    breakpoint_indices = [b for b in raw_breaks if b < n]

    dates_index = series.dropna().index
    breakpoint_dates: list[date] = []
    for idx in breakpoint_indices:
        ts = dates_index[idx]
        breakpoint_dates.append(ts.date() if hasattr(ts, "date") else ts)

    return ChangepointResult(
        breakpoints=tuple(breakpoint_indices),
        breakpoint_dates=tuple(breakpoint_dates),
        n_segments=len(breakpoint_indices) + 1,
        penalty=penalty,
    )
