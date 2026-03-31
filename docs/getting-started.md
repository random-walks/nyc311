# Getting Started

This guide shows the fastest path to a useful `nyc311` run as either a CLI
user or a Python user.

## Install

```bash
pip install nyc311
```

For development installs, use:

```bash
uv sync --all-groups
```

## Input Data

The implemented loader expects NYC 311-style records with these columns:

- `unique_key`
- `created_date`
- `complaint_type`
- `descriptor`
- `borough`
- `community_district` or `community_board`

`resolution_description` is optional.

## First Snapshot Run

### CLI

```bash
nyc311 topics \
  --source brooklyn-noise-snapshot.csv \
  --complaint-type "Noise - Residential" \
  --geography community_district \
  --output topics.csv
```

### Python

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

summary = nyc311.aggregate_by_geography(
    nyc311.extract_topics(records, nyc311.TopicQuery("Noise - Residential")),
    geography="community_district",
)
nyc311.export_topic_table(
    summary,
    nyc311.ExportTarget("csv", Path("topics.csv")),
)

print(f"rows: {len(summary)}")
```

## Add Date And Geography Filters

```python
from datetime import date
from pathlib import Path

import nyc311

records = nyc311.fetch_service_requests(
    filters=nyc311.ServiceRequestFilter(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 3, 31),
        geography=nyc311.GeographyFilter("borough", nyc311.BOROUGH_BROOKLYN),
        complaint_types=("Noise - Residential",),
    ),
    socrata_config=nyc311.SocrataConfig(page_size=500, max_pages=2),
)

summary = nyc311.aggregate_by_geography(
    nyc311.extract_topics(records, nyc311.TopicQuery("Noise - Residential")),
    geography="community_district",
)
nyc311.export_topic_table(
    summary,
    nyc311.ExportTarget("csv", Path("brooklyn-noise-topics.csv")),
)
```

## Load Live Data From Socrata

Live Socrata loading is exposed through both the SDK and the CLI.

### CLI snapshot workflow

This is the recommended pattern for larger or repeated analysis runs: fetch a
filtered local snapshot first, then iterate against the CSV.

```bash
nyc311 fetch \
  --output rodent-snapshot.csv \
  --complaint-type "Rodent" \
  --geography borough \
  --geography-value BROOKLYN \
  --start-date 2025-01-01 \
  --end-date 2025-01-31 \
  --page-size 500 \
  --max-pages 1
```

Then point `nyc311 topics` or your Python code at the local snapshot.

```python
from datetime import date

import nyc311

records = nyc311.fetch_service_requests(
    socrata_config=nyc311.SocrataConfig(
        app_token=None,
        page_size=500,
        max_pages=2,
    ),
    filters=nyc311.ServiceRequestFilter(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        complaint_types=("Rodent",),
    ),
)

assignments = nyc311.extract_topics(records, nyc311.TopicQuery("Rodent"))
summary = nyc311.aggregate_by_geography(assignments, geography="borough")
```

## Export GeoJSON

Boundary-backed GeoJSON export is available from both the SDK and CLI.

### CLI

```bash
nyc311 topics \
  --source brooklyn-noise-snapshot.csv \
  --complaint-type "Noise - Residential" \
  --geography community_district \
  --format geojson \
  --boundaries community_district_boundaries.geojson \
  --output topics.geojson
```

### Python

```python
from pathlib import Path

import nyc311

nyc311.run_topic_pipeline(
    "brooklyn-noise-snapshot.csv",
    "Noise - Residential",
    geography="community_district",
    output_format="geojson",
    boundaries="community_district_boundaries.geojson",
    output=Path("topics.geojson"),
)
```

## Supported Complaint Types

The current rules-based extractor supports:

- `Blocked Driveway`
- `Illegal Parking`
- `Noise - Residential`
- `Rodent`

Use `nyc311.supported_topic_queries()` to inspect that list from code.

## Next Steps

- Use [CLI Reference](cli.md) to see every current flag and option.
- Use [SDK Guide](sdk.md) to compose custom workflows.
- Use [Examples](examples.md) for copy-paste scripts and notebooks.
- Use [Architecture](architecture.md) if you are extending the package.
