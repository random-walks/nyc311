# nyc311

[![Actions Status][actions-badge]][actions-link]
[![Documentation Status][rtd-badge]][rtd-link]
[![PyPI version][pypi-version]][pypi-link]
[![PyPI platforms][pypi-platforms]][pypi-link]

Python toolkit for building reproducible complaint-intelligence outputs from NYC
311 service-request data through both a thin CLI and a functional SDK.

## Status

`nyc311` is preparing its first public stable release in the `0.2` line with a
complete first-pass toolkit for loading, analyzing, and exporting NYC 311
complaint data.

The `0.2` release line better matches the current scope than the older `v0.1`
foundation framing that the project started from.

### Implemented in the `0.2` release line

- load filtered NYC 311-style records from local CSV extracts or the live
  Socrata API
- stage filtered live slices as reproducible local CSV snapshots
- derive deterministic first-pass topic labels for supported complaint types
- aggregate complaint topics by borough or community district
- measure topic-rule coverage and summarize resolution gaps
- score anomalies over aggregated topic summaries
- export CSV tables, boundary-backed GeoJSON, and markdown report cards
- run the workflow through both a thin CLI and a composable functional SDK

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

For plotting and exploratory analysis without the geospatial stack:

```bash
pip install "nyc311[science]"
```

## Why this exists

NYC 311 data is one of the richest public records of neighborhood
quality-of-life complaints in the country, but much of the useful signal is
locked inside short text fields such as complaint descriptors.

This project aims to turn those records into reusable outputs for civic
analysis, journalism, and research while staying honest about what is truly
implemented today.

## Core workflow

The current `0.2` release line focuses on a deterministic, testable workflow:

1. read a local CSV extract of NYC 311-style records or load a filtered slice
   from Socrata
2. filter rows by date, geography, and complaint type
3. assign a first-pass topic label using explicit keyword rules
4. aggregate counts by borough or community district
5. export the result as a CSV summary table or boundary-backed GeoJSON

### Supported topic extraction

The current rules-based topic extractor is implemented only for:

- `Blocked Driveway`
- `Illegal Parking`
- `Noise - Residential`
- `Rodent`

This is intentionally described as **first-pass topic extraction**, not
clustering or advanced NLP.

## Quick links

- Docs home: [nyc311.readthedocs.io](https://nyc311.readthedocs.io/en/latest/)
- Getting started:
  [Getting Started](https://nyc311.readthedocs.io/en/latest/getting-started/)
- CLI reference: [CLI Reference](https://nyc311.readthedocs.io/en/latest/cli/)
- SDK guide: [SDK Guide](https://nyc311.readthedocs.io/en/latest/sdk/)
- Examples: [Examples](https://nyc311.readthedocs.io/en/latest/examples/)
- Architecture:
  [Architecture](https://nyc311.readthedocs.io/en/latest/architecture/)
- Contributing:
  [Contributing](https://nyc311.readthedocs.io/en/latest/contributing/)

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

The current public package surface is organized around explicit namespaces:

- `nyc311.models` for dataclasses, constants, and configs
- `nyc311.io` for CSV and Socrata loading
- `nyc311.analysis` for topic extraction, coverage, gaps, and anomalies
- `nyc311.geographies` for packaged boundary layers and geometry helpers
- `nyc311.samples` for packaged sample records and sample-aligned boundaries
- `nyc311.export` for CSV, GeoJSON, and report exports
- `nyc311.pipeline` for one-call workflow helpers
- `nyc311.dataframes` for optional pandas conversions
- `nyc311.spatial` for optional geopandas helpers
- `nyc311.plotting` for optional plotting helpers
- `nyc311.presets` for reusable filter and Socrata config builders
- `nyc311.cli` with the `topics` and `fetch` subcommands

## Documentation

The hosted docs site is the canonical reference:

- [nyc311.readthedocs.io](https://nyc311.readthedocs.io/)

If you are browsing in GitHub, the docs source lives in `docs/`:

- `docs/index.md`
- `docs/getting-started.md`
- `docs/cli.md`
- `docs/sdk.md`
- `docs/examples.md`
- `docs/api.md`
- `docs/architecture.md`
- `docs/contributing.md`

Runnable examples live in `examples/` as self-contained consumer projects.

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
