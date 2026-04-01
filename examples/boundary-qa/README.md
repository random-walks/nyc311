# Boundary QA

This example audits the packaged sample points against the packaged
community-district boundary layer, then turns the results into a tracked QA
tearsheet with stable figures.

## Questions This Example Answers

- What share of packaged sample points falls inside the boundary layer?
- Which sample points fall outside every polygon?
- How often does the raw `community_district` text agree with the spatial join?
- Which packaged sample polygons receive no matched points?

## Local Repo Usage

```bash
cd examples/boundary-qa
uv sync
uv run python main.py
```

## Public Package Shape

```bash
pip install "nyc311[spatial,plotting]"
python main.py
```

## Output Layout

- `artifacts/`: ignored scratch QA tables and boundary inventory CSVs
- `reports/`: tracked tearsheet and tracked report figures

Running the example writes:

- `artifacts/boundary-summary.csv`
- `artifacts/boundary-unmatched-points.csv`
- `artifacts/boundary-text-vs-spatial.csv`
- `reports/boundary-qa-tearsheet.md`
- `reports/figures/boundary-match-status-map.png`
- `reports/figures/boundary-coverage-breakdown.png`

## Notes

- uses packaged sample records and packaged sample-aligned boundaries
- does not create or depend on a cache
- keeps report-ready assets separate from heavier untracked QA tables
