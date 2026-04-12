"""Self-exciting Hawkes point process estimation.

Models event contagion where past events increase the rate of
future events:

    Mohler, G. O., Short, M. B., Brantingham, P. J., Schoenberg,
    F. P., & Tye, G. E. (2011). Self-exciting point process
    modeling of crime. *Journal of the American Statistical
    Association*, 106(493), 100--108.

    Hawkes, A. G. (1971). Spectra of some self-exciting and
    mutually exciting point processes. *Biometrika*, 58(1), 83--90.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class HawkesResult:
    """Result of a Hawkes process estimation."""

    background_rate: float
    triggering_kernel_alpha: float
    triggering_kernel_beta: float
    branching_ratio: float
    n_events: int
    log_likelihood: float
    model_summary: str


def fit_hawkes_process(
    event_times: Any,
    *,
    kernel: str = "exponential",
    max_iter: int = 1000,
) -> HawkesResult:
    """Fit a univariate Hawkes process to event timestamps.

    The conditional intensity is:

        lambda(t) = mu + sum_{t_i < t} alpha * beta * exp(-beta * (t - t_i))

    Args:
        event_times: Array-like of event timestamps as floats
            (e.g. seconds since epoch, or days since start).
        kernel: Triggering kernel type. Currently only
            ``"exponential"`` is supported.
        max_iter: Maximum iterations for the EM algorithm.

    Returns:
        A :class:`HawkesResult` with background rate, triggering
        kernel parameters, branching ratio, and log-likelihood.

    Raises:
        ImportError: If numpy or scipy is not installed.
        ValueError: If fewer than 3 events are provided.
    """
    if kernel != "exponential":
        msg = f"Only 'exponential' kernel is supported, got {kernel!r}"
        raise ValueError(msg)

    try:
        import numpy as np
    except ImportError as exc:
        msg = "numpy is required for fit_hawkes_process(). Install with: pip install nyc311[stats]"
        raise ImportError(msg) from exc

    times = np.sort(np.asarray(event_times, dtype=float))
    n = len(times)

    if n < 3:
        msg = "Need at least 3 events to fit a Hawkes process."
        raise ValueError(msg)

    t_max = times[-1] - times[0]
    times = times - times[0]

    mu = n / (2.0 * t_max)
    alpha = 0.1
    beta_param = 1.0

    for _ in range(max_iter):
        intensities = np.full(n, mu)
        for i in range(1, n):
            dt = times[i] - times[:i]
            intensities[i] += alpha * beta_param * np.sum(np.exp(-beta_param * dt))

        p = np.zeros((n, n))
        for i in range(1, n):
            dt = times[i] - times[:i]
            trigger = alpha * beta_param * np.exp(-beta_param * dt)
            total = mu + np.sum(trigger)
            if total > 0:
                p[i, :i] = trigger / total

        n_background = sum(
            mu
            / (
                mu
                + alpha
                * beta_param
                * np.sum(np.exp(-beta_param * (times[i] - times[:i])))
            )
            if i > 0
            else 1.0
            for i in range(n)
        )

        mu_new = n_background / t_max

        n_triggered = n - n_background
        alpha_new = n_triggered / n if n > 0 else 0.0

        if n_triggered > 0:
            weighted_dt_sum = 0.0
            for i in range(1, n):
                dt = times[i] - times[:i]
                weights = p[i, :i]
                weighted_dt_sum += np.sum(weights * dt)
            beta_new = (
                n_triggered / weighted_dt_sum if weighted_dt_sum > 0 else beta_param
            )
        else:
            beta_new = beta_param

        if (
            abs(mu_new - mu) < 1e-8
            and abs(alpha_new - alpha) < 1e-8
            and abs(beta_new - beta_param) < 1e-8
        ):
            mu, alpha, beta_param = mu_new, alpha_new, beta_new
            break

        mu, alpha, beta_param = mu_new, alpha_new, beta_new

    ll = 0.0
    for i in range(n):
        lam_i = mu
        if i > 0:
            dt = times[i] - times[:i]
            lam_i += alpha * beta_param * float(np.sum(np.exp(-beta_param * dt)))
        ll += np.log(max(lam_i, 1e-10))
    ll -= mu * t_max
    for i in range(n):
        ll += alpha * (np.exp(-beta_param * (t_max - times[i])) - 1.0)

    branching = alpha / beta_param if beta_param > 0 else float("inf")

    summary = (
        f"Hawkes Process: {n} events over {t_max:.1f} time units\n"
        f"Background rate (mu): {mu:.4f}\n"
        f"Triggering: alpha={alpha:.4f}, beta={beta_param:.4f}\n"
        f"Branching ratio: {branching:.4f}\n"
        f"Log-likelihood: {ll:.2f}"
    )

    return HawkesResult(
        background_rate=float(mu),
        triggering_kernel_alpha=float(alpha),
        triggering_kernel_beta=float(beta_param),
        branching_ratio=float(branching),
        n_events=n,
        log_likelihood=float(ll),
        model_summary=summary,
    )
