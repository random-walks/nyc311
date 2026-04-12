#!/usr/bin/env python3
"""Step 4: Staggered difference-in-differences with event-study diagnostics.

Estimates group-time average treatment effects using the Callaway &
Sant'Anna (2021) approach, then validates the parallel-trends
assumption via an event-study F-test.
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path
from typing import TYPE_CHECKING

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared.diagnostics import interpret_event_study, interpret_staggered_did

if TYPE_CHECKING:
    from nyc311.stats import EventStudyResult, StaggeredDiDResult

DATA_DIR = Path(__file__).parent / "data"


def run() -> tuple[StaggeredDiDResult, EventStudyResult]:
    """Run staggered DiD + event study and print diagnostics."""
    from nyc311.stats import event_study, staggered_did

    panel = pickle.loads((DATA_DIR / "panel.pkl").read_bytes())

    did_result = staggered_did(panel, outcome="complaint_count")
    print(interpret_staggered_did(did_result))

    print()

    es_result = event_study(
        panel,
        outcome="complaint_count",
        pre_periods=6,
        post_periods=6,
    )
    print(interpret_event_study(es_result))

    return did_result, es_result


if __name__ == "__main__":
    print("Step 4: Staggered DiD + Event Study\n")
    run()
