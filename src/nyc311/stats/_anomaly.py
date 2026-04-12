"""Seasonality-adjusted anomaly detection via STL residuals.

Decomposes a time series with STL, then flags observations whose
residuals exceed a z-score threshold:

    Cleveland, R. B., Cleveland, W. S., McRae, J. E., &
    Terpenning, I. J. (1990). STL: A seasonal-trend decomposition
    procedure based on loess. *Journal of Official Statistics*, 6(1),
    3--33.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class STLAnomalyResult:
    """Result of STL-residual anomaly detection."""

    anomaly_dates: tuple[Any, ...]
    anomaly_scores: tuple[float, ...]
    threshold: float
    n_anomalies: int
    residual_mean: float
    residual_std: float


def detect_stl_anomalies(
    series: Any,
    *,
    period: int | None = None,
    threshold: float = 2.0,
) -> STLAnomalyResult:
    """Detect anomalies using STL decomposition residuals.

    Decomposes ``series`` via STL and flags observations whose
    absolute residual z-score exceeds ``threshold``.

    Args:
        series: A ``pandas.Series`` indexed by a ``DatetimeIndex``.
        period: Seasonal period in observations.  When ``None``, the
            period is inferred from the index frequency.
        threshold: Absolute z-score threshold above which an
            observation is flagged as anomalous.  Defaults to ``2.0``.

    Returns:
        An :class:`STLAnomalyResult` with the anomaly dates, their
        z-scores, and summary statistics of the residual distribution.

    Raises:
        ImportError: If statsmodels or pandas is not installed.
            Install with ``pip install nyc311[stats]``.
    """
    try:
        import numpy as np
    except ImportError as exc:
        msg = "numpy is required for detect_stl_anomalies(). Install with: pip install nyc311[stats]"
        raise ImportError(msg) from exc

    from nyc311.stats._decomposition import seasonal_decompose

    decomp = seasonal_decompose(series, period=period)
    residual = decomp.residual.dropna()

    resid_values = np.asarray(residual.values, dtype=float)
    mu = float(np.mean(resid_values))
    sigma = float(np.std(resid_values, ddof=1)) if len(resid_values) > 1 else 0.0

    if sigma == 0.0:
        return STLAnomalyResult(
            anomaly_dates=(),
            anomaly_scores=(),
            threshold=threshold,
            n_anomalies=0,
            residual_mean=mu,
            residual_std=0.0,
        )

    z_scores = (resid_values - mu) / sigma
    mask = np.abs(z_scores) > threshold

    anomaly_dates = tuple(residual.index[mask])
    anomaly_scores = tuple(float(z) for z in z_scores[mask])

    return STLAnomalyResult(
        anomaly_dates=anomaly_dates,
        anomaly_scores=anomaly_scores,
        threshold=threshold,
        n_anomalies=int(mask.sum()),
        residual_mean=mu,
        residual_std=sigma,
    )
