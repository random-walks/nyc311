# Examples

This folder contains copy-paste starting points for the `nyc311` CLI and SDK.

## Layout

- `data/`: small offline demo datasets for geography-forward examples
- `scripts/quickstart_csv.py`: fetch live data, analyze it in memory, and write
  a first topic-summary CSV
- `scripts/fetch_filtered_snapshot.py`: fetch a filtered Socrata slice and save
  it as a reproducible local CSV snapshot, or skip export and inspect records in
  memory only
- `scripts/community_district_case_study.py`: a small case study / EDA-style
  workflow over a larger Brooklyn live sample
- `scripts/topic_eda.py`: raw-data audit workflow for topic coverage, anomalies,
  and report-card output
- `scripts/borough_choropleth.py`: offline borough-level categorical choropleth
  from the demo spatial dataset
- `scripts/point_to_boundary_join.py`: offline point-in-polygon join example
- `notebooks/quickstart_sdk.ipynb`: notebook version of the SDK quickstart
- `notebooks/community_district_case_study.ipynb`: notebook Brooklyn EDA case
  study
- `notebooks/topic_eda.ipynb`: notebook version of the topic-coverage audit
- `notebooks/community_district_choropleth.ipynb`: offline district-level map
- `notebooks/spatial_topic_comparison.ipynb`: offline joined-topic comparison
- `notebooks/boundary_qa.ipynb`: quick QA pass over the demo boundary files
- `utils/`: shared helpers for paths, filters, plotting, display, and geo maps

## Best-Practice Workflow For Large Datasets

For larger datasets, the cleanest data-science workflow is:

1. filter as early as possible at the source
2. fetch a local snapshot for reproducibility
3. keep large snapshots out of git
4. do iterative EDA and modeling against the local snapshot, not the live API

In practical `nyc311` terms:

- use `nyc311.fetch_service_requests(...)` or `nyc311 fetch`
- start with `--max-pages` during development
- save the snapshot outside the repo or under an ignored local data directory
- rerun the same CLI/SDK logic against the cached CSV when iterating

## Running The Scripts

From the repo root:

```bash
uv run python examples/scripts/quickstart_csv.py
uv run python examples/scripts/community_district_case_study.py
uv run python examples/scripts/topic_eda.py
```

To fetch a live snapshot:

```bash
uv run python examples/scripts/fetch_filtered_snapshot.py --help
```

To run the offline spatial demos:

```bash
uv sync --extra spatial --extra science
uv run python examples/scripts/borough_choropleth.py
uv run python examples/scripts/point_to_boundary_join.py
```

## Notes

These examples intentionally start from no local data. They fetch a live Socrata
slice first, then analyze that in memory or export a snapshot if needed.

The new geography-forward examples also ship with a tiny offline dataset under
`examples/data/` so you can try the spatial helpers without relying on a live
API call.
