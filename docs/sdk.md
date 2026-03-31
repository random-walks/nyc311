# SDK Guide

`nyc311` is usable as a functional SDK for notebooks, scripts, scheduled jobs,
and data-processing workflows.

The current SDK is built around small, typed steps:

1. load records
2. extract deterministic topics
3. aggregate by geography
4. export an artifact if needed

## The Functional Workflow

The most common SDK pattern is:

1. fetch a live filtered slice into memory
2. inspect or enrich it in Python
3. export a local snapshot only if you want one
4. run topic or resolution analysis against that in-memory data

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

assignments = nyc311.extract_topics(
    records,
    nyc311.TopicQuery("Noise - Residential", top_n=10),
)

summary = nyc311.aggregate_by_geography(
    assignments,
    geography="community_district",
)

nyc311.export_topic_table(
    summary,
    nyc311.ExportTarget("csv", Path("brooklyn-noise-topics.csv")),
)
```

## One-Call Pipeline Helper

For workflow code that does not need to manage every intermediate step, use
`run_topic_pipeline()`:

```python
from pathlib import Path

import nyc311

records = nyc311.fetch_service_requests(
    filters=nyc311.ServiceRequestFilter(
        geography=nyc311.GeographyFilter("borough", nyc311.BOROUGH_BROOKLYN),
        complaint_types=("Noise - Residential",),
    ),
    socrata_config=nyc311.SocrataConfig(page_size=250, max_pages=1),
)

nyc311.export_service_requests_csv(
    records,
    nyc311.ExportTarget("csv", Path("brooklyn-noise-snapshot.csv")),
)
```

If you already have a local snapshot, `run_topic_pipeline()` remains the fastest
one-call path:

```python
summary = nyc311.run_topic_pipeline(
    "brooklyn-noise-snapshot.csv",
    "Noise - Residential",
    geography="community_district",
    output=Path("topics.csv"),
)
```

## Live Socrata Loading

The SDK already supports live loading through `SocrataConfig`.

```python
from datetime import date

import nyc311

summary = nyc311.run_topic_pipeline(
    nyc311.SocrataConfig(
        app_token=None,
        page_size=500,
        max_pages=1,
    ),
    "Rodent",
    geography="borough",
    filters=nyc311.ServiceRequestFilter(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
    ),
)
```

## Stage A Local Snapshot First

For larger workflows, a good pattern is to fetch once and cache the result as a
local CSV snapshot:

```python
from pathlib import Path

import nyc311

records = nyc311.load_service_requests(
    nyc311.SocrataConfig(page_size=500, max_pages=2),
    filters=nyc311.ServiceRequestFilter(
        complaint_types=("Noise - Residential",),
    ),
)

nyc311.export_service_requests_csv(
    records,
    nyc311.ExportTarget("csv", Path("noise-snapshot.csv")),
)
```

That keeps notebook iteration reproducible and avoids repeated live API fetches.

## Borough Constants

The public SDK includes canonical borough constants and normalization helpers:

```python
import nyc311

nyc311.BOROUGH_BROOKLYN
nyc311.SUPPORTED_BOROUGHS
nyc311.normalize_borough_name("bk")
```

## Boundary-Backed GeoJSON

```python
from pathlib import Path

import nyc311

summary = nyc311.run_topic_pipeline(
    "brooklyn-noise-snapshot.csv",
    "Noise - Residential",
    geography="community_district",
    output_format="geojson",
    boundaries="community_district_boundaries.geojson",
    output=Path("topics.geojson"),
)
```

Boundary files must currently include:

- `properties.geography`
- `properties.geography_value`

## Public Surface

### Implemented now

- `load_service_requests`
- `fetch_service_requests`
- `load_resolution_data`
- `load_boundaries`
- `extract_topics`
- `aggregate_by_geography`
- `analyze_resolution_gaps`
- `export_topic_table`
- `export_geojson`
- `export_service_requests_csv`
- `run_topic_pipeline`
- typed models such as `ServiceRequestFilter`, `TopicQuery`, and `ExportTarget`

### Planned placeholders

These remain importable but raise `NotImplementedError`:

- `detect_anomalies`
- `export_anomalies`
- `export_report_card`

## When To Use The CLI Instead

Use the CLI when you want:

- a repeatable command in CI or a shell script
- a simple local CSV to artifact workflow
- no custom Python composition

Use the SDK when you want:

- Socrata ingestion
- notebooks or workflow orchestration
- custom filtering, branching, or intermediate inspection
- direct access to typed objects instead of files alone
