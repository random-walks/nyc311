"""Tests for the nyc311 ↔ factor-factory adapters.

Covers:

- :func:`nyc311.temporal.panel_dataset_to_factor_factory` (and the
  equivalent :meth:`PanelDataset.to_factor_factory_panel` method) on a
  small balanced panel with a single treatment event.
- Round-trip of the spatial weights dict through
  :func:`spatial_weights_from_panel`.
- :meth:`nyc311.factors.Pipeline.as_factor_factory_estimate` chaining
  into ``factor_factory.engines.did.twfe``, recovering the synthetic
  ATT.
"""

from __future__ import annotations

from datetime import date

import pytest

pd = pytest.importorskip("pandas")
ff = pytest.importorskip("factor_factory")

from nyc311.factors import Pipeline  # noqa: E402
from nyc311.temporal import (  # noqa: E402
    PanelDataset,
    PanelObservation,
    TreatmentEvent,
    panel_dataset_to_factor_factory,
    spatial_weights_from_panel,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_synthetic_panel(
    *,
    treatment_offset: float = -5.0,
    baseline: int = 50,
) -> PanelDataset:
    """Build a 2-unit x 4-period balanced panel with a known ATT.

    One unit is treated from period 3; the outcome is ``baseline +
    treatment_offset`` while treated. The true ATT equals
    ``treatment_offset``.
    """
    units = ("BROOKLYN 01", "MANHATTAN 03")
    periods = ("2024-01", "2024-02", "2024-03", "2024-04")

    event = TreatmentEvent(
        name="pilot",
        description="synthetic pilot",
        treated_units=("MANHATTAN 03",),
        treatment_date=date(2024, 3, 1),
        geography="community_district",
    )

    observations: list[PanelObservation] = []
    for u in units:
        for i, p in enumerate(periods):
            is_treated = u == "MANHATTAN 03" and i >= 2
            n = int(baseline + (treatment_offset if is_treated else 0))
            observations.append(
                PanelObservation(
                    unit_id=u,
                    period=p,
                    complaint_count=n,
                    complaint_counts_by_type={"Rodent": n},
                    resolution_rate=0.9,
                    median_resolution_days=7.0,
                    treatment=is_treated,
                    treatment_date=date(2024, 3, 1) if u == "MANHATTAN 03" else None,
                    population=100_000,
                )
            )

    return PanelDataset(
        observations=tuple(observations),
        unit_type="community_district",
        periods=periods,
        treatment_events=(event,),
    )


# ---------------------------------------------------------------------------
# Adapter tests
# ---------------------------------------------------------------------------


def test_panel_dataset_to_factor_factory_builds_a_valid_panel() -> None:
    dataset = _make_synthetic_panel()

    panel = panel_dataset_to_factor_factory(dataset)

    assert panel.outcome_col == "complaint_count"
    assert set(panel.unit_ids) == {"BROOKLYN 01", "MANHATTAN 03"}
    summary = panel.summary()
    assert summary["n_units"] == 2
    assert summary["n_periods"] == 4
    assert summary["dimension"] == "community_district"
    assert summary["n_treatment_events"] == 1
    assert tuple(summary["treatment_event_names"]) == ("pilot",)


def test_panel_method_is_equivalent_to_the_function() -> None:
    dataset = _make_synthetic_panel()

    via_method = dataset.to_factor_factory_panel()
    via_func = panel_dataset_to_factor_factory(dataset)

    assert via_method.summary() == via_func.summary()
    pd.testing.assert_frame_equal(via_method.df, via_func.df)


def test_spatial_weights_roundtrip_via_df_attrs() -> None:
    dataset = _make_synthetic_panel()
    weights = {
        "BROOKLYN 01": {"MANHATTAN 03": 1.0},
        "MANHATTAN 03": {"BROOKLYN 01": 1.0},
    }

    panel = panel_dataset_to_factor_factory(dataset, spatial_weights=weights)
    recovered = spatial_weights_from_panel(panel)

    assert recovered == weights


def test_spatial_weights_from_panel_returns_none_when_absent() -> None:
    dataset = _make_synthetic_panel()

    panel = panel_dataset_to_factor_factory(dataset)

    assert spatial_weights_from_panel(panel) is None


def test_empty_dataset_raises_valueerror() -> None:
    empty = PanelDataset(
        observations=(),
        unit_type="community_district",
        periods=(),
    )

    with pytest.raises(ValueError, match="Cannot convert an empty"):
        panel_dataset_to_factor_factory(empty)


def test_unknown_outcome_col_raises_valueerror() -> None:
    dataset = _make_synthetic_panel()

    with pytest.raises(ValueError, match="outcome_col="):
        panel_dataset_to_factor_factory(dataset, outcome_col="not_a_column")


# ---------------------------------------------------------------------------
# Engine smoke test (DiD / TWFE)
# ---------------------------------------------------------------------------


def test_did_twfe_recovers_synthetic_att() -> None:
    """TWFE on the 2x4 panel should recover ATT ≈ treatment_offset."""
    dataset = _make_synthetic_panel(treatment_offset=-5.0)
    panel = dataset.to_factor_factory_panel()

    from factor_factory.engines.did import estimate as did_estimate

    results = did_estimate(panel, methods=("twfe",), outcome="complaint_count")

    assert len(results) == 1
    assert results[0].method == "twfe"
    assert results[0].att == pytest.approx(-5.0, abs=1e-6)


def test_pipeline_as_factor_factory_estimate_dispatches_to_did() -> None:
    dataset = _make_synthetic_panel(treatment_offset=-5.0)
    panel = dataset.to_factor_factory_panel()

    pipeline = Pipeline()
    results = pipeline.as_factor_factory_estimate(
        panel,
        family="did",
        method="twfe",
        outcome="complaint_count",
    )

    assert results[0].method == "twfe"
    assert results[0].att == pytest.approx(-5.0, abs=1e-6)


def test_pipeline_bridge_rejects_unknown_family() -> None:
    dataset = _make_synthetic_panel()
    panel = dataset.to_factor_factory_panel()

    with pytest.raises(ValueError, match="Unknown factor-factory engine family"):
        Pipeline().as_factor_factory_estimate(panel, family="not_a_family")
