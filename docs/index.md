# nyc311

`nyc311` is a Python toolkit for turning NYC 311 service-request data into
reproducible complaint-intelligence outputs.

It is designed for two complementary use cases:

- a thin CLI for repeatable batch runs
- a functional SDK for scripts, interactive analysis, and data workflows

These docs track the `0.2` release surface as the project prepares its first
public stable launch.

The `0.2` release line ships a complete first-pass analysis workflow:

- loading filtered NYC 311-style records from local CSV extracts
- loading filtered records from the live NYC Socrata API
- deterministic first-pass topic extraction for supported complaint types
- aggregation by borough or community district
- topic-coverage, resolution-gap, and anomaly analysis helpers
- CSV, boundary-backed GeoJSON, and markdown report exports

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

## What Ships In The `0.2` Release Line

### Implemented

- `load_service_requests()` for local CSV and `SocrataConfig` sources
- `fetch_service_requests()` for explicit live in-memory fetching
- `extract_topics()` for:
  - `Blocked Driveway`
  - `Illegal Parking`
  - `Noise - Residential`
  - `Rodent`
- `aggregate_by_geography()`
- `analyze_topic_coverage()` for descriptor coverage summaries
- `analyze_resolution_gaps()` for first-pass borough-level unresolved-share
  summaries
- `detect_anomalies()` for z-score-based anomaly flags over aggregated summaries
- `export_topic_table()`
- `export_anomalies()`
- `export_geojson()`
- `export_report_card()`
- `export_service_requests_csv()` for local snapshot staging
- optional pandas-backed dataframe helpers such as `records_to_dataframe()`
- `run_topic_pipeline()` for a one-call workflow
- `nyc311 fetch` and `nyc311 topics` for the current CLI workflows

## Choose Your Path

- Start with [Getting Started](getting-started.md) for installation and first
  runs.
- Use [CLI Reference](cli.md) for repeatable command-line usage.
- Use [SDK Guide](sdk.md) for script and workflow-oriented usage.
- Use [Examples](examples.md) for self-contained consumer projects and staged
  fetch workflows.
- Use [API Reference](api.md) for the complete public package surface.
- Use [Architecture](architecture.md) if you are maintaining or extending the
  project.
