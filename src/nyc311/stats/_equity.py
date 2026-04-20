"""Equity and inequality decomposition methods.

Implements the Oaxaca-Blinder decomposition for explaining outcome
gaps between groups, and the population-weighted Theil index for
inequality measurement:

    Oaxaca, R. (1973). Male-female wage differentials in urban labor
    markets. *International Economic Review*, 14(3), 693--709.

    Blinder, A. S. (1973). Wage discrimination: Reduced form and
    structural estimates. *Journal of Human Resources*, 8(4), 436--455.

    Theil, H. (1967). *Economics and Information Theory*.
    North-Holland.

.. note::

    As of v1.0.0 factor-factory's ``engines.inequality`` wraps the
    Theil decomposition in the unified engine-family interface and is
    the preferred backend for :func:`theil_index`. See
    :func:`factor_factory.engines.inequality.estimate`.
    :func:`oaxaca_blinder_decomposition` has no factor-factory
    equivalent and this implementation remains authoritative.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class OaxacaBlinderResult:
    """Oaxaca-Blinder decomposition of an outcome gap."""

    mean_group_a: float
    mean_group_b: float
    total_gap: float
    explained: float
    unexplained: float
    component_contributions: dict[str, float]
    n_group_a: int
    n_group_b: int


@dataclass(frozen=True, slots=True)
class TheilResult:
    """Population-weighted Theil T index with group decomposition."""

    total: float
    between_group: float
    within_group: float
    unit_contributions: dict[str, float]
    n_units: int


def oaxaca_blinder_decomposition(
    group_a: Any,
    group_b: Any,
    outcome: str,
    regressors: tuple[str, ...],
) -> OaxacaBlinderResult:
    """Decompose the mean-outcome gap between two groups.

    Uses the Oaxaca-Blinder twofold decomposition with group B
    coefficients as the reference:

        gap = (mean(X_a) - mean(X_b)) @ beta_b  [explained]
            + mean(X_a) @ (beta_a - beta_b)      [unexplained]

    Args:
        group_a: ``pandas.DataFrame`` for the first group.
        group_b: ``pandas.DataFrame`` for the second group.
        outcome: Name of the outcome column.
        regressors: Column names to include as explanatory variables.

    Returns:
        An :class:`OaxacaBlinderResult` with the total gap, explained
        and unexplained components, and per-variable contributions.

    Raises:
        ImportError: If numpy or pandas is not installed.
        ValueError: If fewer than 2 observations exist in either group.
    """
    try:
        import numpy as np
    except ImportError as exc:
        msg = "numpy is required for oaxaca_blinder_decomposition(). Install with: pip install nyc311[stats]"
        raise ImportError(msg) from exc

    ya = np.asarray(group_a[outcome].values, dtype=float)
    yb = np.asarray(group_b[outcome].values, dtype=float)

    if len(ya) < 2 or len(yb) < 2:
        msg = "Each group must have at least 2 observations."
        raise ValueError(msg)

    xa = np.column_stack(
        [np.asarray(group_a[r].values, dtype=float) for r in regressors]
    )
    xb = np.column_stack(
        [np.asarray(group_b[r].values, dtype=float) for r in regressors]
    )

    xa_with_const = np.column_stack([np.ones(len(xa)), xa])
    xb_with_const = np.column_stack([np.ones(len(xb)), xb])

    beta_a = np.linalg.lstsq(xa_with_const, ya, rcond=None)[0]
    beta_b = np.linalg.lstsq(xb_with_const, yb, rcond=None)[0]

    mean_xa = xa.mean(axis=0)
    mean_xb = xb.mean(axis=0)

    mean_a = float(ya.mean())
    mean_b = float(yb.mean())
    total_gap = mean_a - mean_b

    explained_components = (mean_xa - mean_xb) * beta_b[1:]
    explained = float(explained_components.sum())
    mean_xa_with_const = np.concatenate([[1], mean_xa])
    unexplained = float(mean_xa_with_const @ (beta_a - beta_b))

    contributions = {
        name: float(explained_components[i]) for i, name in enumerate(regressors)
    }

    return OaxacaBlinderResult(
        mean_group_a=mean_a,
        mean_group_b=mean_b,
        total_gap=total_gap,
        explained=explained,
        unexplained=unexplained,
        component_contributions=contributions,
        n_group_a=len(ya),
        n_group_b=len(yb),
    )


def theil_index(
    values: dict[str, float],
    populations: dict[str, int],
    *,
    groups: dict[str, str] | None = None,
) -> TheilResult:
    """Compute the population-weighted Theil T index.

    When ``groups`` is provided, decomposes the total index into
    between-group and within-group components.

    Args:
        values: Mapping ``{unit_id: value}`` of the variable to
            measure inequality over (e.g. complaint rate).
        populations: Mapping ``{unit_id: population}`` for weighting.
        groups: Optional mapping ``{unit_id: group_label}`` for
            decomposition. When ``None``, between-group and
            within-group are both set to ``0.0``.

    Returns:
        A :class:`TheilResult` with the total index, between/within
        components, per-unit contributions, and count.

    Raises:
        ImportError: If numpy is not installed.
        ValueError: If values and populations have mismatched keys.
    """
    try:
        import numpy as np
    except ImportError as exc:
        msg = "numpy is required for theil_index(). Install with: pip install nyc311[stats]"
        raise ImportError(msg) from exc

    unit_ids = sorted(values)
    if set(unit_ids) != set(populations):
        msg = "values and populations must have the same keys."
        raise ValueError(msg)

    v = np.array([values[uid] for uid in unit_ids], dtype=float)
    p = np.array([populations[uid] for uid in unit_ids], dtype=float)

    total_pop = p.sum()
    total_value = (v * p).sum()

    if total_value <= 0 or total_pop <= 0:
        return TheilResult(
            total=0.0,
            between_group=0.0,
            within_group=0.0,
            unit_contributions=dict.fromkeys(unit_ids, 0.0),
            n_units=len(unit_ids),
        )

    mu = total_value / total_pop
    shares = (v * p) / total_value

    with np.errstate(divide="ignore", invalid="ignore"):
        log_ratios = np.where(v > 0, np.log(v / mu), 0.0)

    contributions_arr = shares * log_ratios
    total_t = float(np.sum(contributions_arr))

    unit_contributions = {
        uid: float(contributions_arr[i]) for i, uid in enumerate(unit_ids)
    }

    between = 0.0
    within = 0.0
    if groups is not None:
        group_labels = sorted(set(groups.values()))
        for g in group_labels:
            member_mask = np.array([groups.get(uid) == g for uid in unit_ids])
            g_pop = p[member_mask].sum()
            g_value = (v[member_mask] * p[member_mask]).sum()
            if g_pop <= 0 or g_value <= 0:
                continue
            g_mu = g_value / g_pop
            g_share = g_value / total_value
            between += g_share * float(np.log(g_mu / mu))

            g_v = v[member_mask]
            g_p = p[member_mask]
            g_shares = (g_v * g_p) / g_value
            with np.errstate(divide="ignore", invalid="ignore"):
                g_log = np.where(g_v > 0, np.log(g_v / g_mu), 0.0)
            within += g_share * float(np.sum(g_shares * g_log))

    return TheilResult(
        total=total_t,
        between_group=between,
        within_group=within,
        unit_contributions=unit_contributions,
        n_units=len(unit_ids),
    )
