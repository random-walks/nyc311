#!/usr/bin/env python3
"""Step 6: Statistical power analysis for the panel design.

Computes the minimum detectable effect (MDE) given the real panel's
dimensions, ICC, and outcome variance.
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path
from typing import TYPE_CHECKING

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared.diagnostics import interpret_power

if TYPE_CHECKING:
    from nyc311.stats import PowerResult

DATA_DIR = Path(__file__).parent / "data"


def run() -> PowerResult:
    """Compute MDE for this panel design and print diagnostics."""
    import numpy as np

    from nyc311.stats import minimum_detectable_effect

    panel = pickle.loads((DATA_DIR / "panel.pkl").read_bytes())
    df = panel.to_dataframe()
    outcome_var = float(np.var(df["complaint_count"].to_numpy(), ddof=1))
    n_treated = len(panel.treatment_events[0].treated_units)
    proportion_treated = n_treated / len(panel.unit_ids)

    result = minimum_detectable_effect(
        n_units=len(panel.unit_ids),
        n_periods=len(panel.periods),
        icc=0.05,
        alpha=0.05,
        power=0.80,
        proportion_treated=proportion_treated,
        outcome_variance=outcome_var,
    )

    print(interpret_power(result))
    return result


if __name__ == "__main__":
    print("Step 6: Power Analysis\n")
    run()
