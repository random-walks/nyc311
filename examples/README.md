# Examples

This folder contains copy-paste starting points for the `nyc311` CLI and SDK.

## Layout

- `scripts/quickstart_csv.py`: fetch live data, analyze it in memory, and write
  a first topic-summary CSV
- `scripts/fetch_filtered_snapshot.py`: fetch a filtered Socrata slice and save
  it as a reproducible local CSV snapshot, or skip export and inspect records in
  memory only
- `scripts/community_district_case_study.py`: a small case study / EDA-style
  workflow over a larger Brooklyn live sample
- `notebooks/quickstart_sdk.ipynb`: notebook version of the SDK quickstart
- `notebooks/community_district_case_study.ipynb`: notebook Brooklyn EDA case
  study

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
```

To fetch a live snapshot:

```bash
uv run python examples/scripts/fetch_filtered_snapshot.py --help
```

## Notes

These examples intentionally start from no local data. They fetch a live Socrata
slice first, then analyze that in memory or export a snapshot if needed.
