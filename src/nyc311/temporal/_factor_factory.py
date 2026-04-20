"""Adapter from :class:`PanelDataset` to :class:`factor_factory.tidy.Panel`.

This module provides the bridge between nyc311's
:class:`nyc311.temporal.PanelDataset` and factor-factory's
:class:`factor_factory.tidy.Panel`. The adapter is additive: nyc311's
own dataclasses are unchanged, and existing consumers of
``PanelDataset`` keep their API.

See :doc:`docs/integration.md` for the full crosswalk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import factor_factory.tidy as ff_tidy

    from ._models import PanelDataset


_SPATIAL_WEIGHTS_ATTR = "nyc311_spatial_weights"


def _period_to_timestamp(period_label: str) -> Any:
    """Convert a PanelDataset period label (e.g. ``"2024-03"``) to a Timestamp."""
    import pandas as pd

    return pd.Period(period_label).to_timestamp(how="start")


def _infer_freq(period_labels: tuple[str, ...]) -> str:
    """Infer a pandas offset alias from a sorted tuple of period labels."""
    if not period_labels:
        return "MS"
    sample = period_labels[0]
    # "2024-03" → monthly; "2024Q1" → quarterly; "2024" → yearly
    if "Q" in sample:
        return "QS"
    if len(sample) == 4 and sample.isdigit():
        return "YS"
    return "MS"


def panel_dataset_to_factor_factory(
    dataset: PanelDataset,
    *,
    outcome_col: str = "complaint_count",
    provenance: ff_tidy.Provenance | None = None,
    spatial_weights: dict[str, dict[str, float]] | None = None,
) -> ff_tidy.Panel:
    """Convert a :class:`PanelDataset` to a :class:`factor_factory.tidy.Panel`.

    Maps nyc311's panel model onto factor-factory's tidy Panel contract:

    - ``unit_id`` → Panel first-level MultiIndex, named ``unit_id``.
    - ``period`` (string label) → pandas Timestamp at the period start,
      second-level index named ``period``.
    - ``complaint_count`` → primary outcome column (configurable via
      ``outcome_col``).
    - ``treatment`` (bool) → int 0/1 column named ``treatment``.
    - ``resolution_rate``, ``median_resolution_days``, ``population``,
      per-type complaint counts, and covariates flow through as
      additional columns the engine can consume as covariates.
    - ``TreatmentEvent`` tuples are translated to factor-factory's
      frozen :class:`TreatmentEvent` pydantic model (``geography`` maps
      to ``dimension``).
    - A ``spatial_weights`` dict (as produced by
      :func:`nyc311.temporal.build_distance_weights`) is attached to
      the resulting :attr:`Panel.df.attrs` under the key
      ``"nyc311_spatial_weights"`` for in-memory round-trip.

    Args:
        dataset: The balanced :class:`PanelDataset` to convert.
        outcome_col: Column name to tag as the primary outcome in the
            Panel metadata. Must be one of ``"complaint_count"``,
            ``"resolution_rate"``, ``"median_resolution_days"``, or a
            ``"complaints_<type>"`` column present on the observations.
        provenance: Optional factor-factory :class:`Provenance` record
            describing the dataset. When ``None``, a default is
            constructed pointing at the NYC Open Data 311 Socrata
            endpoint.
        spatial_weights: Optional nested dict as produced by
            :func:`build_distance_weights`. Stashed on
            ``panel.df.attrs["nyc311_spatial_weights"]`` so downstream
            code can pick it up without a second computation.

    Returns:
        A fully-validated :class:`factor_factory.tidy.Panel`.

    Raises:
        ImportError: If ``factor-factory`` or pandas is not installed.
        ValueError: If ``dataset`` is empty or ``outcome_col`` is not
            present on the first observation.
    """
    try:
        import pandas as pd
        from factor_factory.tidy import (
            Panel,
            PanelMetadata,
            Provenance,
        )
        from factor_factory.tidy import (
            TreatmentEvent as FFTreatmentEvent,
        )
    except ImportError as exc:
        message = (
            "factor-factory and pandas are required for "
            "PanelDataset.to_factor_factory_panel(). "
            "Install with: pip install nyc311"
        )
        raise ImportError(message) from exc

    if not dataset.observations:
        message = "Cannot convert an empty PanelDataset to a factor-factory Panel."
        raise ValueError(message)

    rows: list[dict[str, Any]] = []
    for obs in dataset.observations:
        row: dict[str, Any] = {
            "unit_id": obs.unit_id,
            "period": _period_to_timestamp(obs.period),
            "complaint_count": obs.complaint_count,
            "resolution_rate": obs.resolution_rate,
            "treatment": int(obs.treatment),
        }
        if obs.median_resolution_days is not None:
            row["median_resolution_days"] = obs.median_resolution_days
        if obs.population is not None:
            row["population"] = obs.population
        for ctype, cnt in obs.complaint_counts_by_type.items():
            row[f"complaints_{ctype}"] = cnt
        if obs.covariates:
            row.update(obs.covariates)
        rows.append(row)

    df = pd.DataFrame(rows).set_index(["unit_id", "period"]).sort_index()

    if outcome_col not in df.columns:
        message = (
            f"outcome_col={outcome_col!r} not in panel columns. "
            f"Available: {sorted(df.columns)}"
        )
        raise ValueError(message)

    ff_events = tuple(
        FFTreatmentEvent(
            name=ev.name,
            description=ev.description,
            treated_units=tuple(ev.treated_units),
            treatment_date=ev.treatment_date,
            dimension=ev.geography,
        )
        for ev in dataset.treatment_events
    )

    if provenance is None:
        provenance = Provenance(
            data_source="NYC Open Data — 311 Service Requests (Socrata erm2-nwe9)",
            license="CC0-1.0",
            creator="nyc311.temporal.PanelDataset",
            citation="https://opendata.cityofnewyork.us/",
        )

    metadata = PanelMetadata(
        outcome_cols=(outcome_col,),
        period_kind="timestamp",
        freq=_infer_freq(dataset.periods),
        dimension=dataset.unit_type,
        treatment_events=ff_events,
        record_count=len(dataset.observations),
        provenance=provenance,
    )

    panel = Panel(df, metadata)

    if spatial_weights is not None:
        panel.df.attrs[_SPATIAL_WEIGHTS_ATTR] = dict(spatial_weights)

    return panel


def spatial_weights_from_panel(
    panel: ff_tidy.Panel,
) -> dict[str, dict[str, float]] | None:
    """Recover spatial weights previously attached via the adapter.

    Args:
        panel: A :class:`factor_factory.tidy.Panel` that was produced by
            :func:`panel_dataset_to_factor_factory` with
            ``spatial_weights`` supplied.

    Returns:
        The nested weights dict, or ``None`` if no spatial weights were
        attached.
    """
    weights = panel.df.attrs.get(_SPATIAL_WEIGHTS_ATTR)
    if weights is None:
        return None
    return dict(weights)


__all__ = [
    "panel_dataset_to_factor_factory",
    "spatial_weights_from_panel",
]
