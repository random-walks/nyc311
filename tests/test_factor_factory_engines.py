"""Parity smoke tests for factor-factory engines on nyc311 PanelDatasets.

For each module in :mod:`nyc311.stats` that has a confirmed
factor-factory equivalent, we exercise the factor-factory engine on a
PanelDataset converted through the adapter. These are deliberately
thin: we are not re-verifying the engine math (factor-factory owns
that), only checking that the adapter hands the engine a Panel the
engine accepts.

Coverage map (nyc311.stats → factor_factory.engines):

- ``_staggered_did`` → ``engines.did.{twfe,cs,sa,bjs}``
- ``_synthetic_control`` → ``engines.scm.{pysyncon,augmented,matrix_completion}``
- ``_changepoint`` → ``engines.changepoint.ruptures``
- ``_decomposition`` → ``engines.stl.sktime_stl``
- ``_spatial`` → ``engines.spatial.morans_i``
- ``_panel_models`` → ``engines.panel_reg.pyfixest``
- ``_equity.theil_index`` → ``engines.inequality.theil_t``

Modules with no factor-factory equivalent (``_bym2``, ``_gwr``,
``_equity.oaxaca_blinder``, ``_power``, ``_spatial_regression``) are
not covered here.
"""

from __future__ import annotations

import pytest

pd = pytest.importorskip("pandas")
ff = pytest.importorskip("factor_factory")

from nyc311.temporal import (  # noqa: E402
    PanelDataset,
    PanelObservation,
    TreatmentEvent,
)

pytestmark = pytest.mark.optional


# ---------------------------------------------------------------------------
# Fixture: a small balanced panel with a known treatment effect.
# ---------------------------------------------------------------------------


def _build_panel(
    *,
    n_units: int = 6,
    n_periods: int = 24,
    treated_unit_id: str = "U0",
    treatment_period_idx: int = 12,
    att: float = -5.0,
    baseline: float = 50.0,
) -> PanelDataset:
    """A balanced panel with one treated unit whose post-period outcome falls by ``att``."""
    units = tuple(f"U{i}" for i in range(n_units))
    start = pd.Timestamp("2024-01-01")
    periods = tuple(
        str((start + pd.offsets.MonthBegin(i)).to_period("M")) for i in range(n_periods)
    )

    event = TreatmentEvent(
        name="pilot",
        description="synthetic pilot",
        treated_units=(treated_unit_id,),
        treatment_date=(
            pd.Timestamp(periods[treatment_period_idx])
            .to_period("M")
            .to_timestamp()
            .date()
        ),
        geography="community_district",
    )

    observations: list[PanelObservation] = []
    for u_idx, u in enumerate(units):
        for i, p in enumerate(periods):
            is_treated = u == treated_unit_id and i >= treatment_period_idx
            # light per-unit fixed effect + period trend so scm/did have signal
            n = int(baseline + u_idx * 1.5 + i * 0.2 + (att if is_treated else 0.0))
            observations.append(
                PanelObservation(
                    unit_id=u,
                    period=p,
                    complaint_count=n,
                    complaint_counts_by_type={"Rodent": n},
                    resolution_rate=0.9,
                    median_resolution_days=7.0,
                    treatment=is_treated,
                    treatment_date=event.treatment_date
                    if u == treated_unit_id
                    else None,
                    population=100_000,
                )
            )

    return PanelDataset(
        observations=tuple(observations),
        unit_type="community_district",
        periods=periods,
        treatment_events=(event,),
    )


@pytest.fixture
def nyc_panel() -> PanelDataset:
    return _build_panel()


# ---------------------------------------------------------------------------
# DiD family (engines.did.{twfe,cs,sa,bjs})
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("method", ["twfe", "cs", "sa", "bjs"])
def test_engines_did_accepts_adapter_panel(
    nyc_panel: PanelDataset, method: str
) -> None:
    panel = nyc_panel.to_factor_factory_panel()
    from factor_factory.engines.did import estimate as did_estimate

    results = did_estimate(panel, methods=(method,), outcome="complaint_count")

    assert len(results) == 1
    assert results[0].method == method
    # The treated-minus-control gap is roughly -5.
    assert results[0].att < 0
    assert abs(results[0].att + 5.0) < 2.0


# ---------------------------------------------------------------------------
# Panel regression (engines.panel_reg.pyfixest)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    reason=(
        "factor-factory 1.0.2's panel_reg.pyfixest adapter references a "
        "'Coefficient' column that current pyfixest (>=0.50) no longer "
        "emits. Tracked upstream; the adapter path is correct on the "
        "nyc311 side."
    ),
    strict=False,
)
def test_engines_panel_reg_pyfixest_accepts_adapter_panel(
    nyc_panel: PanelDataset,
) -> None:
    panel = nyc_panel.to_factor_factory_panel()
    from factor_factory.engines.panel_reg import estimate as panel_reg_estimate

    results = panel_reg_estimate(
        panel,
        methods=("pyfixest",),
        outcome="complaint_count",
        regressors=("treatment",),
        fixed_effects=("unit_id", "period"),
    )

    assert len(results) == 1


# ---------------------------------------------------------------------------
# SCM (engines.scm.augmented)
# ---------------------------------------------------------------------------


def test_engines_scm_augmented_accepts_adapter_panel(
    nyc_panel: PanelDataset,
) -> None:
    panel = nyc_panel.to_factor_factory_panel()
    from factor_factory.engines.scm import estimate as scm_estimate

    results = scm_estimate(panel, methods=("augmented",), outcome="complaint_count")

    records = results.to_records()
    assert len(records) == 1
    assert records[0]["method"] == "augmented"


# ---------------------------------------------------------------------------
# Changepoint (engines.changepoint.ruptures)
# ---------------------------------------------------------------------------


def test_engines_changepoint_ruptures_accepts_adapter_panel(
    nyc_panel: PanelDataset,
) -> None:
    panel = nyc_panel.to_factor_factory_panel()
    from factor_factory.engines.changepoint import estimate as cp_estimate

    results = cp_estimate(panel, methods=("ruptures",), outcome="complaint_count")

    assert len(results.to_records()) == 1


# ---------------------------------------------------------------------------
# STL (engines.stl.sktime_stl)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    reason=(
        "factor-factory 1.0.2's stl.sktime_stl adapter reads freq from "
        "the DataFrame index, but pandas MultiIndex levels do not "
        "preserve a DatetimeIndex.freq attribute across set_index / "
        "sort_index. Workaround upstream is to fall back on "
        "panel.metadata.freq. The adapter path (PanelDataset → Panel) "
        "is correct."
    ),
    strict=False,
)
def test_engines_stl_sktime_accepts_adapter_panel(
    nyc_panel: PanelDataset,
) -> None:
    panel = nyc_panel.to_factor_factory_panel()
    from factor_factory.engines.stl import estimate as stl_estimate

    results = stl_estimate(
        panel,
        methods=("sktime_stl",),
        outcome="complaint_count",
        seasonal_period=12,
    )

    assert len(results.to_records()) == 1


# ---------------------------------------------------------------------------
# Inequality (engines.inequality.theil_t)
# ---------------------------------------------------------------------------


def test_engines_inequality_theil_t_accepts_adapter_panel(
    nyc_panel: PanelDataset,
) -> None:
    panel = nyc_panel.to_factor_factory_panel()
    from factor_factory.engines.inequality import estimate as ineq_estimate

    # Use the treatment flag as a group column — rough but exercises the adapter.
    results = ineq_estimate(
        panel,
        methods=("theil_t",),
        outcome="complaint_count",
        group_col="treatment",
    )

    assert len(results.to_records()) == 1


# ---------------------------------------------------------------------------
# SDID (engines.sdid.sdid) — exercised in detail in examples/sdid-multi-borough-policy/.
# ---------------------------------------------------------------------------


def test_engines_sdid_accepts_adapter_panel(
    nyc_panel: PanelDataset,
) -> None:
    panel = nyc_panel.to_factor_factory_panel()
    from factor_factory.engines.sdid import estimate as sdid_estimate

    results = sdid_estimate(panel, methods=("sdid",), outcome="complaint_count")

    records = results.to_records()
    assert len(records) == 1
    assert records[0]["method"] == "sdid"
