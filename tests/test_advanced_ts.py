"""Tests for anomaly detection and power analysis."""

from __future__ import annotations

import pytest

from nyc311.stats import PowerResult, STLAnomalyResult


class TestAdvancedTSDataclasses:
    def test_anomaly_result(self) -> None:
        r = STLAnomalyResult(
            anomaly_dates=(),
            anomaly_scores=(),
            threshold=2.0,
            n_anomalies=0,
            residual_mean=0.0,
            residual_std=1.0,
        )
        assert r.threshold == 2.0

    def test_power_result(self) -> None:
        r = PowerResult(
            mde=0.5,
            alpha=0.05,
            power=0.80,
            n_units=50,
            n_periods=12,
            icc=0.05,
            variance_explained=0.0,
        )
        assert r.mde == 0.5


@pytest.mark.optional
class TestSTLAnomalyDetection:
    def test_detects_injected_anomaly(self) -> None:
        import numpy as np
        import pandas as pd

        from nyc311.stats import detect_stl_anomalies

        rng = np.random.default_rng(42)
        dates = pd.date_range("2020-01-01", periods=60, freq="MS")
        seasonal = 5.0 * np.sin(2 * np.pi * np.arange(60) / 12)
        trend = np.linspace(100, 120, 60)
        noise = rng.normal(0, 1, 60)
        values = trend + seasonal + noise

        values[30] += 20.0  # inject anomaly

        series = pd.Series(values, index=dates)
        result = detect_stl_anomalies(series, threshold=2.0)

        assert isinstance(result, STLAnomalyResult)
        assert result.n_anomalies > 0
        assert result.residual_std > 0

    def test_no_anomalies_in_clean_data(self) -> None:
        import numpy as np
        import pandas as pd

        from nyc311.stats import detect_stl_anomalies

        dates = pd.date_range("2020-01-01", periods=48, freq="MS")
        values = 100 + 5.0 * np.sin(2 * np.pi * np.arange(48) / 12)
        series = pd.Series(values, index=dates)

        result = detect_stl_anomalies(series, threshold=5.0)
        assert result.n_anomalies == 0


@pytest.mark.optional
class TestPowerAnalysis:
    def test_mde_decreases_with_more_units(self) -> None:
        from nyc311.stats import minimum_detectable_effect

        small = minimum_detectable_effect(n_units=10, n_periods=12)
        large = minimum_detectable_effect(n_units=100, n_periods=12)
        assert large.mde < small.mde

    def test_mde_increases_with_icc(self) -> None:
        from nyc311.stats import minimum_detectable_effect

        low_icc = minimum_detectable_effect(n_units=50, n_periods=12, icc=0.01)
        high_icc = minimum_detectable_effect(n_units=50, n_periods=12, icc=0.20)
        assert high_icc.mde > low_icc.mde

    def test_invalid_params(self) -> None:
        from nyc311.stats import minimum_detectable_effect

        with pytest.raises(ValueError, match="n_units"):
            minimum_detectable_effect(n_units=1, n_periods=12)
        with pytest.raises(ValueError, match="n_periods"):
            minimum_detectable_effect(n_units=10, n_periods=0)
