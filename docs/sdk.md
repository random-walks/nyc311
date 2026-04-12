# SDK Guide

`nyc311` is usable as a functional SDK for scripts, scheduled jobs, interactive
analysis, and data-processing workflows.

This guide describes the current stable SDK surface in the `0.3.x` line.

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

## Bulk Per-Borough Downloads

For multi-year, full-city extracts, `nyc311.pipeline.bulk_fetch()` splits a
single logical query into one CSV per borough. Each completed CSV is paired
with a `.meta.json` sidecar capturing the row count, SHA-256 checksum, fetch
timestamp, and the filter parameters used. Subsequent calls skip any borough
whose file already exists, so you can resume an interrupted download.

```python
from datetime import date
from pathlib import Path

from nyc311.pipeline import bulk_fetch

paths = bulk_fetch(
    complaint_types=("Noise - Residential", "Rodent"),
    start_date=date(2023, 1, 1),
    end_date=date(2024, 12, 31),
    cache_dir=Path("data/cache"),
    on_progress=lambda boro, page, rows: print(f"{boro}: page {page} ({rows} rows)"),
)

for csv_path in paths:
    print(csv_path, csv_path.with_suffix(".meta.json"))
```

## Factor Pipelines

`nyc311.factors` provides a composable, immutable pipeline for computing
domain-specific metrics over geographic units. Each `Factor` consumes a
`FactorContext` (one geographic unit, one time window, the complaints inside
it, and optional population/extras) and returns a single value. A `Pipeline`
runs many factors over many contexts in a single pass and produces a columnar
`PipelineResult`.

```python
from datetime import date

from nyc311 import io, models
from nyc311.factors import (
    ComplaintVolumeFactor,
    FactorContext,
    Pipeline,
    ResponseRateFactor,
    TopicConcentrationFactor,
)

records = io.load_service_requests(
    "data/cache/brooklyn-2024.csv",
    filters=models.ServiceRequestFilter(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    ),
)

# Group records by community district into FactorContexts.
by_cd: dict[str, list[models.ServiceRequestRecord]] = {}
for rec in records:
    by_cd.setdefault(rec.community_district, []).append(rec)

contexts = [
    FactorContext(
        geography="community_district",
        geography_value=cd,
        complaints=tuple(complaints),
        time_window_start=date(2024, 1, 1),
        time_window_end=date(2024, 12, 31),
    )
    for cd, complaints in by_cd.items()
]

pipeline = (
    Pipeline()
    .add(ComplaintVolumeFactor())
    .add(ResponseRateFactor())
    .add(TopicConcentrationFactor())
)
result = pipeline.run(contexts)
df = result.to_dataframe()  # requires nyc311[dataframes]
print(df.sort_values("complaint_volume", ascending=False).head())
```

`Pipeline.add()` returns a **new** pipeline rather than mutating in place,
so pipelines are safe to compose and share between callers.

## Temporal Panels

`nyc311.temporal` builds balanced `(unit, period)` panels from raw
`ServiceRequestRecord` lists. Treatment events code policy interventions as
per-unit treatment indicators, and inverse-distance spatial weights feed
spatial-econometric workflows downstream.

```python
from datetime import date

from nyc311 import io
from nyc311.temporal import TreatmentEvent, build_complaint_panel

records = io.load_service_requests("data/cache/brooklyn-2023.csv")

panel = build_complaint_panel(
    records,
    geography="community_district",
    freq="ME",  # monthly
    treatment_events=(
        TreatmentEvent(
            name="rat_mitigation_zone_2023",
            description="DOHMH rat mitigation zone designation",
            treated_units=("BK01", "BK02", "BK03"),
            treatment_date=date(2023, 7, 1),
            geography="community_district",
        ),
    ),
)

treated = panel.treatment_group()
controls = panel.control_group()
df = panel.to_dataframe()  # MultiIndex (unit_id, period)
```

For spatial weights:

```python
from nyc311.geographies import load_nyc_boundaries
from nyc311.temporal import build_distance_weights, centroids_from_boundaries

boundaries = load_nyc_boundaries("community_district")
centroids = centroids_from_boundaries(boundaries)
weights = build_distance_weights(centroids, threshold_meters=2000.0)
```

## Statistical Modeling

`nyc311.stats` is a thin, typed layer over `statsmodels`, `ruptures`,
`linearmodels`, and `esda` / `libpysal`. Every routine is opt-in via the
`stats` extra and degrades cleanly with an `ImportError` when its dependency
is missing.

```python
from datetime import date

from nyc311.stats import (
    detect_changepoints,
    interrupted_time_series,
    seasonal_decompose,
)

# A pandas Series of monthly complaint counts indexed by month.
series = panel.to_dataframe()["complaint_count"].groupby(level="period").sum()
series.index = series.index.to_timestamp()

decomposition = seasonal_decompose(series, period=12)
breaks = detect_changepoints(series, method="pelt")
its = interrupted_time_series(series, intervention_date=date(2023, 7, 1))

print(its.level_change, its.p_value_level)
```

For panel regressions:

```python
from nyc311.stats import panel_fixed_effects

result = panel_fixed_effects(
    panel,
    outcome="complaint_count",
    regressors=("resolution_rate",),
    time_effects=True,
    cluster="entity",
)
print(result.coefficients, result.r_squared)
```

For spatial autocorrelation:

```python
from nyc311.stats import global_morans_i, local_morans_i

values = {row.Index[0]: row.complaint_count for row in df.itertuples()}
moran = global_morans_i(values, weights)
lisa = local_morans_i(values, weights, permutations=999)
```

### Causal Inference

```python
from nyc311.stats import synthetic_control, staggered_did, event_study, regression_discontinuity

# Synthetic control — counterfactual from donor units
result = synthetic_control(panel, treated_unit="BROOKLYN 03", outcome="complaint_count")
print(result.att, result.donor_weights)

# Staggered difference-in-differences (Callaway–Sant'Anna 2021)
did = staggered_did(panel, outcome="complaint_count")
print(did.aggregated_att, did.aggregated_p_value)

# Event-study plot with pre-trend test
es = event_study(panel, outcome="complaint_count", pre_periods=5, post_periods=5)
print(es.coefficients, es.pre_trend_p_value)

# Sharp regression discontinuity
rd = regression_discontinuity(running_var, outcome, cutoff=0.0)
print(rd.treatment_effect, rd.p_value)
```

### Spatial Econometrics

```python
from nyc311.stats import (
    spatial_lag_model,
    spatial_error_model,
    geographically_weighted_regression,
)

# Spatial lag model (Anselin 1988)
slm = spatial_lag_model(panel, weights, "complaint_count", ("income", "density"))
print(slm.rho, slm.coefficients)

# Spatial error model
sem = spatial_error_model(panel, weights, "complaint_count", ("income", "density"))
print(sem.lam, sem.coefficients)

# Geographically weighted regression (Brunsdon et al. 1996)
gwr = geographically_weighted_regression(values, regressors, coordinates)
print(gwr.local_coefficients, gwr.bandwidth)
```

### Equity & Bias Analysis

```python
from nyc311.stats import (
    oaxaca_blinder_decomposition,
    theil_index,
    reporting_rate_adjustment,
    latent_reporting_bias_em,
)

# Oaxaca-Blinder decomposition — explain resolution-time gaps
ob = oaxaca_blinder_decomposition(
    group_a_df, group_b_df, "resolution_days", ("income", "density")
)
print(ob.explained, ob.unexplained, ob.total_gap)

# Theil index — population-weighted inequality
ti = theil_index(rates, populations, groups=borough_map)
print(ti.total, ti.between_group, ti.within_group)

# Ecometric reporting-rate adjustment (O'Brien 2015)
adj = reporting_rate_adjustment(
    panel, "complaint_rate", ("median_income", "pop_density")
)
print(adj.adjusted_rates, adj.icc)

# Latent reporting-bias EM (Agostini et al. 2025)
em = latent_reporting_bias_em(counts, populations, covariates=covs)
print(em.estimated_true_rates, em.reporting_probabilities)
```

### Anomaly Detection & Power Analysis

```python
from nyc311.stats import detect_stl_anomalies, minimum_detectable_effect

# STL-residual anomaly detection
anomalies = detect_stl_anomalies(monthly_series, threshold=2.0)
print(anomalies.anomaly_dates, anomalies.n_anomalies)

# Power analysis for panel experiments
power = minimum_detectable_effect(n_units=59, n_periods=24, icc=0.05)
print(f"MDE: {power.mde:.3f} at 80% power")
```

### Bayesian Small-Area Smoothing

```python
from nyc311.stats import bym2_smooth

# BYM2 model (Riebler et al. 2016) — requires nyc311[bayes]
result = bym2_smooth(observed_counts, expected_counts, adjacency)
print(result.smoothed_rates, result.mixing_parameter)
```

### Self-Exciting Point Processes

```python
from nyc311.stats import fit_hawkes_process

# Hawkes process for complaint clustering (Mohler 2011)
hawkes = fit_hawkes_process(event_timestamps)
print(hawkes.background_rate, hawkes.branching_ratio)
```

Install the optional stats extra first:

```bash
pip install "nyc311[stats]"
pip install "nyc311[bayes]"            # BYM2 small-area smoothing (PyMC)
```

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
- `nyc311.presets`
- `nyc311.factors`
- `nyc311.temporal`
- `nyc311.stats` — time series, panel regression, spatial autocorrelation,
  causal inference, spatial econometrics, equity/bias analysis, anomaly
  detection, power analysis, Bayesian smoothing, and point processes

## When To Use The CLI Instead

Use the CLI when you want:

- a repeatable command in CI or a shell script
- a simple local CSV to artifact workflow
- no custom Python composition

Use the SDK when you want:

- Socrata ingestion
- interactive analysis or workflow orchestration
- custom filtering, branching, or intermediate inspection
- direct access to typed objects instead of files alone
