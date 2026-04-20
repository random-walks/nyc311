# Multi-borough 311 intake rollout — SDID case study

A self-contained showcase for
[`factor_factory.engines.sdid`](https://github.com/random-walks/factor-factory)
as wired through nyc311's adapter. Unlike the two production case studies
under `examples/case_studies/`, this one uses **synthetic data** so it
runs in under ten seconds and never touches the Socrata API.

## Scenario

A (fictional) expanded 311 intake rollout hits three NYC boroughs —
Manhattan, Brooklyn, and the Bronx — on the same month. Queens and
Staten Island stay on the old intake system through the study
window. We have monthly panel data for all five boroughs over three
years. The outcome is *resolution rate* (fraction of rodent
complaints with a non-null `resolution_description`).

The question: how does rollout change the borough-wide resolution
rate, once common time trends and borough fixed effects are netted
out?

Synthetic difference-in-differences (Arkhangelsky et al. 2021, *AER*)
is the right tool when multiple treated units adopt on the same
date: it combines synthetic-control-style unit weights with
DiD-style outcome regressions, outperforming bare TWFE under
time-varying confounders. SDID requires a single common treatment
onset across treated units — this scenario provides exactly that.
For true staggered-timing designs (different boroughs adopting on
different dates), use the Callaway-Sant'Anna estimator via
`factor_factory.engines.did.estimate(..., methods=("cs",))`
instead.

## Running

```bash
cd examples/sdid-multi-borough-policy
uv run python run_analysis.py
```

Outputs:

- `data/panel.parquet` — the synthetic Panel (pandas parquet).
- `artifacts/sdid_results.json` — SDID result dict, factor-factory
  schema.
- `artifacts/did_results.json` — a TWFE baseline for contrast.
- `manuscripts/FINDINGS.md`, `METHODOLOGY.md`, `DIAGNOSTICS_CHECKLIST.md`,
  `MANUSCRIPT.md`, `AUDIT.md` — jellycell tearsheets rendered from
  the artifacts.

## What's exercised

- `nyc311.temporal.PanelDataset` construction from synthetic records.
- `PanelDataset.to_factor_factory_panel()` adapter.
- `factor_factory.engines.sdid.estimate` — the headline.
- `factor_factory.engines.did.estimate` (TWFE) — contrast baseline.
- `factor_factory.jellycell.tearsheets.*` renderers.
