# Spatial Join QA

This is the canonical spatial QA example for `nyc311`. It combines the old
boundary-coverage audit and the old point-to-boundary join preview into one
report-rich workflow over the packaged sample records and the packaged
sample-aligned community-district subset.

## Questions This Example Answers

- What share of packaged sample points joins successfully to the sampled
  district subset?
- Which rows remain unmatched?
- How often does the raw `community_district` text agree with the spatial join?
- Which sampled polygons receive no matched sample points?
- Which sampled districts receive the most matched records?

## Local Repo Usage

```bash
cd examples/spatial-join-qa
uv sync
uv run python main.py
```

## Public Package Shape

```bash
pip install "nyc311[spatial,plotting]"
python main.py
```

## Output Layout

- `artifacts/`: ignored boundary inventory, join preview, unmatched rows, and
  raw-vs-spatial QA tables
- `reports/`: tracked tearsheet and tracked report figures

Running the example writes:

- `artifacts/spatial-join-qa-boundary-summary.csv`
- `artifacts/spatial-join-qa-join-preview.csv`
- `artifacts/spatial-join-qa-unmatched-points.csv`
- `artifacts/spatial-join-qa-text-vs-spatial.csv`
- `artifacts/spatial-join-qa-joined-district-counts.csv`
- `reports/spatial-join-qa-tearsheet.md`
- `reports/figures/spatial-join-qa-match-status-map.png`
- `reports/figures/spatial-join-qa-coverage-breakdown.png`
- `reports/figures/spatial-join-qa-joined-district-counts.png`

## Notes

- uses packaged sample records and packaged sample-aligned boundaries
- keeps the full city district layer as background context while auditing the
  sampled subset
- does not create or depend on a cache
