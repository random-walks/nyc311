# Examples

`nyc311` examples now live as self-contained consumer projects under
`examples/`. There are no repo-level example notebooks, no shared
`examples/utils/`, and no shared `examples/output/`.

## Contract

Every example follows the same structure:

- one semantic-slug folder under `examples/`
- one local `pyproject.toml`
- one local `README.md`
- one local `.gitignore`
- one `main.py` entrypoint
- local `cache/` and ignored `artifacts/` directories created on demand
- optional tracked `reports/` for markdown and report figures that should ship
  with the example

Each example imports only `nyc311.*`, so it exercises the package the same way
an external user would. In the repo, that happens through a local editable path
dependency. Outside the repo, the same scripts work after installing `nyc311`
from PyPI with the listed extras.

The canonical bootstrap starting point for new examples is
`examples/example-template/`.

## Overview

| Example                                   | Focus                                                                 | Default data mode                 | Extra                 | Cache | Artifacts                            | Reports                          | Status      |
| ----------------------------------------- | --------------------------------------------------------------------- | --------------------------------- | --------------------- | ----- | ------------------------------------ | -------------------------------- | ----------- |
| `examples/quickstart-sdk/`                | first in-memory SDK walkthrough                                       | packaged sample records           | base                  | no    | CSV topic summary                    | markdown tearsheet               | implemented |
| `examples/fetch-filtered-snapshot/`       | filtered Socrata fetch, cache reuse, and fetch metadata               | live fetch with local cache reuse | base                  | yes   | snapshot CSV + metadata JSON/MD      | optional publishable tearsheet   | implemented |
| `examples/community-district-case-study/` | Brooklyn case study with topic, volume, and resolution summaries      | cache-backed live slice           | `plotting`            | yes   | multiple scratch CSV summaries       | publish-gated tearsheet + 3 PNGs | implemented |
| `examples/topic-eda/`                     | coverage audit, unmatched descriptors, anomalies, and resolution gaps | cache-backed live slice           | `dataframes,plotting` | yes   | baseline report card + CSV summaries | publish-gated tearsheet + 4 PNGs | implemented |
| `examples/borough-choropleth/`            | borough-level dominant-topic map                                      | packaged sample records           | `spatial,plotting`    | no    | scratch CSV summaries                | tearsheet + 3 PNGs               | implemented |
| `examples/spatial-join-qa/`               | canonical spatial join QA over a larger cached live district audit    | cache-backed live slice           | `spatial,plotting`    | yes   | boundary inventory + join QA CSVs    | publish-gated tearsheet + 3 PNGs | implemented |
| `examples/community-district-choropleth/` | district-level dominant-topic map with full-layer context             | cache-backed live slice           | `spatial,plotting`    | yes   | scratch CSV summaries                | publish-gated tearsheet + 3 PNGs | implemented |
| `examples/spatial-topic-comparison/`      | joined-district topic comparison after spatial enrichment             | cache-backed live slice           | `spatial,plotting`    | yes   | joined topic CSV + preview tables    | publish-gated tearsheet + 4 PNGs | implemented |

## Data And Cache Strategy

The examples follow one default runtime story:

1. run in memory whenever packaged sample data is enough
2. when a story needs more data, write a cache file inside that example folder
3. reuse that local cache on later runs instead of refetching by default
4. keep ignored scratch outputs in `artifacts/` and tracked markdown/figures in
   `reports/`
5. for live examples, update tracked report assets only through an explicit
   publish step

That pattern keeps examples reproducible without reintroducing one shared global
dump directory.

## Local Repo Usage

From any example folder:

```bash
uv sync
uv run python main.py
```

Examples are intentionally not executed in the main CI or test matrix. The
package itself remains the tested release surface.

## Bootstrap Template

When adding a new example, start from `examples/example-template/`. It captures
the current conventions for:

- uv path-dependency setup
- ignored `cache/` and `artifacts/`
- tracked `reports/` and `reports/figures/`
- explicit relative markdown image paths like `./figures/example-chart.png`

## Snapshot-First Pattern

For larger workflows, fetch once and then iterate against a local snapshot:

```bash
nyc311 fetch \
  --output local-noise-snapshot.csv \
  --complaint-type "Noise - Residential" \
  --geography borough \
  --geography-value BROOKLYN \
  --start-date 2025-01-01 \
  --end-date 2025-03-31 \
  --page-size 1000 \
  --max-pages 6
```

Then point analysis at the saved file:

```bash
nyc311 topics \
  --source local-noise-snapshot.csv \
  --complaint-type "Noise - Residential" \
  --geography community_district \
  --output topics.csv
```

That same pattern is mirrored inside the cache-backed example projects.

## Case Studies

Longer-form analyses live under `examples/case_studies/`. Unlike the
short-form examples above, these projects exercise the full v0.3.0 modeling
surface against real data and ship with research-grade findings.

### `examples/case_studies/resolution_equity/`

A longitudinal study of NYC 311 resolution times across 59 community
districts over 60 monthly periods (January 2020 - December 2024). It walks
the entire `nyc311` v0.3.0 surface end-to-end:

- `nyc311.pipeline.bulk_fetch()` downloads 5 years of data split per borough
  with `.meta.json` integrity sidecars
- `nyc311.temporal.build_complaint_panel()` builds the balanced
  ``(community_district x month)`` panel
- `nyc311.stats.seasonal_decompose()` extracts trend, seasonal, and residual
  components per complaint type
- `nyc311.stats.detect_changepoints()` finds structural breaks aligned with
  COVID-19 lockdown and reopening phases
- `nyc311.stats.panel_fixed_effects()` runs the two-way FE resolution-equity
  regression
- `nyc311.stats.global_morans_i()` and `local_morans_i()` test for spatial
  clustering of slow/fast resolution districts
- `nyc311.factors` composes the supporting domain metrics

Run it from the case-study directory:

```bash
pip install "nyc311[stats,spatial,dataframes]"
cd examples/case_studies/resolution_equity
python run_analysis.py
```

The numbered scripts (`01_fetch_data.py` through `06_changepoint_detection.py`)
can also be run individually. See `FINDINGS.md` in that directory for the
written-up results.

### `examples/case_studies/rat_containerization/`

Evaluates the 2024 NYC rat containerization mandate using the full causal
inference toolkit:

- `nyc311.stats.synthetic_control()` builds a data-driven counterfactual for
  the first treated community district
- `nyc311.stats.staggered_did()` estimates group-time ATTs across the
  staggered rollout, correcting for TWFE bias
- `nyc311.stats.event_study()` produces event-time coefficients with
  pre-trend diagnostics
- `nyc311.stats.regression_discontinuity()` estimates the local treatment
  effect at the policy boundary
- `nyc311.factors` composes supporting metrics via `SpatialLagFactor` and
  `EquityGapFactor`

```bash
pip install "nyc311[stats,spatial,dataframes]"
cd examples/case_studies/rat_containerization
python run_analysis.py
```
