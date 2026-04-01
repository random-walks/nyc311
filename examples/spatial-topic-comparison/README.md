# Spatial Topic Comparison

This example spatially enriches the packaged `Noise - Residential` sample,
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

## Public Package Shape

```bash
pip install "nyc311[spatial,plotting]"
python main.py
```

## Output Layout

- `artifacts/`: ignored joined topic summaries and scratch preview tables
- `reports/`: tracked tearsheet and tracked report figures

Running the example writes:

- `artifacts/spatial-topic-comparison.csv`
- `artifacts/spatial-topic-joined-preview.csv`
- `artifacts/spatial-topic-unmatched.csv`
- `artifacts/spatial-topic-raw-vs-joined.csv`
- `artifacts/spatial-topic-reassignments.csv`
- `reports/spatial-topic-comparison-tearsheet.md`
- `reports/figures/spatial-topic-comparison-preview.png`
- `reports/figures/spatial-dominant-noise-topics.png`
- `reports/figures/spatial-party-music-intensity.png`
- `reports/figures/spatial-topic-mix-by-district.png`

## Notes

- uses packaged sample records and the full packaged community-district layer
- does not create or depend on a cache
- uses a custom joined-district aggregation so the report reflects spatially
  assigned polygons instead of the raw record geography field
- keeps a raw-vs-spatial comparison artifact so readers can see where the join
  meaningfully changes the district assignment
