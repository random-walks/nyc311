# Examples

The repository ships quickstart scripts and notebooks in `examples/`.

These examples match the current `0.2` alpha prerelease surface on this branch.

## Included Examples

- `examples/scripts/quickstart_csv.py`
- `examples/scripts/fetch_filtered_snapshot.py`
- `examples/scripts/community_district_case_study.py`
- `examples/scripts/topic_eda.py`
- `examples/scripts/borough_choropleth.py`
- `examples/scripts/point_to_boundary_join.py`
- `examples/notebooks/quickstart_sdk.ipynb`
- `examples/notebooks/community_district_case_study.ipynb`
- `examples/notebooks/topic_eda.ipynb`
- `examples/notebooks/community_district_choropleth.ipynb`
- `examples/notebooks/spatial_topic_comparison.ipynb`
- `examples/notebooks/boundary_qa.ipynb`

The notebooks are now pure in-memory consumers of `nyc311` APIs. They use:

- `nyc311.load_sample_service_requests()`
- `nyc311.load_sample_boundaries()`
- packaged NYC boundary layers exposed via `nyc311.load_nyc_boundaries*()`
- in-memory plotting helpers such as `nyc311.plot_boundary_preview()`

The packaged geography catalog now includes boroughs, community districts, city
council districts, neighborhood tabulation areas, MODZCTAs, and census tracts.

The file-oriented `examples/data/` and `examples/utils/` helpers remain
available for scripts and ad hoc exploration, but notebooks no longer depend on
them.

## Recommended Workflow For Large Datasets

For larger data-science workflows:

1. fetch a narrow live slice from Socrata
2. save it as a local CSV snapshot
3. iterate on analysis against the local file
4. keep large artifacts out of git

That pattern is easier to debug, easier to reproduce, and friendlier to the
Socrata API than pulling large live datasets for every notebook run. The
library-owned sample loaders provide the same reproducible workflow for notebook
examples that should run without local file setup.

## Start With A Snapshot

The CLI now supports:

```bash
nyc311 fetch \
  --output local-noise-snapshot.csv \
  --complaint-type "Noise - Residential" \
  --geography borough \
  --geography-value BROOKLYN \
  --start-date 2025-01-01 \
  --end-date 2025-01-31 \
  --page-size 500 \
  --max-pages 2
```

Then run your local analysis against that snapshot:

```bash
nyc311 topics \
  --source local-noise-snapshot.csv \
  --complaint-type "Noise - Residential" \
  --geography community_district \
  --output topics.csv
```

## Running Repo Examples

From the repo root:

```bash
uv sync --all-groups --all-extras
uv run python examples/scripts/quickstart_csv.py
uv run python examples/scripts/community_district_case_study.py
uv run python examples/scripts/fetch_filtered_snapshot.py
uv run python examples/scripts/topic_eda.py
uv run python examples/scripts/borough_choropleth.py
uv run python examples/scripts/point_to_boundary_join.py
```

The dataframe and notebook-oriented examples rely on the optional `dataframes`
or `science` extras. The new geography-forward examples additionally rely on the
`spatial` extra. `make install` already includes the core contributor
dependencies; add `uv sync --extra spatial --extra science` when you want to run
the mapping notebooks and scripts.
