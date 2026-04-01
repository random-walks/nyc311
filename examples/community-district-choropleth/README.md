# Community District Choropleth

This example builds a community-district dominant-topic choropleth from the
packaged `Noise - Residential` sample, then turns it into a tracked tearsheet
with full-layer map context and supporting charts.

## Questions This Example Answers

- Which sampled districts skew hardest toward party music?
- Which districts have the strongest dominant-topic signal?
- Which districts have the flattest topic mix?
- Which districts appear in the full layer but not in the packaged sample?

## Local Repo Usage

```bash
cd examples/community-district-choropleth
uv sync
uv run python main.py
```

## Public Package Shape

```bash
pip install "nyc311[spatial,plotting]"
python main.py
```

## Output Layout

- `artifacts/`: ignored scratch topic-summary CSVs
- `reports/`: tracked tearsheet and tracked report figures

Running the example writes:

- `artifacts/community-district-topic-summaries.csv`
- `artifacts/community-district-dominant-topic-summaries.csv`
- `reports/community-district-choropleth-tearsheet.md`
- `reports/figures/community-district-dominant-noise-topics.png`
- `reports/figures/community-district-party-music-intensity.png`
- `reports/figures/community-district-topic-mix-topn.png`

## Notes

- uses packaged sample records only
- uses the full packaged community-district layer so no-data areas stay visible
- does not create or depend on a cache
