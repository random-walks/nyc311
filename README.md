# nyc311

[![Actions Status][actions-badge]][actions-link]
[![Documentation Status][rtd-badge]][rtd-link]
[![PyPI version][pypi-version]][pypi-link]
[![PyPI platforms][pypi-platforms]][pypi-link]

Python toolkit for building reproducible complaint-intelligence outputs from NYC
311 service-request data.

## Status

`nyc311` now ships a **real but still intentionally narrow v0.1 foundation**.

### Implemented now in v0.1

- load filtered NYC 311-style records from a **local CSV extract**
- load filtered NYC 311-style records from the **live Socrata API**
- derive a deterministic **first-pass topic label** for supported complaint
  types
- aggregate complaint topics by **borough** or **community district**
- export useful outputs as:
  - a **CSV topic summary table**
  - a **boundary-backed GeoJSON feature collection**
- run one thin CLI workflow for the happy path

### Still planned later

- anomaly detection
- resolution-gap analysis
- report-card generation
- broader report-generation and notebook workflows
- richer CLI coverage beyond the single happy-path command

Anything in the public package surface that is still planned remains importable
and raises a consistent `NotImplementedError`.

## Why this exists

NYC 311 data is one of the richest public records of neighborhood
quality-of-life complaints in the country, but much of the useful signal is
locked inside short text fields such as complaint descriptors.

This project aims to turn those records into reusable outputs for civic
analysis, journalism, and research while staying honest about what is truly
implemented today.

## v0.1 happy path

The current release focuses on one deterministic, testable workflow:

1. read a local CSV extract of NYC 311-style records or load a filtered slice
   from Socrata
2. filter rows by date, geography, and complaint type
3. assign a first-pass topic label using explicit keyword rules
4. aggregate counts by borough or community district
5. export the result as a CSV summary table or boundary-backed GeoJSON

### Supported v0.1 topic extraction

The current rules-based topic extractor is implemented only for:

- `Blocked Driveway`
- `Illegal Parking`
- `Noise - Residential`
- `Rodent`

This is intentionally described as **first-pass topic extraction**, not
clustering or advanced NLP.

## Example

```python
from datetime import date
from pathlib import Path

from nyc311 import (
    ExportTarget,
    GeographyFilter,
    ServiceRequestFilter,
    TopicQuery,
    aggregate_by_geography,
    export_topic_table,
    extract_topics,
    load_service_requests,
)

records = load_service_requests(
    "tests/fixtures/service_requests_fixture.csv",
    filters=ServiceRequestFilter(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 3, 31),
        geography=GeographyFilter("community_district", "BROOKLYN 01"),
        complaint_types=("Noise - Residential",),
    ),
)

assignments = extract_topics(records, TopicQuery("Noise - Residential"))
summary = aggregate_by_geography(assignments, geography="community_district")

export_topic_table(
    summary,
    ExportTarget(format="csv", output_path=Path("brooklyn-noise-topics.csv")),
)
```

CLI equivalent:

```bash
nyc311 topics \
  --source tests/fixtures/service_requests_fixture.csv \
  --complaint-type "Noise - Residential" \
  --geography community_district \
  --output brooklyn-noise-topics.csv
```

## Data assumptions in v0.1

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

`resolution_description` is optional and loaded when present, but it is not yet
used in the v0.1 topic rules.

## Public package surface

### Implemented now

- `nyc311.load_service_requests`
- `nyc311.load_boundaries`
- `nyc311.extract_topics`
- `nyc311.aggregate_by_geography`
- `nyc311.export_topic_table`
- `nyc311.export_geojson`
- `nyc311.main` with the `topics` subcommand
- typed models for filters, records, assignments, and summary rows

### Planned placeholders

- `nyc311.load_resolution_data`
- `nyc311.detect_anomalies`
- `nyc311.analyze_resolution_gaps`
- `nyc311.export_anomalies`
- `nyc311.export_report_card`

## Seeded sources of truth

- `docs/notes/original-spec.md`
- `docs/notes/gap-explination.md`
- `docs/mvp-roadmap.md`
- `docs/agent-kickoff-todo.md`

## Development

```bash
uv sync --group docs
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run mkdocs serve
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
