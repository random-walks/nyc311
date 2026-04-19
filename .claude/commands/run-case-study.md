---
description: Run one of the nyc311 case studies end-to-end and refresh its jellycell tearsheets. Usage — `/run-case-study <slug>`, e.g. `/run-case-study rat_containerization`. $ARGUMENTS
---

Resolve `$ARGUMENTS` to a case-study directory:

- `rat_containerization` → `examples/case_studies/rat_containerization/`
- `resolution_equity` → `examples/case_studies/resolution_equity/`
- `sdid-multi-borough-policy` → `examples/sdid-multi-borough-policy/`
- `mediation-cascade-resolution` → `examples/mediation-cascade-resolution/`

If the slug doesn't match, list the available options and stop.

Then:

1. `cd` into the matched directory (keep absolute paths — do not stay
   there for later tool calls).
2. Run `uv run python run_analysis.py`. Stream the output. Let the
   analysis take as long as it takes — the `rat_containerization`
   and `resolution_equity` studies pull real 311 data through Socrata
   and can run for 3-8 minutes on first execution (subsequent runs
   use the cached snapshot).
3. When the run finishes, confirm the case study produced its
   artifacts:
   - `data/analysis_results.json`
   - `manuscripts/FINDINGS.md`
   - `manuscripts/METHODOLOGY.md`
   - `manuscripts/DIAGNOSTICS_CHECKLIST.md`
   - Engine-specific result JSON files under `artifacts/`.
4. **Numeric-parity check** for the precious case studies
   (`rat_containerization`, `resolution_equity`): diff the newly
   regenerated `data/analysis_results.json` against the last
   committed copy. If any numeric field changed by more than 1e-3
   (relative), STOP and surface the diff — ask the user before
   overwriting. These two case studies are research artifacts; the
   numbers must match or the user must explicitly opt-in to updated
   values.
5. Print a short summary: which files regenerated, which tearsheets
   were refreshed, and any diff surfaced in step 4.
