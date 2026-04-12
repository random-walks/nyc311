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
