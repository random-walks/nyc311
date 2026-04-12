"""Immutable models for balanced panel datasets built from 311 complaints."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True, slots=True)
class TreatmentEvent:
    """A policy intervention applied to specific geographic units."""

    name: str
    description: str
    treated_units: tuple[str, ...]
    treatment_date: date
    geography: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Treatment name must not be empty.")
        if not self.treated_units:
            raise ValueError("treated_units must contain at least one unit.")


@dataclass(frozen=True, slots=True)
class PanelObservation:
    """One row in a balanced panel: (geographic_unit x time_period)."""

    #: Stable identifier of the geographic unit (community district code,
    #: NTA code, borough name, etc.).
    unit_id: str
    #: Period label (for example ``"2024-03"`` for monthly panels).
    period: str
    #: Total number of complaints in this unit/period cell.
    complaint_count: int
    #: Per-complaint-type counts within this cell.
    complaint_counts_by_type: dict[str, int]
    #: Fraction of complaints with a non-null ``resolution_description``.
    resolution_rate: float
    #: Median days from creation to period-end across resolved complaints,
    #: or ``None`` when no complaint in the cell was resolved.
    median_resolution_days: float | None
    #: ``True`` once the unit has been exposed to a treatment event.
    treatment: bool
    #: Date the unit was first treated, or ``None`` if never treated.
    treatment_date: date | None
    #: Total population for the unit, when supplied.
    population: int | None
    #: Optional time-invariant covariates merged in at panel-build time.
    covariates: dict[str, float] | None = None


@dataclass(frozen=True, slots=True)
class PanelDataset:
    """Balanced panel of (geographic_unit x time_period) observations.

    Methods return **new** :class:`PanelDataset` instances—the dataset is
    never mutated in place.
    """

    observations: tuple[PanelObservation, ...]
    unit_type: str
    periods: tuple[str, ...]
    treatment_events: tuple[TreatmentEvent, ...] = ()

    # ------------------------------------------------------------------
    # Filtering helpers
    # ------------------------------------------------------------------

    def treatment_group(self) -> PanelDataset:
        """Return only observations in units that were ever treated.

        Returns:
            A new :class:`PanelDataset` whose ``observations`` are
            restricted to units with a non-null ``treatment_date``. The
            ``periods`` and ``treatment_events`` fields are preserved.
        """
        treated_ids = {
            obs.unit_id for obs in self.observations if obs.treatment_date is not None
        }
        return PanelDataset(
            observations=tuple(
                o for o in self.observations if o.unit_id in treated_ids
            ),
            unit_type=self.unit_type,
            periods=self.periods,
            treatment_events=self.treatment_events,
        )

    def control_group(self) -> PanelDataset:
        """Return only observations in units that were never treated.

        Returns:
            A new :class:`PanelDataset` whose ``observations`` are
            restricted to units with no ``treatment_date``. The
            ``periods`` and ``treatment_events`` fields are preserved.
        """
        treated_ids = {
            obs.unit_id for obs in self.observations if obs.treatment_date is not None
        }
        return PanelDataset(
            observations=tuple(
                o for o in self.observations if o.unit_id not in treated_ids
            ),
            unit_type=self.unit_type,
            periods=self.periods,
            treatment_events=self.treatment_events,
        )

    def filter_periods(self, start: str, end: str) -> PanelDataset:
        """Restrict the dataset to a closed interval of periods.

        Args:
            start: Inclusive lower-bound period label.
            end: Inclusive upper-bound period label.

        Returns:
            A new :class:`PanelDataset` whose ``observations`` and
            ``periods`` are limited to labels ``p`` satisfying
            ``start <= p <= end``.
        """
        filtered_periods = tuple(p for p in self.periods if start <= p <= end)
        return PanelDataset(
            observations=tuple(
                o for o in self.observations if start <= o.period <= end
            ),
            unit_type=self.unit_type,
            periods=filtered_periods,
            treatment_events=self.treatment_events,
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def unit_ids(self) -> tuple[str, ...]:
        """The sorted, unique unit identifiers in the dataset.

        Returns:
            A tuple of distinct ``unit_id`` values from
            ``observations``, in lexicographic order.
        """
        return tuple(sorted({obs.unit_id for obs in self.observations}))

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def to_dataframe(self) -> Any:
        """Convert to a pandas DataFrame with a ``(unit_id, period)`` MultiIndex.

        Each per-type complaint count is exploded into a
        ``complaints_<type>`` column, and any per-unit covariates are
        merged in as additional columns.

        Returns:
            A ``pandas.DataFrame`` indexed by ``(unit_id, period)`` with
            one column per panel measure. The frame has no rows when the
            dataset is empty.

        Raises:
            ImportError: If pandas is not installed. Install the optional
                dataframes extra with ``pip install nyc311[dataframes]``.
        """
        try:
            import pandas as pd
        except ImportError as exc:
            message = (
                "pandas is required for to_dataframe(). "
                "Install it with: pip install nyc311[dataframes]"
            )
            raise ImportError(message) from exc

        rows: list[dict[str, Any]] = []
        for obs in self.observations:
            row: dict[str, Any] = {
                "unit_id": obs.unit_id,
                "period": obs.period,
                "complaint_count": obs.complaint_count,
                "resolution_rate": obs.resolution_rate,
                "median_resolution_days": obs.median_resolution_days,
                "treatment": obs.treatment,
                "population": obs.population,
            }
            for ctype, cnt in obs.complaint_counts_by_type.items():
                row[f"complaints_{ctype}"] = cnt
            if obs.covariates:
                row.update(obs.covariates)
            rows.append(row)

        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.set_index(["unit_id", "period"])
        return df
