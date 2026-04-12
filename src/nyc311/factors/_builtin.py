"""Built-in factors for NYC 311 complaint analysis."""

from __future__ import annotations

from collections import Counter
from statistics import mean, median

from ._base import Factor, FactorContext


class ComplaintVolumeFactor(Factor):
    """Total complaint count, optionally per-capita per 10 000 residents.

    When *per_capita* is ``True`` and :attr:`FactorContext.total_population`
    is available, the result is ``count / population * 10_000`` (a float).
    Otherwise the raw integer count is returned.
    """

    dtype = "int"

    def __init__(self, *, per_capita: bool = False) -> None:
        self._per_capita = per_capita
        self.name = "complaint_rate_per_10k" if per_capita else "complaint_volume"
        if per_capita:
            self.dtype = "float"  # type: ignore[assignment]

    def compute(self, context: FactorContext) -> int | float:
        count = len(context.complaints)
        if (
            self._per_capita
            and context.total_population
            and context.total_population > 0
        ):
            return count / context.total_population * 10_000
        return count


class ResolutionTimeFactor(Factor):
    """Median or mean days between complaint creation and resolution.

    Uses ``resolution_description is not None`` as a proxy for resolved.
    Returns ``-1.0`` when no resolved complaints exist in the context.
    """

    name = "resolution_time_days"
    dtype = "float"

    def __init__(self, *, method: str = "median") -> None:
        if method not in ("median", "mean"):
            msg = f"method must be 'median' or 'mean', got {method!r}"
            raise ValueError(msg)
        self._method = method

    def compute(self, context: FactorContext) -> float:
        resolved = [
            c for c in context.complaints if c.resolution_description is not None
        ]
        if not resolved:
            return -1.0

        days: list[float] = []
        for c in resolved:
            delta = context.time_window_end - c.created_date
            days.append(max(float(delta.days), 0.0))

        if not days:
            return -1.0
        return median(days) if self._method == "median" else mean(days)


class TopicConcentrationFactor(Factor):
    """Herfindahl-Hirschman Index of complaint-type shares.

    HHI = sum(share_i^2) where share_i is the proportion of complaints of
    type *i*.  Range [1/N, 1.0]; higher values indicate more concentration
    in fewer complaint types.

    Returns ``0.0`` when the context has no complaints.
    """

    name = "topic_concentration"
    dtype = "float"

    def compute(self, context: FactorContext) -> float:
        if not context.complaints:
            return 0.0
        counts = Counter(c.complaint_type for c in context.complaints)
        total = len(context.complaints)
        return sum((count / total) ** 2 for count in counts.values())


class SeasonalityFactor(Factor):
    """Deviation of complaint count from a seasonal baseline.

    *baseline_monthly_counts* maps month number (1-12) to the expected
    count for that month.  The factor returns ``(actual - expected) /
    expected`` as a fractional deviation.  Returns ``0.0`` when the
    baseline is missing for the context's month or is zero.
    """

    name = "seasonality_deviation"
    dtype = "float"

    def __init__(self, baseline_monthly_counts: dict[int, float]) -> None:
        self._baseline = baseline_monthly_counts

    def compute(self, context: FactorContext) -> float:
        month = context.time_window_start.month
        expected = self._baseline.get(month, 0.0)
        if expected <= 0:
            return 0.0
        actual = len(context.complaints)
        return (actual - expected) / expected


class AnomalyScoreFactor(Factor):
    """Z-score of this unit's complaint volume.

    Because the z-score is relative to the **full set of contexts** in
    the pipeline run, this factor stores intermediate counts and
    finalizes during :meth:`Pipeline.run`.  As a stateless compromise
    it uses a fixed *population_mean* and *population_std* provided at
    construction time.

    Returns ``0.0`` when *population_std* is zero.
    """

    name = "anomaly_score"
    dtype = "float"

    def __init__(
        self,
        *,
        population_mean: float,
        population_std: float,
    ) -> None:
        self._mean = population_mean
        self._std = population_std

    def compute(self, context: FactorContext) -> float:
        if self._std == 0:
            return 0.0
        return (len(context.complaints) - self._mean) / self._std


class ResponseRateFactor(Factor):
    """Fraction of complaints that received a resolution description.

    Range [0.0, 1.0].  Returns ``0.0`` for empty contexts.
    """

    name = "response_rate"
    dtype = "float"

    def compute(self, context: FactorContext) -> float:
        if not context.complaints:
            return 0.0
        resolved = sum(
            1 for c in context.complaints if c.resolution_description is not None
        )
        return resolved / len(context.complaints)


class RecurrenceFactor(Factor):
    """Fraction of complaints at locations that appear more than once.

    Locations are identified by rounding latitude/longitude to 4 decimal
    places (~11 m precision).  Returns ``0.0`` when no complaints have
    coordinates.
    """

    name = "recurrence_rate"
    dtype = "float"

    def compute(self, context: FactorContext) -> float:
        geo_complaints = [
            c
            for c in context.complaints
            if c.latitude is not None and c.longitude is not None
        ]
        if not geo_complaints:
            return 0.0

        location_counts = Counter(
            (round(c.latitude, 4), round(c.longitude, 4))  # type: ignore[arg-type]
            for c in geo_complaints
        )
        recurrent = sum(1 for c in location_counts.values() if c > 1)
        return recurrent / len(location_counts) if location_counts else 0.0
