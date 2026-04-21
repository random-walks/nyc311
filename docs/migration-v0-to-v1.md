# Migration guide: v0.3 → v1.0

`nyc311` v1.0.0 is the first major release. The primary driver is the
**factor-factory integration** (see [integration.md](integration.md)); the rest
of this page is the consumer checklist.

## TL;DR — what changed

1. **Python floor**: dropped 3.10 and 3.11 support. **Minimum is 3.12.**
   Upstream factor-factory requires 3.12+.
2. **New default dependencies**: `factor-factory>=1.0.2,<2` is now a core
   dependency.
3. **New optional extra**: `tearsheets = ["jellycell>=1.3.5,<2"]`.
4. **New bridges**: `nyc311.temporal.PanelDataset.to_factor_factory_panel()` and
   `nyc311.factors.Pipeline.as_factor_factory_estimate()`.
5. **Stats modules annotated**: eleven `nyc311.stats` modules now
   cross-reference their factor-factory equivalents in a `.. note::` block.
6. **CI matrix** expanded to ubuntu/macOS/Windows × Python 3.12/3.13.

Nothing in your existing code should break unless you were on Python < 3.12 or
depended on an import path changing. Concretely, the following existing APIs
continue to work unchanged:

- `nyc311.factors.Pipeline`, `.add()`, `.run()`, `PipelineResult`
- `nyc311.temporal.PanelDataset`, its dataclass fields, filter helpers, and
  `.to_dataframe()`
- `nyc311.temporal.TreatmentEvent`, `nyc311.temporal.PanelObservation`
- `nyc311.temporal.build_complaint_panel`, `build_distance_weights`,
  `centroids_from_boundaries`, `weights_to_pysal`
- Every function and dataclass exported from `nyc311.stats`
- The `nyc311 fetch` and `nyc311 topics` CLI subcommands

## Upgrade steps

### 1. Bump your Python floor

If you pin `nyc311>=0.3,<0.4` and run on Python 3.10 or 3.11, you have two
options:

- **Stay on nyc311 v0.3.x** and keep your current Python. nyc311 will not
  backport changes to the 0.x line.
- **Upgrade Python to 3.12 (or 3.13) first**, then bump to `nyc311>=1.0,<2`.

Your `pyproject.toml`:

```diff
 [project]
-requires-python = ">=3.10"
+requires-python = ">=3.12"
 dependencies = [
-  "nyc311>=0.3,<0.4",
+  "nyc311>=1.0,<2",
 ]
```

### 2. (Optional) Add the `tearsheets` extra

If you want jellycell manuscript output from the case studies:

```diff
 [project.optional-dependencies]
-my-extra = ["nyc311>=1.0,<2"]
+my-extra = ["nyc311[tearsheets]>=1.0,<2"]
```

### 3. (Optional) Wire PanelDataset into factor-factory

Old code that hand-rolled a factor-factory `Panel` from nyc311 records:

```python
# v0.3-era boilerplate (no adapter)
import pandas as pd
from factor_factory.tidy import Panel, PanelMetadata

df = pd.DataFrame(...)  # from dataset.to_dataframe() + manual munging
panel = Panel(df, PanelMetadata(outcome_cols=("complaint_count",), ...))
```

v1.0:

```python
from nyc311.temporal import build_complaint_panel

dataset = build_complaint_panel(records, geography="community_district")
panel = dataset.to_factor_factory_panel()
# Now `panel.summary()`, `panel.outcome_col`, engines.did.estimate(panel) all work.
```

### 4. (Optional) Swap homegrown stats calls for factor-factory

For engine families with factor-factory coverage (see the
[stats crosswalk](integration.md#stats-module-crosswalk)), you can replace the
homegrown nyc311 call:

```python
# Before
from nyc311.stats import synthetic_control

scm_result = synthetic_control(
    panel=dataset,
    treated_unit="MANHATTAN 03",
    outcome="complaint_count",
    n_placebo_runs=200,
)
att = scm_result.att
```

```python
# After
ff_panel = dataset.to_factor_factory_panel()
from factor_factory.engines.scm import estimate as scm_estimate

scm_results = scm_estimate(
    ff_panel,
    methods=("augmented",),
    outcome="complaint_count",
)
records = scm_results.to_records()
att = records[0]["att"]
```

Both paths are supported in v1.0. The homegrown call will not grow new features;
prefer the factor-factory call for new code.

### 5. CI

If you pin actions in your own CI, the factor-factory / v1.0.0 set are:

```yaml
- uses: actions/checkout@v6
- uses: astral-sh/setup-uv@v8.1.0 # exact — no moving tag
- uses: actions/upload-artifact@v7
- uses: actions/download-artifact@v8
```

## Removed / renamed

**None.** v1.0.0 does not rename or remove any public API. The
`nyc311.factors.Pipeline` and `nyc311.temporal.PanelDataset` shapes are
unchanged. The new bridges are strictly additive.

## Deprecated

Nothing is deprecated in v1.0.0. A future minor may deprecate specific
`nyc311.stats` methods in favor of the factor-factory equivalent, but only with
a full deprecation cycle (two minors of warning before removal).

## v1.0.1 + v1.0.2 addenda

Two patch releases landed same-week as v1.0.0 in response to downstream
dogfooding signal. Both are **strictly additive**, no consumer code needs to
change, but you can opt into two small API improvements:

### `ServiceRequestRecord.closed_date` (v1.0.1, see [#20](https://github.com/random-walks/nyc311/issues/20))

`closed_date: date | None` is now a first-class field on the record, carried
end-to-end through CSV ingest / export, dataframe helpers, and the Socrata
`$select`. Unresolved complaints surface as `None` (pandas `NaT` in
`datetime64[ns]` columns). Resolution-time analysis becomes a one-liner:

```python
# Before — had to bypass the SDK and hit Socrata directly
import aiohttp

async with aiohttp.ClientSession() as session:
    ...  # manual $select=..., closed_date + pagination
```

```python
# After
from nyc311 import io, models

records = io.load_service_requests(
    "data/cache/noise-2020-2024.csv",
    filters=models.ServiceRequestFilter(complaint_types=("Noise - Residential",)),
)
resolved = [r for r in records if r.closed_date is not None]
latencies = [(r.closed_date - r.created_date).days for r in resolved]
```

CSV snapshots written by pre-v1.0.1 SDKs load without the column (it's
optional); fresh snapshots written by v1.0.1+ include it.

### `nyc-geo-toolkit>=0.3.0,<0.5` pin (v1.0.2)

The pin widened to allow installing
[nyc-geo-toolkit v0.4.0](https://github.com/random-walks/nyc-geo-toolkit/releases/tag/v0.4.0)
alongside nyc311. Upstream v0.4.0 adds a shapely-backed
`centroids_from_boundaries` helper that returns a `BoundaryCollection` of
GeoJSON `Point` features with optional `representative_point=True` for
non-convex polygons (useful for NYC's jagged community districts).

nyc311's own `nyc311.temporal.centroids_from_boundaries` stays as-is — it's the
shapely-free path, returns `dict[str, (lat, lon)]`, and feeds directly into
`build_distance_weights`. Don't swap them mid-analysis (the two return different
shapes and slightly different numbers). See the cross-reference note in that
function's docstring for the full decision table.

For publication-grade geometry:

```python
from nyc_geo_toolkit import centroids_from_boundaries, load_nyc_boundaries

cbs = load_nyc_boundaries("community_district")
centroid_collection = centroids_from_boundaries(cbs, representative=True)
centroids = {
    f.geography_value: (f.geometry["coordinates"][1], f.geometry["coordinates"][0])
    for f in centroid_collection.features
}
```

## Questions

Open an issue on [GitHub](https://github.com/random-walks/nyc311/issues). If you
are migrating an academic analysis, cite the specific nyc311 release you used;
the `CITATION.cff` file in the repo root covers the two case-study artifacts
bundled with this release.
