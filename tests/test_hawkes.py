"""Tests for Hawkes point process estimation."""

from __future__ import annotations

import pytest

from nyc311.stats import HawkesResult


class TestHawkesDataclass:
    def test_hawkes_result(self) -> None:
        r = HawkesResult(
            background_rate=0.5,
            triggering_kernel_alpha=0.3,
            triggering_kernel_beta=1.0,
            branching_ratio=0.3,
            n_events=100,
            log_likelihood=-200.0,
            model_summary="summary",
        )
        assert r.branching_ratio == 0.3


@pytest.mark.optional
class TestHawkesProcess:
    def test_fit_poisson_events(self) -> None:
        """Fit a Hawkes to Poisson events: branching ratio should be low."""
        import numpy as np

        from nyc311.stats import fit_hawkes_process

        rng = np.random.default_rng(42)
        times = np.sort(rng.uniform(0, 100, 80))

        result = fit_hawkes_process(times)
        assert isinstance(result, HawkesResult)
        assert result.n_events == 80
        assert result.background_rate > 0
        assert result.branching_ratio < 1.0

    def test_too_few_events(self) -> None:
        import numpy as np

        from nyc311.stats import fit_hawkes_process

        with pytest.raises(ValueError, match="at least 3"):
            fit_hawkes_process(np.array([1.0, 2.0]))

    def test_invalid_kernel(self) -> None:
        import numpy as np

        from nyc311.stats import fit_hawkes_process

        with pytest.raises(ValueError, match="exponential"):
            fit_hawkes_process(np.array([1.0, 2.0, 3.0]), kernel="gaussian")
