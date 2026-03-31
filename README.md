# nyc311

[![Actions Status][actions-badge]][actions-link]
[![Documentation Status][rtd-badge]][rtd-link]
[![PyPI version][pypi-version]][pypi-link]
[![PyPI platforms][pypi-platforms]][pypi-link]

Python toolkit for building reproducible complaint-intelligence outputs from NYC
311 service-request data through both a thin CLI and a functional SDK.

## Status

`nyc311` now ships an **early alpha release** with a complete first-pass toolkit
for loading, analyzing, and exporting NYC 311 complaint data.

### Implemented today

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

For pandas-backed conversion helpers:

```bash
pip install "nyc311[dataframes]"
```

For notebook and plotting workflows:

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

The current release focuses on a deterministic, testable workflow:

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

- Docs home: [`docs/index.md`](docs/index.md)
- Getting started: [`docs/getting-started.md`](docs/getting-started.md)
- CLI reference: [`docs/cli.md`](docs/cli.md)
- SDK guide: [`docs/sdk.md`](docs/sdk.md)
- Examples: [`docs/examples.md`](docs/examples.md)
- Architecture: [`docs/architecture.md`](docs/architecture.md)
- Contributing: [`docs/contributing.md`](docs/contributing.md)

## Example

```python
from datetime import date
from pathlib import Path

import nyc311

records = nyc311.fetch_service_requests(
    filters=nyc311.ServiceRequestFilter(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        geography=nyc311.GeographyFilter("borough", nyc311.BOROUGH_BROOKLYN),
        complaint_types=("Noise - Residential",),
    ),
    socrata_config=nyc311.SocrataConfig(page_size=250, max_pages=1),
)

nyc311.export_service_requests_csv(
    records,
    nyc311.ExportTarget("csv", Path("brooklyn-noise-snapshot.csv")),
)

assignments = nyc311.extract_topics(records, nyc311.TopicQuery("Noise - Residential"))
summary = nyc311.aggregate_by_geography(assignments, geography="community_district")
nyc311.export_topic_table(
    summary,
    nyc311.ExportTarget("csv", Path("brooklyn-noise-topics.csv")),
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

The current public package surface includes:

- `nyc311.load_service_requests`
- `nyc311.fetch_service_requests`
- `nyc311.load_resolution_data`
- `nyc311.load_boundaries`
- `nyc311.extract_topics`
- `nyc311.aggregate_by_geography`
- `nyc311.analyze_topic_coverage`
- `nyc311.analyze_resolution_gaps`
- `nyc311.detect_anomalies`
- `nyc311.export_topic_table`
- `nyc311.export_anomalies`
- `nyc311.export_geojson`
- `nyc311.export_report_card`
- `nyc311.export_service_requests_csv`
- `nyc311.records_to_dataframe`
- `nyc311.assignments_to_dataframe`
- `nyc311.summaries_to_dataframe`
- `nyc311.gaps_to_dataframe`
- `nyc311.anomalies_to_dataframe`
- `nyc311.coverage_to_dataframe`
- `nyc311.run_topic_pipeline`
- `nyc311.main` with the `topics` and `fetch` subcommands
- typed models for filters, records, assignments, and summary rows

## Documentation

The main user-facing docs now live in `docs/`:

- `docs/index.md`
- `docs/getting-started.md`
- `docs/cli.md`
- `docs/sdk.md`
- `docs/examples.md`
- `docs/api.md`
- `docs/architecture.md`
- `docs/contributing.md`

Runnable examples live in `examples/`, including scripts and notebooks.

The original planning docs are preserved under `docs/og-context/` for historical
context.

## Archived context

- `docs/og-context/notes/original-spec.md`
- `docs/og-context/notes/gap-explination.md`
- `docs/og-context/mvp-roadmap.md`
- `docs/og-context/agent-kickoff-todo.md`

## Development

```bash
uv sync
uv sync --all-groups --all-extras
uv run pytest -m "not integration and not optional"
uv run --extra dataframes pytest -m optional
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run mkdocs serve
uv run python scripts/audit_implementation.py
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
