# nyc311

`nyc311` is a Python toolkit for turning NYC 311 service-request data into
reproducible complaint-intelligence outputs.

Authored by [Blaise Albis-Burdige](https://blaiseab.com/).

It is designed for two complementary use cases:

- a thin CLI for repeatable batch runs
- a functional SDK for scripts, interactive analysis, and data workflows

These docs track the current stable `1.x` surface.

The current release line provides:

- loading filtered NYC 311-style records from local CSV extracts
- loading filtered records from the live NYC Socrata API
- deterministic first-pass topic extraction for supported complaint types
- aggregation by borough or community district
- topic-coverage, resolution-gap, and anomaly analysis helpers
- CSV, boundary-backed GeoJSON, and markdown report exports
- composable factor pipelines (`nyc311.factors`) with built-in domain factors
- balanced temporal panels (`nyc311.temporal`) with treatment-event modeling and
  inverse-distance spatial weights
- seventeen statistical modules (`nyc311.stats`) for ITS, changepoints, STL,
  Moran's I / LISA, panel FE/RE, synthetic control, staggered DiD, event
  studies, RDD, spatial econometrics, Theil + Oaxaca-Blinder, reporting-bias
  adjustment, Hawkes, BYM2, power analysis
- **factor-factory integration** — two additive bridges
  (`PanelDataset.to_factor_factory_panel()`,
  `Pipeline.as_factor_factory_estimate()`) route nyc311 panels into
  [factor-factory](https://github.com/random-walks/factor-factory)'s 17
  causal-inference engine families. See
  [factor-factory integration](integration.md).
- optional `tearsheets` extra — emits
  [jellycell](https://github.com/random-walks/jellycell) tearsheet manuscripts
  from the bundled case studies

## Geography layer

`nyc311.geographies` is the 311-facing compatibility layer over
[`nyc-geo-toolkit`](https://github.com/random-walks/nyc-geo-toolkit). It keeps
the packaged boundary workflow available inside `nyc311` while the generic
boundary assets and normalization logic live in the shared toolkit package.

## Docs Paths

- Hosted docs: [nyc311.readthedocs.io](https://nyc311.readthedocs.io/)
- Local preview: `make docs`
- Strict docs build: `make docs-build`

## Install

```bash
pip install nyc311
```

For the full turnkey stack:

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

## Quickstart

=== "CLI"

    ```bash
    nyc311 topics \
      --source service_requests.csv \
      --complaint-type "Noise - Residential" \
      --geography community_district \
      --output topics.csv
    ```

=== "Python"

    ```python
    from datetime import date
    from pathlib import Path

    from nyc311 import export, models, pipeline

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
    ```

## What Ships In The `1.x` Line

### Core SDK

- `load_service_requests()` for local CSV and `SocrataConfig` sources
- `fetch_service_requests()` for explicit live in-memory fetching
- `extract_topics()` for `Blocked Driveway`, `Illegal Parking`,
  `Noise - Residential`, `Rodent`
- `aggregate_by_geography()`, `analyze_topic_coverage()`,
  `analyze_resolution_gaps()`, `detect_anomalies()`
- `export_topic_table()`, `export_anomalies()`, `export_geojson()`,
  `export_report_card()`, `export_service_requests_csv()`
- optional pandas-backed dataframe helpers such as `records_to_dataframe()`
- `run_topic_pipeline()` for a one-call workflow
- `nyc311 fetch` and `nyc311 topics` CLI subcommands
- packaged sample fixtures via `nyc311.samples.load_sample_service_requests()`
  and `load_sample_boundaries()` for offline scripting

### Analysis surface (v1.0)

- `nyc311.factors.Pipeline` — composable, immutable factor pipeline with twelve
  built-in factors
- `nyc311.temporal.PanelDataset` — balanced `(unit, period)` panels with
  `TreatmentEvent` modeling and inverse-distance spatial weights
- `nyc311.stats` — seventeen statistical modules (ITS, changepoints, STL,
  Moran's I / LISA, panel FE/RE, SCM, staggered DiD, event studies, RDD, spatial
  lag / error, GWR, Theil, Oaxaca-Blinder, reporting-bias EM, Hawkes, BYM2
  small-area smoothing, power analysis)

### factor-factory integration (v1.0)

- `PanelDataset.to_factor_factory_panel()` — additive adapter to
  `factor_factory.tidy.Panel`
- `Pipeline.as_factor_factory_estimate()` — dispatches any of factor-factory's
  17 causal-inference engine families on a converted Panel
- Eleven of the seventeen `nyc311.stats` modules now cross-reference a
  factor-factory equivalent as the preferred backend

## Choose Your Path

- Start with [Getting Started](getting-started.md) for installation and first
  runs.
- Use [CLI Reference](cli.md) for repeatable command-line usage.
- Use [SDK Guide](sdk.md) for script and workflow-oriented usage.
- Use [factor-factory integration](integration.md) for the causal-inference
  engine adapters.
- Migrating from v0.3? See [Migration (v0 to v1)](migration-v0-to-v1.md).
- Use [Examples](examples.md) for self-contained consumer projects, the two
  production case studies, and the two factor-factory engine showcases.
- Use [API Reference](api.md) for the complete public package surface.
- Use [Architecture](architecture.md) if you are maintaining or extending the
  project.
