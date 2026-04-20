# Getting Started

This guide shows the fastest path to a useful `nyc311` run as either a CLI user
or a Python user.

It reflects the current stable `1.x` release surface. Python ≥ 3.12 is required
(factor-factory upstream floor).

## Install

```bash
pip install nyc311
```

For the full turnkey stack:

```bash
pip install "nyc311[all]"
```

For pandas-backed dataframe helpers, install:

```bash
pip install "nyc311[dataframes]"
```

For geopandas-backed geography and spatial helpers, install:

```bash
pip install "nyc311[spatial]"
```

For plotting helpers, install:

```bash
pip install "nyc311[plotting]"
```

For plotting and exploratory analysis without the geospatial stack, install:

```bash
pip install "nyc311[science]"
```

For development installs, use a lean or full environment:

```bash
uv sync
uv sync --all-groups --all-extras
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

## Optional dataframe helpers

`records_to_dataframe()`, `assignments_to_dataframe()`,
`summaries_to_dataframe()`, `gaps_to_dataframe()`, `anomalies_to_dataframe()`,
`coverage_to_dataframe()`, and `dataframe_to_records()` require the `dataframes`
extra (or the broader `science` extra) because they depend on pandas.

## Geography helpers

`nyc311.geographies` preserves a 311-facing packaged-boundary surface while the
generic boundary assets and normalization logic live in `nyc-geo-toolkit`.

The base install already supports typed packaged boundary loading:

```python
from nyc311 import geographies

print(geographies.list_boundary_layers())
boroughs = geographies.load_nyc_boundaries("borough")
```

If you want GeoDataFrame loaders, spatial joins, or plotting-backed notebooks,
install the relevant optional extras first.

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

summary = analysis.aggregate_by_geography(
    analysis.extract_topics(records, models.TopicQuery("Noise - Residential")),
    geography="community_district",
)
export.export_topic_table(
    summary,
    models.ExportTarget("csv", Path("topics.csv")),
)

print(f"rows: {len(summary)}")
```

## Add Date And Geography Filters

```python
from datetime import date
from pathlib import Path

from nyc311 import analysis, export, models, pipeline

records = pipeline.fetch_service_requests(
    filters=models.ServiceRequestFilter(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 3, 31),
        geography=models.GeographyFilter("borough", models.BOROUGH_BROOKLYN),
        complaint_types=("Noise - Residential",),
    ),
    socrata_config=models.SocrataConfig(page_size=500, max_pages=2),
)

summary = analysis.aggregate_by_geography(
    analysis.extract_topics(records, models.TopicQuery("Noise - Residential")),
    geography="community_district",
)
export.export_topic_table(
    summary,
    models.ExportTarget("csv", Path("brooklyn-noise-topics.csv")),
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

from nyc311 import analysis, models, pipeline

records = pipeline.fetch_service_requests(
    socrata_config=models.SocrataConfig(
        app_token=None,
        page_size=500,
        max_pages=2,
    ),
    filters=models.ServiceRequestFilter(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        complaint_types=("Rodent",),
    ),
)

assignments = analysis.extract_topics(records, models.TopicQuery("Rodent"))
summary = analysis.aggregate_by_geography(assignments, geography="borough")
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

from nyc311.pipeline import run_topic_pipeline

run_topic_pipeline(
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

Use `nyc311.models.supported_topic_queries()` to inspect that list from code.

## Next Steps

- Use [CLI Reference](cli.md) to see every current flag and option.
- Use [SDK Guide](sdk.md) to compose custom workflows.
- Use [Examples](examples.md) for self-contained consumer projects.
- Use [Architecture](architecture.md) if you are extending the package.
