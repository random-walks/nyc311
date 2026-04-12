#!/usr/bin/env python3
"""Step 3: Synthetic control method for a treated Manhattan district.

Constructs a data-driven counterfactual for MANHATTAN 03 using a
weighted combination of untreated donor units (Abadie et al., 2010).
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path
from typing import TYPE_CHECKING

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared.diagnostics import interpret_synthetic_control

if TYPE_CHECKING:
    from nyc311.stats import SyntheticControlResult

DATA_DIR = Path(__file__).parent / "data"


def run() -> SyntheticControlResult:
    """Run synthetic control on the real panel and print diagnostics."""
    from nyc311.stats import synthetic_control

    panel = pickle.loads((DATA_DIR / "panel.pkl").read_bytes())

    # Pick a specific treated district as the focal unit
    treated = [u for u in panel.unit_ids if u.startswith("MANHATTAN")]
    focal_unit = "MANHATTAN 03" if "MANHATTAN 03" in treated else treated[0]

    result = synthetic_control(
        panel,
        treated_unit=focal_unit,
        outcome="complaint_count",
    )

    print(interpret_synthetic_control(result))
    return result


if __name__ == "__main__":
    print("Step 3: Synthetic Control\n")
    run()
