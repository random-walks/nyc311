# Borough Choropleth

This example builds a borough-level dominant-topic choropleth from packaged
sample records and the packaged borough boundary layer, then turns the results
into a beginner-friendly markdown report with tracked figures.

## Local Repo Usage

```bash
cd examples/borough-choropleth
uv sync
uv run python main.py
```

## Public Package Shape

```bash
pip install "nyc311[spatial,plotting]"
python main.py
```

## Output Layout

- `artifacts/`: ignored scratch outputs and intermediate CSVs
- `reports/`: tracked markdown and report figures

Running the example writes:

- `artifacts/borough-topic-summaries.csv`
- `artifacts/borough-dominant-topic-summaries.csv`
- `reports/borough-choropleth-tearsheet.md`
- `reports/figures/borough-dominant-noise-topics.png`
- `reports/figures/borough-party-music-intensity.png`
- `reports/figures/borough-topic-mix-facets.png`

## Notes

- uses packaged sample records only
- does not create or depend on a cache
- keeps report-ready assets separate from heavier untracked artifacts
