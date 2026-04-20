#!/usr/bin/env python3
"""Step 11: Render jellycell tearsheets from the analysis results.

Additive step — runs AFTER ``10_generate_findings.py`` and does NOT
modify or replace ``FINDINGS.md``. The existing FINDINGS.md remains
the authoritative study write-up. This step produces a parallel
tearsheet set under ``manuscripts/`` via
:mod:`factor_factory.jellycell.tearsheets`.

Engines bridged:

- ``synthetic_control`` → ``scm_results.json``
- ``staggered_did`` → ``did_results.json``
- ``rdd`` → ``rdd_results.json``

Other nyc311 outputs (STL decomposition, changepoints, equity
diagnostics) are kept in the homegrown ``FINDINGS.md`` only, because
factor-factory's tearsheet templates don't have dedicated slots for
every family and a lossy bridge would be misleading.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared.tearsheets import (
    ensure_jellycell_toml,
    render_all_tearsheets,
    write_factor_factory_artifacts,
)

HERE = Path(__file__).parent
DATA_DIR = HERE / "data"
ARTIFACTS_DIR = HERE / "artifacts"
MANUSCRIPTS_DIR = HERE / "manuscripts"
ANALYSIS_JSON = DATA_DIR / "analysis_results.json"


def run() -> None:
    """Render jellycell tearsheets alongside the existing FINDINGS.md."""
    if not ANALYSIS_JSON.exists():
        print(f"  Skipping tearsheets: {ANALYSIS_JSON.name} not found.")
        print("  Run step 10 ('10_generate_findings.py') first.")
        return

    MANUSCRIPTS_DIR.mkdir(exist_ok=True)
    analysis = json.loads(ANALYSIS_JSON.read_text())

    ensure_jellycell_toml(HERE, "rat-containerization-study")

    written = write_factor_factory_artifacts(analysis, ARTIFACTS_DIR)
    if written:
        print(f"  Wrote {len(written)} artifact(s): {', '.join(written)}")
    else:
        print("  No artifacts written (no covered engine results in analysis).")

    rendered = render_all_tearsheets(HERE)
    if rendered:
        print(f"  Rendered {len(rendered)} tearsheet(s): {', '.join(rendered)}")
        print(f"  See {MANUSCRIPTS_DIR.relative_to(HERE.parent.parent.parent)}/")


if __name__ == "__main__":
    run()
