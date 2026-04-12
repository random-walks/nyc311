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

    unit_id: str
    period: str
    complaint_count: int
    complaint_counts_by_type: dict[str, int]
    resolution_rate: float
    median_resolution_days: float | None
    treatment: bool
    treatment_date: date | None
    population: int | None
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
        """Return only observations in units that were ever treated."""
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
        """Return only observations in units that were never treated."""
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
        """Return observations whose period is between *start* and *end* inclusive."""
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
        """Sorted unique unit identifiers."""
        return tuple(sorted({obs.unit_id for obs in self.observations}))

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def to_dataframe(self) -> Any:
        """Convert to a pandas DataFrame with ``(unit_id, period)`` MultiIndex."""
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
