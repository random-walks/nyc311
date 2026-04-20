# Integration with factor-factory and jellycell

Starting in v1.0.0, `nyc311` integrates with two upstream packages:

- [**factor-factory**](https://github.com/random-walks/factor-factory) — a
  17-engine-family causal-inference framework. `nyc311` ships a pair of additive
  adapters that route `PanelDataset`s and `Pipeline`s into factor-factory
  engines.
- [**jellycell**](https://github.com/random-walks/jellycell) — a reporting /
  tearsheet library. `nyc311`'s case studies optionally emit jellycell
  manuscripts alongside the existing `FINDINGS.md`.

The integration is additive: the existing `nyc311.factors.Pipeline`,
`nyc311.temporal.PanelDataset`, and `nyc311.stats.*` APIs are unchanged.

## The two adapters

### `PanelDataset.to_factor_factory_panel()`

Converts a nyc311 panel into a
[`factor_factory.tidy.Panel`](https://factor-factory.readthedocs.io/):

```python
from nyc311.temporal import build_complaint_panel, TreatmentEvent
from nyc311.temporal import build_distance_weights, centroids_from_boundaries

panel = build_complaint_panel(
    records,
    geography="community_district",
    freq="ME",
    treatment_events=[event],
)

# Optional: carry spatial weights through via df.attrs.
weights = build_distance_weights(
    centroids_from_boundaries(boundaries), threshold_meters=2000
)

ff_panel = panel.to_factor_factory_panel(
    outcome_col="complaint_count",
    spatial_weights=weights,
)
```

Mapping:

| `PanelDataset`                                   | `factor_factory.tidy.Panel`                             |
| ------------------------------------------------ | ------------------------------------------------------- |
| `unit_id`                                        | First-level MultiIndex, named `unit_id`                 |
| `period` (`"2024-03"` string)                    | Second-level MultiIndex, `pandas.Timestamp` at start    |
| `complaint_count`                                | Primary outcome column (configurable via `outcome_col`) |
| `resolution_rate`, `median_resolution_days`, ... | Additional columns (available as covariates)            |
| `treatment` (`bool`)                             | `treatment` int column (`0`/`1`)                        |
| `TreatmentEvent` tuples                          | `PanelMetadata.treatment_events`                        |
| `unit_type`                                      | `PanelMetadata.dimension`                               |
| `spatial_weights=...`                            | `panel.df.attrs["nyc311_spatial_weights"]`              |

Recover the weights with `nyc311.temporal.spatial_weights_from_panel(panel)`.

### `Pipeline.as_factor_factory_estimate()`

Dispatches to `factor_factory.engines.<family>.estimate` on a panel:

```python
from nyc311.factors import Pipeline, ComplaintVolumeFactor

pipeline = Pipeline().add(ComplaintVolumeFactor())
ff_panel = dataset.to_factor_factory_panel()

did_results = pipeline.as_factor_factory_estimate(
    ff_panel,
    family="did",
    method="twfe",
    outcome="complaint_count",
)
```

The returned object is a factor-factory `<Family>Results`. For `family="did"`
that's `DidResults` — iterable, with `[0].att`, `[0].se`, `[0].ci_95`, etc.

Supported `family` values match `factor_factory.engines.*`: `did`, `sdid`,
`mediation`, `rdd`, `scm`, `changepoint`, `stl`, `panel_reg`, `inequality`,
`spatial`, `reporting_bias`, `hawkes`, `survival`, `event_study`, `het_te`,
`dml`, `climate`, `diffusion`.

## Stats-module crosswalk

As of v1.0.0, eleven of `nyc311.stats`'s seventeen modules have a factor-factory
equivalent. Their module docstrings now cross-reference the upstream engine with
a `.. note:: factor-factory preferred` block. The homegrown implementation
remains authoritative for backwards compatibility but will not grow new methods.

| `nyc311.stats` module      | Method                                        | factor-factory                                       |
| -------------------------- | --------------------------------------------- | ---------------------------------------------------- |
| `_staggered_did`           | Callaway-Sant'Anna / TWFE / Sun-Abraham / BJS | `engines.did.{cs,twfe,sa,bjs}`                       |
| `_synthetic_control`       | SCM                                           | `engines.scm.{augmented,matrix_completion,pysyncon}` |
| `_rdd`                     | CCT robust local poly                         | `engines.rdd.rd_robust`                              |
| `_changepoint`             | PELT / binseg                                 | `engines.changepoint.ruptures`                       |
| `_decomposition`           | STL                                           | `engines.stl.sktime_stl`                             |
| `_panel_models`            | FE / RE                                       | `engines.panel_reg.pyfixest`                         |
| `_equity.theil_index`      | Theil T                                       | `engines.inequality.theil_t`                         |
| `_spatial.global_morans_i` | Global Moran's I                              | `engines.spatial.morans_i`                           |
| `_reporting_bias`          | Latent-EM                                     | `engines.reporting_bias.latent_em`                   |
| `_hawkes`                  | Hawkes self-exciting                          | `engines.hawkes.tick`                                |
| `_anomaly`                 | STL residual anomaly                          | `engines.stl.sktime_stl` (residual)                  |

Not covered upstream (`nyc311.stats` remains authoritative):

- `_bym2` (Bayesian small-area smoothing — PyMC native)
- `_gwr` (geographically-weighted regression)
- `_equity.oaxaca_blinder`
- `_power` (power analysis helper)
- `_spatial_regression` (spatial lag / error)
- `_its` (segmented-regression ITS; a DiD-like approximation is in
  factor-factory but not a direct ITS)

See
[`.claude/skills/stats-module-discipline.md`](https://github.com/random-walks/nyc311/blob/main/.claude/skills/stats-module-discipline.md)
for the rule: new statistical methods go through factor-factory first; homegrown
only with an explicit RFC.

## Tearsheets

Installing the optional `tearsheets` extra pulls in jellycell:

```bash
pip install "nyc311[tearsheets]"
```

With the `tearsheets` extra, the two precious case studies and the two new ones
emit
[`factor_factory.jellycell.tearsheets`](https://factor-factory.readthedocs.io/en/latest/jellycell/)
manuscripts in addition to their native `FINDINGS.md` output. The tearsheet set
for each case study:

- `manuscripts/METHODOLOGY.md`
- `manuscripts/DIAGNOSTICS_CHECKLIST.md`
- `manuscripts/FINDINGS.md`
- `manuscripts/MANUSCRIPT.md` (stub; human-authored after first run)
- `manuscripts/AUDIT.md`

Each case study ships a `jellycell.toml` alongside its `run_analysis.py` so
`uv run jellycell render` works in-place.

## Version ranges

| Package           | v1.0.0 pin                             |
| ----------------- | -------------------------------------- |
| `factor-factory`  | `>=1.0.2,<2`                           |
| `jellycell`       | `>=1.3.5,<2` (via `tearsheets` extra)  |
| `nyc-geo-toolkit` | `>=0.3.0,<0.4`                         |
| Python            | `>=3.12` (dropped 3.10/3.11 in v1.0.0) |

Follow the
[factor-factory roadmap](https://github.com/random-walks/factor-factory/blob/main/docs/og_context/06_post_v0.1_roadmap.md)
for upcoming engine families; most new engines become available to
`Pipeline.as_factor_factory_estimate` automatically the moment the dependency
pin accepts them.
