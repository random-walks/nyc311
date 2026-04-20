# nyc311

![nyc311 — NYC 311 complaint analysis](docs/images/nyc311-hero.png)

[![Actions Status][actions-badge]][actions-link]
[![Documentation Status][rtd-badge]][rtd-link]
[![PyPI version][pypi-version]][pypi-link]
[![PyPI platforms][pypi-platforms]][pypi-link]

Python toolkit for reproducible NYC 311 complaint analysis via a typed SDK and
CLI.

Authored by [Blaise Albis-Burdige](https://blaiseab.com/).

## What this package does

`nyc311` is the stable `1.x` toolkit for turning NYC 311 service-request data
into reproducible complaint-intelligence outputs and publication-quality
statistical analyses.

It pairs a thin CLI with a typed SDK so the same workflow can run in batch jobs,
scripts, notebooks, and consumer packages.

The current release line provides:

- load filtered NYC 311-style records from local CSV extracts or the live
  Socrata API
- derive deterministic first-pass topic labels for supported complaint types
- aggregate complaint topics by borough or community district
- measure topic-rule coverage and summarize resolution gaps
- score anomalies over aggregated topic summaries
- export CSV tables, boundary-backed GeoJSON, and markdown report cards
- expose the workflow through both a thin CLI and a composable functional SDK
- compose domain-specific factor pipelines over geographic units
- build balanced temporal panels with treatment-event modeling and
  inverse-distance spatial weights
- run interrupted-time-series, PELT changepoint, STL decomposition, Moran's I /
  LISA, and panel fixed/random-effects regressions
- causal inference: synthetic control, staggered difference-in-differences,
  event-study plots, regression discontinuity
- spatial econometrics: spatial lag and error models, geographically weighted
  regression
- equity analysis: Oaxaca-Blinder decomposition, Theil index, reporting-rate
  adjustment, latent reporting-bias EM
- diagnostics: seasonality-adjusted anomaly detection, power analysis / MDE
  calculator
- Bayesian: BYM2 small-area smoothing (behind `nyc311[bayes]`)
- point processes: Hawkes self-exciting process for complaint contagion
- bulk-fetch full-city extracts split per borough with `.meta.json` integrity
  sidecars

## Geography layer

`nyc311.geographies` is the 311-facing compatibility layer over
[`nyc-geo-toolkit`](https://github.com/random-walks/nyc-geo-toolkit).

Use `nyc311` when you want packaged NYC boundaries inside the 311 workflow. Use
`nyc-geo-toolkit` directly when you only need the generic geography assets,
normalization helpers, and boundary loaders.

## factor-factory integration (v1.0.0)

As of v1.0.0, `nyc311` wires through to
[factor-factory](https://github.com/random-walks/factor-factory)'s 17
causal-inference engine families via two additive adapters:

```python
from nyc311.temporal import build_complaint_panel, TreatmentEvent

panel = build_complaint_panel(records, geography="community_district")

# Hand off to any factor-factory engine family:
ff_panel = panel.to_factor_factory_panel()

from factor_factory.engines.did import estimate as did_estimate

results = did_estimate(ff_panel, methods=("twfe",), outcome="complaint_count")
print(results[0].att, results[0].ci_95)
```

The `nyc311.stats` modules continue to work as before; eleven of the seventeen
now cross-reference their factor-factory equivalent in a `.. note::` block. See
[`docs/integration.md`](docs/integration.md) for the full crosswalk and
[`docs/migration-v0-to-v1.md`](docs/migration-v0-to-v1.md) for the consumer
upgrade path.

Install the `tearsheets` extra to emit
[jellycell](https://github.com/random-walks/jellycell) manuscripts from the
bundled case studies:

```bash
pip install "nyc311[tearsheets]"
```

## Install

Choose the dependency footprint that matches your workflow:

```bash
pip install nyc311
```

For the full turnkey experience:

```bash
pip install "nyc311[all]"
```

For pandas-backed conversion helpers:

```bash
pip install "nyc311[dataframes]"
```

For geopandas-backed geography and spatial helpers:

```bash
pip install "nyc311[spatial]"
```

For plotting helpers:

```bash
pip install "nyc311[plotting]"
```

For plotting and exploratory analysis without the geospatial stack:

```bash
pip install "nyc311[science]"
```

For statistical modeling (interrupted time series, changepoints, STL, Moran's I,
panel regressions):

```bash
pip install "nyc311[stats]"
```

For BYM2 small-area smoothing (PyMC):

```bash
pip install "nyc311[bayes]"
```

## Why this exists

NYC 311 data is one of the richest public records of neighborhood
quality-of-life complaints in the country, but much of the useful signal is
locked inside short text fields such as complaint descriptors.

`nyc311` turns those records into reusable outputs for civic analysis,
journalism, and research through an explicit, testable workflow.

## Core workflow

The current stable workflow is:

1. load records from a local CSV extract or a filtered Socrata slice
2. filter by date, geography, and complaint type
3. assign a first-pass topic label using explicit keyword rules
4. aggregate counts by borough or community district
5. export a CSV summary table or boundary-backed GeoJSON artifact

### Supported topic extraction

The current rules-based topic extractor is implemented for the complaint types
returned by `nyc311.models.supported_topic_queries()` (nine high-volume types
including noise, rodents, street condition, heat/hot water, sanitary, and
abandoned vehicles).

This is intentionally described as **first-pass topic extraction**, not
clustering or advanced NLP.

## Time series

Use `nyc311.dataframes` helpers for DatetimeIndex complaint counts and panel
layouts:

```python
from nyc311 import pipeline, presets
from nyc311.dataframes import to_timeseries, to_panel

records = pipeline.fetch_service_requests(
    filters=presets.brooklyn_borough_filter(
        start_date="2024-01-01",
        end_date="2024-12-31",
        complaint_types=("Noise - Residential", "Rodent"),
    ),
    socrata_config=presets.large_socrata_config(),
    cache_dir="./cache",
)

ts = to_timeseries(records, freq="W")
ts.plot(title="Weekly complaint volume")

panel = to_panel(records, freq="ME", geography="borough")
panel.xs("BROOKLYN")["Noise - Residential"].plot()
```

## Data surface

- **Socrata:** dataset `erm2-nwe9` (NYC 311 Service Requests from 2010 onward;
  tens of millions of rows). Use `presets.large_socrata_config()` for bulk
  pagination (default 5,000 rows per HTTP request) and `nyc311.io.cached_fetch`
  to stream pages to CSV without holding the full history in memory.
- **Boundaries:** borough, community district, council district, NTA, census
  tract, and ZCTA layers ship through `nyc311.geographies` (built on
  `nyc-geo-toolkit`).
- **Caching:** pass `cache_dir` and optional `refresh` / `max_cached_records` to
  `pipeline.fetch_service_requests` or `io.load_service_requests` so repeated
  runs reuse deterministic CSV snapshots under `cache_dir`.

## Quick links

Docs: [Home](https://nyc311.readthedocs.io/en/latest/),
[Getting Started](https://nyc311.readthedocs.io/en/latest/getting-started/),
[CLI Reference](https://nyc311.readthedocs.io/en/latest/cli/),
[SDK Guide](https://nyc311.readthedocs.io/en/latest/sdk/),
[Examples](https://nyc311.readthedocs.io/en/latest/examples/),
[Architecture](https://nyc311.readthedocs.io/en/latest/architecture/),
[Contributing](https://nyc311.readthedocs.io/en/latest/contributing/),
[Releasing](https://nyc311.readthedocs.io/en/latest/releasing/),
[Changelog](https://nyc311.readthedocs.io/en/latest/changelog/)

## Example

```python
from datetime import date
from pathlib import Path

from nyc311 import analysis, export, models, pipeline

records = pipeline.fetch_service_requests(
    filters=models.ServiceRequestFilter(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        geography=models.GeographyFilter("borough", models.BOROUGH_BROOKLYN),
        complaint_types=("Noise - Residential",),
    ),
    socrata_config=models.SocrataConfig(page_size=250, max_pages=1),
)

export.export_service_requests_csv(
    records,
    models.ExportTarget("csv", Path("brooklyn-noise-snapshot.csv")),
)

assignments = analysis.extract_topics(records, models.TopicQuery("Noise - Residential"))
summary = analysis.aggregate_by_geography(assignments, geography="community_district")
export.export_topic_table(
    summary,
    models.ExportTarget("csv", Path("brooklyn-noise-topics.csv")),
)
```

CLI equivalent:

```bash
nyc311 fetch \
  --output brooklyn-noise-snapshot.csv \
  --complaint-type "Noise - Residential" \
  --geography borough \
  --geography-value BROOKLYN \
  --start-date 2025-01-01 \
  --end-date 2025-01-31 \
  --page-size 250 \
  --max-pages 1

nyc311 topics \
  --source brooklyn-noise-snapshot.csv \
  --complaint-type "Noise - Residential" \
  --geography community_district \
  --output brooklyn-noise-topics.csv
```

Live-data snapshot workflow:

```bash
nyc311 fetch \
  --output brooklyn-rodent-snapshot.csv \
  --complaint-type "Rodent" \
  --geography borough \
  --geography-value BROOKLYN \
  --start-date 2025-01-01 \
  --end-date 2025-01-31 \
  --page-size 500 \
  --max-pages 1
```

### Factor pipeline

`nyc311.factors` composes domain-specific metrics over geographic units:

```python
from datetime import date

from nyc311.factors import (
    ComplaintVolumeFactor,
    EquityGapFactor,
    FactorContext,
    Pipeline,
    ResponseRateFactor,
    SpatialLagFactor,
    TopicConcentrationFactor,
)

contexts = [
    FactorContext(
        geography="community_district",
        geography_value=cd,
        complaints=tuple(complaints),
        time_window_start=date(2024, 1, 1),
        time_window_end=date(2024, 12, 31),
    )
    for cd, complaints in records_by_cd.items()
]

result = (
    Pipeline()
    .add(ComplaintVolumeFactor())
    .add(ResponseRateFactor())
    .add(TopicConcentrationFactor())
    .run(contexts)
)
df = result.to_dataframe()  # one row per CD, one column per factor
```

See the [SDK guide](https://nyc311.readthedocs.io/en/latest/sdk/) for the
matching temporal-panel, statistical-modeling, and bulk-download examples.

## Data assumptions

`load_service_requests()` currently supports:

- local CSV files
- live Socrata loading via `SocrataConfig`

CSV inputs use these columns:

- `unique_key`
- `created_date`
- `complaint_type`
- `descriptor`
- `borough`
- `community_district` or `community_board`

`resolution_description` is optional and loaded when present. It is currently
used by the resolution-gap and report-card helpers, while topic extraction
remains descriptor-driven.

## Public package surface

The public API is organized around explicit namespaces:

- `nyc311.models` for dataclasses, constants, and configs
- `nyc311.io` for CSV and Socrata loading
- `nyc311.analysis` for topic extraction, coverage, gaps, and anomalies
- `nyc311.geographies` for the 311-facing compatibility layer over
  `nyc-geo-toolkit`
- `nyc311.samples` for packaged sample records and sample-aligned boundaries
- `nyc311.export` for CSV, GeoJSON, and report exports
- `nyc311.pipeline` for one-call workflow helpers
- `nyc311.dataframes` for optional pandas conversions
- `nyc311.spatial` for optional geopandas helpers
- `nyc311.plotting` for optional plotting helpers
- `nyc311.presets` for reusable filter and Socrata config builders
- `nyc311.factors` for the composable factor pipeline and built-in domain
  factors (including SpatialLagFactor and EquityGapFactor)
- `nyc311.temporal` for balanced panel datasets, treatment events, and
  inverse-distance spatial weights
- `nyc311.stats` for ITS, PELT changepoints, STL, Moran's I / LISA, panel
  fixed/random-effects regressions, synthetic control, staggered DiD, event
  study, RDD, spatial lag/error, GWR, Oaxaca-Blinder, Theil, reporting-bias
  adjustment, BYM2, Hawkes, anomaly detection, and power analysis
- `nyc311.cli` with the `topics` and `fetch` subcommands

## Documentation

The hosted docs site is the canonical reference:
[nyc311.readthedocs.io](https://nyc311.readthedocs.io/).

If you are browsing in GitHub, the source docs live in `docs/`, including
`index.md`, `getting-started.md`, `cli.md`, `sdk.md`, `examples.md`, `api.md`,
`architecture.md`, and `contributing.md`.

Runnable examples live in `examples/` as self-contained consumer projects.

**Precious research case studies** (real data, cited in `CITATION.cff`) under
`examples/case_studies/`:

- **[Rat Containerization](examples/case_studies/rat_containerization/)** --
  Evaluates the 2024 NYC containerization mandate using 81K real rodent
  complaints, the factor pipeline, STL decomposition, Moran's I, Theil
  inequality, synthetic control, staggered DiD, event study, RDD, and power
  analysis across 70 community districts.
- **[Resolution Equity](examples/case_studies/resolution_equity/)** --
  Investigates whether resolution times vary by neighborhood demographics using
  1M real 311 requests, two-way FE regression, Oaxaca-Blinder decomposition with
  ACS census data, spatial autocorrelation, ITS, and latent reporting-bias
  estimation.

**factor-factory engine showcases** (synthetic data, offline in seconds):

- **[SDID multi-borough policy](examples/sdid-multi-borough-policy/)** --
  Synthetic Difference-in-Differences (Arkhangelsky et al. 2021, _AER_) over a
  5-borough × 36-month simulated 311 intake rollout.
- **[Mediation cascade (resolution)](examples/mediation-cascade-resolution/)**
  -- Four-way mediation decomposition (VanderWeele 2014, _Epidemiology_) of
  pilot → triage-time → resolution-rate.
- **[factor-factory quickstart](examples/factor-factory-quickstart/)** --
  Minimal `PanelDataset → factor_factory.tidy.Panel → engine → pandas` in ~50
  lines, **without jellycell**. Starting point for consumers who want the
  adapter without the tearsheet machinery.

For local preview:

```bash
make docs
make docs-build
```

## Development

```bash
uv sync
uv sync --all-groups --all-extras
uv run --all-extras pytest -m "not integration"
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run mkdocs serve
uv run mkdocs build --strict
uv run python scripts/audit_public_api.py
uv run pytest -m "fetch and not integration"
```

## License

MIT.

<!-- prettier-ignore-start -->
[actions-badge]:            https://github.com/random-walks/nyc311/actions/workflows/ci.yml/badge.svg
[actions-link]:             https://github.com/random-walks/nyc311/actions
[github-discussions-badge]: https://img.shields.io/static/v1?label=Discussions&message=Ask&color=blue&logo=github
[github-discussions-link]:  https://github.com/random-walks/nyc311/discussions
[pypi-link]:                https://pypi.org/project/nyc311/
[pypi-platforms]:           https://img.shields.io/pypi/pyversions/nyc311
[pypi-version]:             https://img.shields.io/pypi/v/nyc311
[rtd-badge]:                https://readthedocs.org/projects/nyc311/badge/?version=latest
[rtd-link]:                 https://nyc311.readthedocs.io/en/latest/?badge=latest
<!-- prettier-ignore-end -->
