"""Tests for the statistical modeling module.

Tests that depend on optional packages (statsmodels, ruptures, esda,
linearmodels) are marked ``@pytest.mark.optional``.
"""

from __future__ import annotations

from datetime import date

import pytest

from nyc311.stats import (
    ChangepointResult,
    DecompositionResult,
    ITSResult,
    LISAResult,
    MoranResult,
    PanelRegressionResult,
)

# ---------------------------------------------------------------------------
# Model dataclass construction
# ---------------------------------------------------------------------------


class TestResultDataclasses:
    def test_its_result(self) -> None:
        r = ITSResult(
            pre_trend=0.5,
            post_trend=0.2,
            level_change=-10.0,
            trend_change=-0.3,
            p_value_level=0.01,
            p_value_trend=0.05,
            model_summary="summary",
        )
        assert r.level_change == -10.0

    def test_changepoint_result(self) -> None:
        r = ChangepointResult(
            breakpoints=(30,),
            breakpoint_dates=(date(2024, 3, 1),),
            n_segments=2,
            penalty=1.5,
        )
        assert r.n_segments == 2

    def test_decomposition_result(self) -> None:
        r = DecompositionResult(trend=None, seasonal=None, residual=None, period=12)
        assert r.period == 12

    def test_moran_result(self) -> None:
        r = MoranResult(statistic=0.3, p_value=0.01, z_score=2.5, expected=-0.02)
        assert r.statistic == 0.3

    def test_lisa_result(self) -> None:
        r = LISAResult(
            local_statistic=(0.5, -0.3),
            p_values=(0.01, 0.8),
            cluster_labels=("HH", "ns"),
            unit_ids=("A", "B"),
        )
        assert r.cluster_labels == ("HH", "ns")

    def test_panel_regression_result(self) -> None:
        r = PanelRegressionResult(
            method="entity_fe",
            coefficients={"x1": 0.5},
            std_errors={"x1": 0.1},
            p_values={"x1": 0.001},
            r_squared=0.7,
            n_observations=100,
            n_entities=10,
            n_periods=10,
            model_summary="summary",
        )
        assert r.method == "entity_fe"


# ---------------------------------------------------------------------------
# Interrupted Time Series
# ---------------------------------------------------------------------------


@pytest.mark.optional
class TestInterruptedTimeSeries:
    def test_basic_its(self) -> None:
        import numpy as np
        import pandas as pd

        from nyc311.stats import interrupted_time_series

        # Simulate a series with a clear level shift at the intervention point
        rng = np.random.default_rng(42)
        dates = pd.date_range("2023-01-01", periods=60, freq="ME")
        pre = 50 + 0.5 * np.arange(30) + rng.normal(0, 2, 30)
        post = 30 + 0.5 * np.arange(30, 60) + rng.normal(0, 2, 30)
        series = pd.Series(np.concatenate([pre, post]), index=dates)

        result = interrupted_time_series(series, date(2025, 7, 1))
        assert isinstance(result, ITSResult)
        # Level change should be significantly negative
        assert result.level_change < 0


# ---------------------------------------------------------------------------
# Changepoint Detection
# ---------------------------------------------------------------------------


@pytest.mark.optional
class TestChangepointDetection:
    def test_single_changepoint(self) -> None:
        import numpy as np
        import pandas as pd

        from nyc311.stats import detect_changepoints

        rng = np.random.default_rng(42)
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        signal = np.concatenate(
            [
                rng.normal(50, 5, 50),
                rng.normal(80, 5, 50),
            ]
        )
        series = pd.Series(signal, index=dates)

        result = detect_changepoints(series, method="pelt")
        assert isinstance(result, ChangepointResult)
        assert result.n_segments >= 2
        # The breakpoint should be near index 50
        assert any(40 <= bp <= 60 for bp in result.breakpoints)


# ---------------------------------------------------------------------------
# Seasonal Decomposition
# ---------------------------------------------------------------------------


@pytest.mark.optional
class TestSeasonalDecomposition:
    def test_monthly_decomposition(self) -> None:
        import numpy as np
        import pandas as pd

        from nyc311.stats import seasonal_decompose

        dates = pd.date_range("2020-01-01", periods=48, freq="ME")
        seasonal_component = 10 * np.sin(2 * np.pi * np.arange(48) / 12)
        trend_component = np.linspace(100, 120, 48)
        series = pd.Series(trend_component + seasonal_component, index=dates)

        result = seasonal_decompose(series, period=12)
        assert isinstance(result, DecompositionResult)
        assert result.period == 12
        assert len(result.trend.dropna()) > 0


# ---------------------------------------------------------------------------
# Panel regressions
# ---------------------------------------------------------------------------


def _synthetic_panel_dataset():
    """Build a small balanced panel where the outcome depends on a regressor."""
    import numpy as np

    from nyc311.temporal import PanelDataset, PanelObservation

    rng = np.random.default_rng(0)
    units = [f"U{i:02d}" for i in range(8)]
    periods = [f"2024-{m:02d}" for m in range(1, 13)]

    observations: list[PanelObservation] = []
    for unit in units:
        unit_effect = float(rng.normal(0, 1))
        for p_idx, period in enumerate(periods):
            resolution_rate = float(rng.uniform(0.4, 0.9))
            # outcome = constant + 50*resolution_rate + unit FE + noise
            count = round(
                100.0
                + 50.0 * resolution_rate
                + 5.0 * unit_effect
                + 0.5 * p_idx
                + rng.normal(0, 2)
            )
            observations.append(
                PanelObservation(
                    unit_id=unit,
                    period=period,
                    complaint_count=count,
                    complaint_counts_by_type={},
                    resolution_rate=resolution_rate,
                    median_resolution_days=10.0,
                    treatment=False,
                    treatment_date=None,
                    population=10_000,
                )
            )

    return PanelDataset(
        observations=tuple(observations),
        unit_type="community_district",
        periods=tuple(periods),
    )


@pytest.mark.optional
class TestPanelFixedEffects:
    def test_recovers_known_coefficient(self) -> None:
        pytest.importorskip("linearmodels")

        from nyc311.stats import panel_fixed_effects

        panel = _synthetic_panel_dataset()
        result = panel_fixed_effects(
            panel,
            outcome="complaint_count",
            regressors=("resolution_rate",),
        )

        assert isinstance(result, PanelRegressionResult)
        assert result.method == "entity_fe"
        assert "resolution_rate" in result.coefficients
        # True effect is +50; allow generous tolerance
        assert 30.0 < result.coefficients["resolution_rate"] < 70.0
        assert result.n_observations == 8 * 12
        assert result.n_entities == 8
        assert result.n_periods == 12

    def test_two_way_fe(self) -> None:
        pytest.importorskip("linearmodels")

        from nyc311.stats import panel_fixed_effects

        panel = _synthetic_panel_dataset()
        result = panel_fixed_effects(
            panel,
            outcome="complaint_count",
            regressors=("resolution_rate",),
            time_effects=True,
        )
        assert result.method == "two_way_fe"

    def test_missing_outcome_raises(self) -> None:
        pytest.importorskip("linearmodels")

        from nyc311.stats import panel_fixed_effects

        panel = _synthetic_panel_dataset()
        with pytest.raises(ValueError, match="Missing columns"):
            panel_fixed_effects(
                panel,
                outcome="not_a_real_column",
                regressors=("resolution_rate",),
            )


@pytest.mark.optional
class TestPanelRandomEffects:
    def test_random_effects_returns_result(self) -> None:
        pytest.importorskip("linearmodels")

        from nyc311.stats import panel_random_effects

        panel = _synthetic_panel_dataset()
        result = panel_random_effects(
            panel,
            outcome="complaint_count",
            regressors=("resolution_rate",),
        )

        assert isinstance(result, PanelRegressionResult)
        assert result.method == "random_effects"
        assert "resolution_rate" in result.coefficients
        assert result.r_squared >= 0.0


# ---------------------------------------------------------------------------
# Spatial autocorrelation
# ---------------------------------------------------------------------------


def _grid_weights(rows: int, cols: int) -> dict[str, dict[str, float]]:
    """Build row-standardized rook-contiguity weights for a rows x cols grid."""
    units = [f"{r}_{c}" for r in range(rows) for c in range(cols)]
    raw: dict[str, dict[str, float]] = {u: {} for u in units}

    def _add(a: str, b: str) -> None:
        raw[a][b] = 1.0
        raw[b][a] = 1.0

    for r in range(rows):
        for c in range(cols):
            uid = f"{r}_{c}"
            if c + 1 < cols:
                _add(uid, f"{r}_{c + 1}")
            if r + 1 < rows:
                _add(uid, f"{r + 1}_{c}")

    for u in units:
        total = sum(raw[u].values())
        if total > 0:
            raw[u] = {nb: w / total for nb, w in raw[u].items()}
    return raw


@pytest.mark.optional
class TestGlobalMoransI:
    def test_clustered_values_have_positive_moran(self) -> None:
        pytest.importorskip("esda")
        pytest.importorskip("libpysal")

        from nyc311.stats import global_morans_i

        rows = cols = 6
        weights = _grid_weights(rows, cols)
        # Top half = high, bottom half = low → strong positive autocorrelation
        values = {
            f"{r}_{c}": (10.0 if r < rows // 2 else 1.0)
            for r in range(rows)
            for c in range(cols)
        }

        result = global_morans_i(values, weights)
        assert isinstance(result, MoranResult)
        assert result.statistic > 0.5
        assert -1.0 <= result.statistic <= 1.0

    def test_random_values_have_near_zero_moran(self) -> None:
        pytest.importorskip("esda")
        pytest.importorskip("libpysal")

        import numpy as np

        from nyc311.stats import global_morans_i

        rows = cols = 6
        weights = _grid_weights(rows, cols)
        rng = np.random.default_rng(123)
        values = {
            f"{r}_{c}": float(rng.normal())
            for r in range(rows)
            for c in range(cols)
        }
        result = global_morans_i(values, weights)
        assert abs(result.statistic) < 0.4


@pytest.mark.optional
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestLocalMoransI:
    def test_lisa_returns_one_label_per_unit(self) -> None:
        pytest.importorskip("esda")
        pytest.importorskip("libpysal")

        from nyc311.stats import local_morans_i

        rows = cols = 5
        weights = _grid_weights(rows, cols)
        values = {
            f"{r}_{c}": (10.0 if r < rows // 2 else 1.0)
            for r in range(rows)
            for c in range(cols)
        }
        result = local_morans_i(values, weights, permutations=199)

        assert isinstance(result, LISAResult)
        n = rows * cols
        assert len(result.local_statistic) == n
        assert len(result.p_values) == n
        assert len(result.cluster_labels) == n
        assert len(result.unit_ids) == n
        # Every label is one of the documented categories
        allowed = {"HH", "HL", "LH", "LL", "ns"}
        assert set(result.cluster_labels) <= allowed
