"""Panel construction from service-request records."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Sequence
from datetime import date
from statistics import median

from nyc311.models import ServiceRequestRecord

from ._models import PanelDataset, PanelObservation, TreatmentEvent

# pandas Period uses short aliases ("M", "Q", "Y") while resample/offset
# uses the newer suffixed forms ("ME", "QE", "YE").  We accept both and
# normalise to the Period-compatible form.
_TO_PERIOD_FREQ: dict[str, str] = {
    "ME": "M",
    "QE": "Q",
    "QS": "Q",
    "YE": "Y",
    "YS": "Y",
    "A": "Y",
}


def _normalize_freq(freq: str) -> str:
    """Return a pandas Period-compatible frequency alias."""
    return _TO_PERIOD_FREQ.get(freq, freq)


def build_complaint_panel(
    records: Sequence[ServiceRequestRecord],
    *,
    geography: str = "community_district",
    freq: str = "ME",
    treatment_events: Sequence[TreatmentEvent] = (),
    population_data: dict[str, int] | None = None,
    covariates: dict[str, dict[str, float]] | None = None,
) -> PanelDataset:
    """Construct a balanced panel from service-request records.

    Parameters
    ----------
    records:
        Raw complaint records to aggregate.
    geography:
        Geographic unit (``"borough"`` or ``"community_district"``).
    freq:
        Pandas offset alias for the period length (default monthly).
    treatment_events:
        Policy interventions to code as treatment indicators.
    population_data:
        ``{unit_id: total_population}`` for per-capita calculations.
    covariates:
        ``{unit_id: {name: value}}`` for time-invariant demographic covariates.

    Returns
    -------
    PanelDataset
        Balanced panel with one observation per (unit, period).
    """
    try:
        import pandas as pd
    except ImportError as exc:
        message = (
            "pandas is required for build_complaint_panel(). "
            "Install it with: pip install nyc311[dataframes]"
        )
        raise ImportError(message) from exc

    norm_freq = _normalize_freq(freq)

    # -- group records by (unit, period) ----------------------------------
    grouped: dict[tuple[str, str], list[ServiceRequestRecord]] = defaultdict(list)
    all_units: set[str] = set()

    for rec in records:
        unit = rec.geography_value(geography)
        period = pd.Timestamp(rec.created_date).to_period(norm_freq)
        period_label = str(period)
        all_units.add(unit)
        grouped[(unit, period_label)].append(rec)

    if not all_units:
        return PanelDataset(
            observations=(),
            unit_type=geography,
            periods=(),
            treatment_events=tuple(treatment_events),
        )

    # -- determine ordered period labels ----------------------------------
    all_periods: set[str] = set()
    for _unit, period_label in grouped:
        all_periods.add(period_label)

    ordered_periods = tuple(sorted(all_periods))

    # -- build treatment lookup -------------------------------------------
    treatment_lookup: dict[str, date] = {}
    for event in treatment_events:
        for unit in event.treated_units:
            existing = treatment_lookup.get(unit)
            if existing is None or event.treatment_date < existing:
                treatment_lookup[unit] = event.treatment_date

    # -- build balanced panel ---------------------------------------------
    pops = population_data or {}
    covs = covariates or {}
    observations: list[PanelObservation] = []

    for unit in sorted(all_units):
        unit_treatment_date = treatment_lookup.get(unit)
        for period_label in ordered_periods:
            recs = grouped.get((unit, period_label), [])

            complaint_count = len(recs)
            type_counts: Counter[str] = Counter(r.complaint_type for r in recs)

            resolved = [r for r in recs if r.resolution_description is not None]
            resolution_rate = (
                len(resolved) / complaint_count if complaint_count else 0.0
            )

            if resolved:
                period_obj = pd.Period(period_label, freq=norm_freq)
                period_end = period_obj.end_time.date()
                days_list = [
                    max((period_end - r.created_date).days, 0) for r in resolved
                ]
                med_days: float | None = median(days_list)
            else:
                med_days = None

            is_treated = False
            if unit_treatment_date is not None:
                try:
                    period_obj = pd.Period(period_label, freq=norm_freq)
                    period_start = period_obj.start_time.date()
                    is_treated = period_start >= unit_treatment_date
                except Exception:  # noqa: BLE001
                    pass

            observations.append(
                PanelObservation(
                    unit_id=unit,
                    period=period_label,
                    complaint_count=complaint_count,
                    complaint_counts_by_type=dict(type_counts),
                    resolution_rate=resolution_rate,
                    median_resolution_days=med_days,
                    treatment=is_treated,
                    treatment_date=unit_treatment_date,
                    population=pops.get(unit),
                    covariates=covs.get(unit),
                )
            )

    return PanelDataset(
        observations=tuple(observations),
        unit_type=geography,
        periods=ordered_periods,
        treatment_events=tuple(treatment_events),
    )
