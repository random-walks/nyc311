"""Advanced factors for spatial and equity analysis."""

from __future__ import annotations

from statistics import median

from ._base import Factor, FactorContext


class SpatialLagFactor(Factor):
    """Spatial lag of complaint counts: weighted average of neighbors.

    Uses a precomputed spatial weights dict and a values dict to
    compute the weighted sum of neighboring unit values for the
    focal unit.
    """

    name = "spatial_lag"
    dtype = "float"

    def __init__(
        self,
        weights: dict[str, dict[str, float]],
        values: dict[str, float],
    ) -> None:
        """Initialize the spatial lag factor.

        Args:
            weights: Nested dict ``{unit_a: {unit_b: weight}}`` of
                spatial weights (typically row-standardized).
            values: Mapping ``{unit_id: numeric_value}`` for the
                variable to spatially lag.
        """
        self._weights = weights
        self._values = values

    def compute(self, context: FactorContext) -> float:
        """Return the spatial lag for the context's geographic unit.

        Returns:
            The weighted sum of neighboring values.  Returns ``0.0``
            when the unit has no neighbors in the weights dict.
        """
        unit = context.geography_value
        nbrs = self._weights.get(unit, {})
        if not nbrs:
            return 0.0
        return sum(w * self._values.get(nb, 0.0) for nb, w in nbrs.items())


class EquityGapFactor(Factor):
    """Disparity metric: ratio of unit resolution time to citywide median.

    Values above 1.0 indicate the unit resolves complaints slower
    than the citywide median; below 1.0, faster.
    """

    name = "equity_gap"
    dtype = "float"

    def __init__(self, citywide_median_days: float) -> None:
        """Initialize the equity gap factor.

        Args:
            citywide_median_days: The citywide median resolution
                time in days, used as the denominator for the ratio.
        """
        self._citywide_median = citywide_median_days

    def compute(self, context: FactorContext) -> float:
        """Return the resolution-time equity ratio for ``context``.

        Returns:
            ``unit_median / citywide_median``, or ``0.0`` when no
            resolved complaints exist or the citywide median is
            non-positive.
        """
        resolved = [
            c for c in context.complaints if c.resolution_description is not None
        ]
        if not resolved or self._citywide_median <= 0:
            return 0.0
        days = [
            max(float((context.time_window_end - c.created_date).days), 0.0)
            for c in resolved
        ]
        unit_median = median(days)
        return unit_median / self._citywide_median
