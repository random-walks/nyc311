# Examples

The repository ships quickstart scripts and notebooks in `examples/`.

## Included Examples

- `examples/scripts/quickstart_csv.py`
- `examples/scripts/fetch_filtered_snapshot.py`
- `examples/scripts/community_district_case_study.py`
- `examples/notebooks/quickstart_sdk.ipynb`
- `examples/notebooks/community_district_case_study.ipynb`

## Recommended Workflow For Large Datasets

For larger data-science workflows:

1. fetch a narrow live slice from Socrata
2. save it as a local CSV snapshot
3. iterate on analysis against the local file
4. keep large artifacts out of git

That pattern is easier to debug, easier to reproduce, and friendlier to the
Socrata API than pulling large live datasets for every notebook run.

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
uv run python examples/scripts/quickstart_csv.py
uv run python examples/scripts/community_district_case_study.py
uv run python examples/scripts/fetch_filtered_snapshot.py
```
