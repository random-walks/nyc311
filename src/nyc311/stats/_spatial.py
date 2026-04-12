"""Spatial autocorrelation statistics for complaint analysis.

Wraps PySAL's ``esda`` module:

    Rey, S. J., & Anselin, L. (2007). PySAL: A Python library of
    spatial analytical methods. *Review of Regional Studies*, 37(1),
    5--27.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MoranResult:
    """Global Moran's I test result."""

    statistic: float
    p_value: float
    z_score: float
    expected: float


@dataclass(frozen=True, slots=True)
class LISAResult:
    """Local Indicators of Spatial Association."""

    local_statistic: tuple[float, ...]
    p_values: tuple[float, ...]
    cluster_labels: tuple[str, ...]
    unit_ids: tuple[str, ...]


_LISA_QUAD_LABELS: dict[int, str] = {
    1: "HH",
    2: "LH",
    3: "LL",
    4: "HL",
}


def global_morans_i(
    values: dict[str, float],
    weights: dict[str, dict[str, float]],
) -> MoranResult:
    """Compute Global Moran's I for ``values`` under spatial ``weights``.

    Args:
        values: Mapping ``{unit_id: numeric_value}`` to test for spatial
            autocorrelation. Unit IDs must align with those in
            ``weights``.
        weights: Nested dict ``{unit_a: {unit_b: weight}}`` describing
            the spatial weights matrix; typically row-standardized.

    Returns:
        A :class:`MoranResult` with the Moran's I statistic, the
        permutation-based p-value, the standardized z-score, and the
        expected value under the null hypothesis.

    Raises:
        ImportError: If ``esda`` or ``libpysal`` is not installed.
            Install the optional stats extra with
            ``pip install nyc311[stats]``.
    """
    try:
        import numpy as np
        from esda.moran import Moran
        from libpysal.weights import W
    except ImportError as exc:
        message = (
            "esda and libpysal are required for spatial autocorrelation. "
            "Install with: pip install nyc311[stats]"
        )
        raise ImportError(message) from exc

    unit_ids = sorted(values)
    y = np.array([values[uid] for uid in unit_ids])

    neighbors = {uid: list(weights.get(uid, {}).keys()) for uid in unit_ids}
    weight_vals = {uid: list(weights.get(uid, {}).values()) for uid in unit_ids}
    w = W(neighbors, weight_vals)

    mi = Moran(y, w)
    return MoranResult(
        statistic=float(mi.I),
        p_value=float(mi.p_sim),
        z_score=float(mi.z_sim),
        expected=float(mi.EI),
    )


def local_morans_i(
    values: dict[str, float],
    weights: dict[str, dict[str, float]],
    *,
    permutations: int = 999,
) -> LISAResult:
    """Compute Local Moran's I (LISA) for hotspot/coldspot identification.

    Args:
        values: Mapping ``{unit_id: numeric_value}`` for the variable
            being tested.
        weights: Nested dict ``{unit_a: {unit_b: weight}}`` describing
            the spatial weights matrix.
        permutations: Number of conditional permutations used to derive
            pseudo p-values.

    Returns:
        A :class:`LISAResult` containing the local statistic, pseudo
        p-values, and quadrant cluster labels (``"HH"``, ``"LH"``,
        ``"LL"``, ``"HL"``, or ``"ns"`` for non-significant) per unit.

    Raises:
        ImportError: If ``esda`` or ``libpysal`` is not installed.
            Install the optional stats extra with
            ``pip install nyc311[stats]``.
    """
    try:
        import numpy as np
        from esda.moran import Moran_Local
        from libpysal.weights import W
    except ImportError as exc:
        message = (
            "esda and libpysal are required for LISA analysis. "
            "Install with: pip install nyc311[stats]"
        )
        raise ImportError(message) from exc

    unit_ids = sorted(values)
    y = np.array([values[uid] for uid in unit_ids])

    neighbors = {uid: list(weights.get(uid, {}).keys()) for uid in unit_ids}
    weight_vals = {uid: list(weights.get(uid, {}).values()) for uid in unit_ids}
    w = W(neighbors, weight_vals)

    lisa = Moran_Local(y, w, permutations=permutations)

    labels: list[str] = []
    for i, quad in enumerate(lisa.q):
        if lisa.p_sim[i] < 0.05:
            labels.append(_LISA_QUAD_LABELS.get(int(quad), "ns"))
        else:
            labels.append("ns")

    return LISAResult(
        local_statistic=tuple(float(x) for x in lisa.Is),
        p_values=tuple(float(x) for x in lisa.p_sim),
        cluster_labels=tuple(labels),
        unit_ids=tuple(unit_ids),
    )
