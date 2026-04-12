"""Tests for spatial regression and GWR methods."""

from __future__ import annotations

import pytest

from nyc311.stats import GWRResult, SpatialErrorResult, SpatialLagResult


class TestSpatialRegressionDataclasses:
    def test_spatial_lag_result(self) -> None:
        r = SpatialLagResult(
            coefficients={"CONSTANT": 1.0, "x1": 0.5},
            std_errors={"CONSTANT": 0.1, "x1": 0.05},
            p_values={"CONSTANT": 0.0, "x1": 0.01},
            rho=0.3,
            rho_p_value=0.001,
            log_likelihood=-50.0,
            aic=106.0,
            n_observations=50,
            model_summary="summary",
        )
        assert r.rho == 0.3

    def test_spatial_error_result(self) -> None:
        r = SpatialErrorResult(
            coefficients={"CONSTANT": 1.0},
            std_errors={"CONSTANT": 0.1},
            p_values={"CONSTANT": 0.0},
            lam=0.4,
            lam_p_value=0.01,
            log_likelihood=-50.0,
            aic=104.0,
            n_observations=50,
            model_summary="summary",
        )
        assert r.lam == 0.4

    def test_gwr_result(self) -> None:
        r = GWRResult(
            local_coefficients={"CONSTANT": (1.0, 1.1), "x": (0.5, 0.6)},
            local_r_squared=(0.8, 0.7),
            bandwidth=1000.0,
            aic=100.0,
            unit_ids=("A", "B"),
            global_r_squared=0.75,
            n_observations=2,
            model_summary="summary",
        )
        assert r.bandwidth == 1000.0


@pytest.mark.optional
class TestGWR:
    def test_gwr_basic(self) -> None:
        import numpy as np

        rng = np.random.default_rng(42)
        n = 20
        unit_ids = [f"unit_{i}" for i in range(n)]
        coords = {
            uid: (40.7 + rng.uniform(-0.1, 0.1), -74.0 + rng.uniform(-0.1, 0.1))
            for uid in unit_ids
        }
        x_vals = {uid: rng.uniform(0, 10) for uid in unit_ids}
        regressors = {uid: {"income": x_vals[uid]} for uid in unit_ids}
        values = {uid: 2.0 * x_vals[uid] + rng.normal(0, 1) for uid in unit_ids}

        from nyc311.stats import geographically_weighted_regression

        result = geographically_weighted_regression(
            values=values,
            regressors=regressors,
            coordinates=coords,
        )
        assert isinstance(result, GWRResult)
        assert result.n_observations == n
        assert len(result.local_r_squared) == n
        assert "income" in result.local_coefficients

    def test_gwr_too_few_observations(self) -> None:
        from nyc311.stats import geographically_weighted_regression

        with pytest.raises(ValueError, match="at least 5"):
            geographically_weighted_regression(
                values={"A": 1.0, "B": 2.0},
                regressors={"A": {"x": 1.0}, "B": {"x": 2.0}},
                coordinates={"A": (40.7, -74.0), "B": (40.8, -74.1)},
            )
