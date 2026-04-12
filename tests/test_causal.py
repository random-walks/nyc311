"""Tests for causal inference methods (synthetic control, DiD, RDD, event study)."""

from __future__ import annotations

from datetime import date

import pytest

from nyc311.stats import (
    EventStudyResult,
    GroupTimeATT,
    RDResult,
    StaggeredDiDResult,
    SyntheticControlResult,
)

# ---------------------------------------------------------------------------
# Dataclass construction
# ---------------------------------------------------------------------------


class TestCausalDataclasses:
    def test_synthetic_control_result(self) -> None:
        r = SyntheticControlResult(
            treated_unit="A",
            donor_weights={"B": 0.6, "C": 0.4},
            counterfactual=(1.0, 2.0),
            observed=(1.5, 3.0),
            treatment_effect=(0.5, 1.0),
            att=0.75,
            periods=("2024-01", "2024-02"),
            pre_treatment_mspe=0.01,
            placebo_p_value=None,
            model_summary="summary",
        )
        assert r.att == 0.75

    def test_staggered_did_result(self) -> None:
        r = StaggeredDiDResult(
            group_time_atts=(
                GroupTimeATT(
                    group="2024-01", period="2024-03", att=1.0, se=0.5, p_value=0.05
                ),
            ),
            aggregated_att=1.0,
            aggregated_se=0.5,
            aggregated_p_value=0.05,
            aggregated_ci_lower=0.0,
            aggregated_ci_upper=2.0,
            n_groups=1,
            n_periods=6,
            model_summary="summary",
        )
        assert r.aggregated_att == 1.0

    def test_event_study_result(self) -> None:
        r = EventStudyResult(
            coefficients=(0.0, 0.1, 0.5),
            std_errors=(0.01, 0.02, 0.03),
            ci_lower=(-0.02, 0.06, 0.44),
            ci_upper=(0.02, 0.14, 0.56),
            relative_periods=(-1, 0, 1),
            pre_trend_f_statistic=0.5,
            pre_trend_p_value=0.6,
            reference_period=-1,
        )
        assert r.reference_period == -1

    def test_rd_result(self) -> None:
        r = RDResult(
            treatment_effect=2.5,
            se_robust=0.5,
            p_value=0.001,
            ci_lower=1.5,
            ci_upper=3.5,
            bandwidth_left=1.0,
            bandwidth_right=1.0,
            n_effective_left=50,
            n_effective_right=50,
            kernel="triangular",
            model_summary="summary",
        )
        assert r.treatment_effect == 2.5


# ---------------------------------------------------------------------------
# Functional tests
# ---------------------------------------------------------------------------


def _build_panel_with_treatment():
    """Build a simple panel with staggered treatment for testing."""
    from nyc311.temporal._models import PanelDataset, PanelObservation, TreatmentEvent

    treatment = TreatmentEvent(
        name="test_policy",
        description="Test",
        treated_units=("UNIT_A",),
        treatment_date=date(2024, 4, 1),
        geography="test",
    )

    observations = []
    units = ["UNIT_A", "UNIT_B", "UNIT_C", "UNIT_D"]
    periods = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]

    for unit in units:
        for i, period in enumerate(periods):
            is_treated = unit == "UNIT_A" and i >= 3
            base = 10.0
            effect = 5.0 if is_treated else 0.0
            observations.append(
                PanelObservation(
                    unit_id=unit,
                    period=period,
                    complaint_count=int(base + effect + i),
                    complaint_counts_by_type={"Noise": int(base + effect + i)},
                    resolution_rate=0.8,
                    median_resolution_days=5.0,
                    treatment=is_treated,
                    treatment_date=date(2024, 4, 1) if unit == "UNIT_A" else None,
                    population=10000,
                    covariates=None,
                )
            )

    return PanelDataset(
        observations=tuple(observations),
        unit_type="test",
        periods=tuple(periods),
        treatment_events=(treatment,),
    )


@pytest.mark.optional
class TestSyntheticControl:
    def test_basic_synthetic_control(self) -> None:
        panel = _build_panel_with_treatment()
        result = pytest.importorskip("nyc311.stats").synthetic_control(
            panel,
            treated_unit="UNIT_A",
            outcome="complaint_count",
        )
        assert isinstance(result, SyntheticControlResult)
        assert result.treated_unit == "UNIT_A"
        assert len(result.donor_weights) > 0
        assert result.att > 0  # treatment increased complaints

    def test_donor_weights_bounded(self) -> None:
        panel = _build_panel_with_treatment()
        result = pytest.importorskip("nyc311.stats").synthetic_control(
            panel,
            treated_unit="UNIT_A",
            outcome="complaint_count",
        )
        for w in result.donor_weights.values():
            assert 0.0 <= w <= 1.0

    def test_invalid_treated_unit(self) -> None:
        panel = _build_panel_with_treatment()
        with pytest.raises(ValueError, match="not found"):
            pytest.importorskip("nyc311.stats").synthetic_control(
                panel, treated_unit="NONEXISTENT", outcome="complaint_count"
            )


@pytest.mark.optional
class TestStaggeredDiD:
    def test_basic_staggered_did(self) -> None:
        panel = _build_panel_with_treatment()
        result = pytest.importorskip("nyc311.stats").staggered_did(
            panel, outcome="complaint_count"
        )
        assert isinstance(result, StaggeredDiDResult)
        assert result.n_groups >= 1
        assert len(result.group_time_atts) > 0

    def test_no_treatment_events(self) -> None:
        from nyc311.temporal._models import PanelDataset

        empty = PanelDataset(observations=(), unit_type="test", periods=())
        with pytest.raises(ValueError, match="treatment event"):
            pytest.importorskip("nyc311.stats").staggered_did(
                empty, outcome="complaint_count"
            )


@pytest.mark.optional
class TestEventStudy:
    def test_event_study_coefficients(self) -> None:
        panel = _build_panel_with_treatment()
        result = pytest.importorskip("nyc311.stats").event_study(
            panel,
            outcome="complaint_count",
            pre_periods=2,
            post_periods=2,
        )
        assert isinstance(result, EventStudyResult)
        assert len(result.coefficients) == len(result.relative_periods)
        assert result.reference_period == -1


@pytest.mark.optional
class TestRDD:
    def test_sharp_rd_with_known_jump(self) -> None:
        import numpy as np

        rng = np.random.default_rng(42)
        n = 200
        x = rng.uniform(-2, 2, n)
        y = np.where(x >= 0, 5.0, 0.0) + rng.normal(0, 0.5, n)

        result = pytest.importorskip("nyc311.stats").regression_discontinuity(
            x, y, cutoff=0.0
        )
        assert isinstance(result, RDResult)
        assert abs(result.treatment_effect - 5.0) < 2.0  # within tolerance
        assert result.p_value < 0.05

    def test_rd_insufficient_data(self) -> None:
        import numpy as np

        with pytest.raises(ValueError, match="at least 3"):
            pytest.importorskip("nyc311.stats").regression_discontinuity(
                np.array([1.0, 2.0]), np.array([1.0, 2.0])
            )
