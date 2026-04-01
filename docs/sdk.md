# SDK Guide

`nyc311` is usable as a functional SDK for notebooks, scripts, scheduled jobs,
and data-processing workflows.

This guide describes the SDK surface for the current `0.2` alpha prerelease
line.

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

assignments = analysis.extract_topics(
    records,
    models.TopicQuery("Noise - Residential", top_n=10),
)

summary = analysis.aggregate_by_geography(
    assignments,
    geography="community_district",
)

export.export_topic_table(
    summary,
    models.ExportTarget("csv", Path("brooklyn-noise-topics.csv")),
)
```

## One-Call Pipeline Helper

For workflow code that does not need to manage every intermediate step, use
`nyc311.pipeline.run_topic_pipeline()`:

```python
from pathlib import Path

from nyc311 import export, models, pipeline

records = pipeline.fetch_service_requests(
    filters=models.ServiceRequestFilter(
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

If you already have a local snapshot, `run_topic_pipeline()` remains the fastest
one-call path:

```python
from nyc311.pipeline import run_topic_pipeline

summary = run_topic_pipeline(
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

from nyc311 import models
from nyc311.pipeline import run_topic_pipeline

summary = run_topic_pipeline(
    models.SocrataConfig(
        app_token=None,
        page_size=500,
        max_pages=1,
    ),
    "Rodent",
    geography="borough",
    filters=models.ServiceRequestFilter(
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

from nyc311 import export, io, models

records = io.load_service_requests(
    models.SocrataConfig(page_size=500, max_pages=2),
    filters=models.ServiceRequestFilter(
        complaint_types=("Noise - Residential",),
    ),
)

export.export_service_requests_csv(
    records,
    models.ExportTarget("csv", Path("noise-snapshot.csv")),
)
```

That keeps notebook iteration reproducible and avoids repeated live API fetches.

## Optional DataFrame helpers

The pandas-backed helpers live behind an optional extra so the base package can
stay lightweight:

```bash
pip install "nyc311[dataframes]"
```

For the full turnkey stack:

```bash
pip install "nyc311[all]"
```

Or install the broader notebook stack without geospatial dependencies:

```bash
pip install "nyc311[science]"
```

Once installed, the SDK exposes helpers such as
`nyc311.dataframes.records_to_dataframe()`,
`nyc311.dataframes.assignments_to_dataframe()`,
`nyc311.dataframes.summaries_to_dataframe()`,
`nyc311.dataframes.gaps_to_dataframe()`,
`nyc311.dataframes.anomalies_to_dataframe()`,
`nyc311.dataframes.coverage_to_dataframe()`, and
`nyc311.dataframes.dataframe_to_records()`.

## Borough Constants

The public SDK includes canonical borough constants and normalization helpers:

```python
from nyc311.models import BOROUGH_BROOKLYN, SUPPORTED_BOROUGHS, normalize_borough_name

BOROUGH_BROOKLYN
SUPPORTED_BOROUGHS
normalize_borough_name("bk")
```

## Boundary-Backed GeoJSON

```python
from pathlib import Path

from nyc311.pipeline import run_topic_pipeline

summary = run_topic_pipeline(
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

### Canonical namespaces

- `nyc311.models`
- `nyc311.io`
- `nyc311.analysis`
- `nyc311.geographies`
- `nyc311.samples`
- `nyc311.export`
- `nyc311.pipeline`
- `nyc311.dataframes`
- `nyc311.spatial`
- `nyc311.plotting`

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
