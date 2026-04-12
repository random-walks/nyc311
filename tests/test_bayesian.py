"""Tests for Bayesian small-area smoothing (BYM2)."""

from __future__ import annotations

import pytest

from nyc311.stats import BYM2Result


class TestBYM2Dataclass:
    def test_bym2_result(self) -> None:
        r = BYM2Result(
            smoothed_rates={"A": 1.0, "B": 1.5},
            credible_lower={"A": 0.5, "B": 1.0},
            credible_upper={"A": 1.5, "B": 2.0},
            mixing_parameter=0.6,
            spatial_variance=0.04,
            iid_variance=0.02,
            unit_ids=("A", "B"),
            n_samples=1000,
            model_summary="summary",
        )
        assert r.mixing_parameter == 0.6


@pytest.mark.optional
class TestBYM2:
    def test_bym2_import_error(self) -> None:
        """BYM2 requires pymc; this test checks the error message."""
        import importlib.util

        if importlib.util.find_spec("pymc") is not None:
            pytest.skip("pymc is installed; ImportError path not testable")

        from nyc311.stats import bym2_smooth

        with pytest.raises(ImportError, match="pymc"):
            bym2_smooth(
                observed_counts={"A": 10},
                expected_counts={"A": 10.0},
                adjacency={"A": ()},
            )
