# Community District Choropleth

This example builds a community-district dominant-topic choropleth from a cached
live `Noise - Residential` slice, then turns it into a tracked tearsheet with
full-layer map context and supporting charts.

## Questions This Example Answers

- Which districts in the cached slice skew hardest toward party music?
- Which districts have the strongest dominant-topic signal?
- Which districts have the flattest topic mix?
- Which districts appear in the full layer but not in the cached slice?

## Local Repo Usage

```bash
cd examples/community-district-choropleth
uv sync
uv run python main.py
```

To force a new network fetch:

```bash
uv run python main.py --refresh
```

To publish a tracked tearsheet for the current cached slice:

```bash
uv run python main.py --publish-report
```

## Public Package Shape

```bash
pip install "nyc311[spatial,plotting]"
python main.py
```

## Output Layout

- `cache/`: ignored cached live snapshot
- `artifacts/`: ignored scratch topic-summary CSVs
- `reports/`: tracked tearsheet and tracked report figures published on demand

Running the example writes:

- `cache/community-district-noise-snapshot.csv`
- `artifacts/community-district-topic-summaries.csv`
- `artifacts/community-district-dominant-topic-summaries.csv`

When `--publish-report` is passed, it also writes:

- `reports/community-district-choropleth-tearsheet.md`
- `reports/figures/community-district-dominant-noise-topics.png`
- `reports/figures/community-district-party-music-intensity.png`
- `reports/figures/community-district-topic-mix-topn.png`

## Notes

- defaults to a larger cached Q1 2025 Brooklyn `Noise - Residential` slice
- uses the full packaged community-district layer so no-data areas stay visible
- updates tracked report assets only when `--publish-report` is passed
