"""Tests for equity, reporting bias, and inequality methods."""

from __future__ import annotations

import pytest

from nyc311.stats import (
    LatentReportingResult,
    OaxacaBlinderResult,
    TheilResult,
)


class TestEquityDataclasses:
    def test_oaxaca_blinder_result(self) -> None:
        r = OaxacaBlinderResult(
            mean_group_a=10.0,
            mean_group_b=8.0,
            total_gap=2.0,
            explained=1.5,
            unexplained=0.5,
            component_contributions={"income": 1.0, "density": 0.5},
            n_group_a=50,
            n_group_b=50,
        )
        assert r.total_gap == 2.0

    def test_theil_result(self) -> None:
        r = TheilResult(
            total=0.15,
            between_group=0.10,
            within_group=0.05,
            unit_contributions={"A": 0.08, "B": 0.07},
            n_units=2,
        )
        assert r.total == 0.15

    def test_latent_reporting_result(self) -> None:
        r = LatentReportingResult(
            estimated_true_rates={"A": 0.01},
            reporting_probabilities={"A": 0.5},
            observed_rates={"A": 0.005},
            n_iterations=50,
            converged=True,
            log_likelihood_trace=(-100.0, -90.0),
        )
        assert r.converged


@pytest.mark.optional
class TestOaxacaBlinder:
    def test_decomposition_sums_to_gap(self) -> None:
        import numpy as np

        rng = np.random.default_rng(42)
        n = 50
        income_a = rng.normal(60, 10, n)
        income_b = rng.normal(40, 10, n)
        outcome_a = 2.0 * income_a + rng.normal(0, 5, n)
        outcome_b = 1.5 * income_b + rng.normal(0, 5, n)

        import pandas as pd

        df_a = pd.DataFrame({"outcome": outcome_a, "income": income_a})
        df_b = pd.DataFrame({"outcome": outcome_b, "income": income_b})

        from nyc311.stats import oaxaca_blinder_decomposition

        result = oaxaca_blinder_decomposition(df_a, df_b, "outcome", ("income",))
        assert isinstance(result, OaxacaBlinderResult)
        assert abs(result.explained + result.unexplained - result.total_gap) < 0.01

    def test_too_few_observations(self) -> None:
        import pandas as pd

        from nyc311.stats import oaxaca_blinder_decomposition

        with pytest.raises(ValueError, match="at least 2"):
            oaxaca_blinder_decomposition(
                pd.DataFrame({"y": [1.0], "x": [1.0]}),
                pd.DataFrame({"y": [2.0], "x": [2.0]}),
                "y",
                ("x",),
            )


@pytest.mark.optional
class TestTheilIndex:
    def test_perfect_equality(self) -> None:
        from nyc311.stats import theil_index

        result = theil_index(
            values={"A": 10.0, "B": 10.0, "C": 10.0},
            populations={"A": 100, "B": 100, "C": 100},
        )
        assert result.total == pytest.approx(0.0, abs=1e-10)

    def test_with_group_decomposition(self) -> None:
        from nyc311.stats import theil_index

        result = theil_index(
            values={"A": 20.0, "B": 5.0, "C": 15.0, "D": 10.0},
            populations={"A": 100, "B": 100, "C": 100, "D": 100},
            groups={"A": "high", "B": "low", "C": "high", "D": "low"},
        )
        assert isinstance(result, TheilResult)
        assert result.total > 0.0
        assert result.between_group >= 0.0

    def test_mismatched_keys(self) -> None:
        from nyc311.stats import theil_index

        with pytest.raises(ValueError, match="same keys"):
            theil_index(
                values={"A": 10.0},
                populations={"B": 100},
            )


@pytest.mark.optional
class TestLatentReportingEM:
    def test_em_converges(self) -> None:
        from nyc311.stats import latent_reporting_bias_em

        counts = {"A": 50, "B": 100, "C": 30, "D": 80}
        pops = {"A": 10000, "B": 10000, "C": 10000, "D": 10000}

        result = latent_reporting_bias_em(counts, pops)
        assert isinstance(result, LatentReportingResult)
        assert result.n_iterations > 0
        for uid in counts:
            assert result.reporting_probabilities[uid] > 0.0
            assert result.estimated_true_rates[uid] > 0.0
