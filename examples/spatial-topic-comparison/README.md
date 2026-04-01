# Spatial Topic Comparison

This example spatially enriches a cached live `Noise - Residential` slice,
re-aggregates deterministic topics by the spatially joined district polygons,
compares the raw district labels to the joined districts, and writes a tracked
tearsheet about how the story changes after the full-city join.

## Questions This Example Answers

- Which joined districts skew hardest toward party music?
- Which joined districts show the strongest dominant-topic signal?
- Which joined districts have the most balanced topic mix?
- Which rows change district when spatial geometry overrides the raw label?

## Local Repo Usage

```bash
cd examples/spatial-topic-comparison
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
- `artifacts/`: ignored joined topic summaries and scratch preview tables
- `reports/`: tracked tearsheet and tracked report figures published on demand

Running the example writes:

- `cache/spatial-topic-comparison-noise-snapshot.csv`
- `artifacts/spatial-topic-comparison.csv`
- `artifacts/spatial-topic-joined-preview.csv`
- `artifacts/spatial-topic-unmatched.csv`
- `artifacts/spatial-topic-raw-vs-joined.csv`
- `artifacts/spatial-topic-reassignments.csv`

When `--publish-report` is passed, it also writes:

- `reports/spatial-topic-comparison-tearsheet.md`
- `reports/figures/spatial-topic-comparison-preview.png`
- `reports/figures/spatial-dominant-noise-topics.png`
- `reports/figures/spatial-party-music-intensity.png`
- `reports/figures/spatial-topic-mix-by-district.png`

## Notes

- defaults to the same larger cached Q1 2025 Brooklyn `Noise - Residential`
  slice as the district choropleth example
- uses a custom joined-district aggregation so the report reflects spatially
  assigned polygons instead of the raw record geography field
- keeps a raw-vs-spatial comparison artifact so readers can see where the join
  meaningfully changes the district assignment
- updates tracked report assets only when `--publish-report` is passed
