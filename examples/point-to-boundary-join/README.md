# Point To Boundary Join

This example turns packaged sample records into points, joins them to packaged
community-district boundaries, and writes a tracked tearsheet about join
coverage, unmatched rows, and raw-vs-spatial label agreement.

## Questions This Example Answers

- What share of sample points joins successfully to a district polygon?
- Which rows remain unmatched?
- How often does the raw district label agree with the spatial assignment?
- Which joined districts receive the most sample records?

## Local Repo Usage

```bash
cd examples/point-to-boundary-join
uv sync
uv run python main.py
```

## Public Package Shape

```bash
pip install "nyc311[spatial,plotting]"
python main.py
```

## Output Layout

- `artifacts/`: ignored join preview CSVs and scratch QA tables
- `reports/`: tracked tearsheet and tracked report figures

Running the example writes:

- `artifacts/point-boundary-join.csv`
- `artifacts/point-boundary-unmatched.csv`
- `artifacts/point-boundary-text-vs-spatial.csv`
- `reports/point-to-boundary-join-tearsheet.md`
- `reports/figures/point-boundary-match-status-map.png`
- `reports/figures/point-boundary-join-rate.png`
- `reports/figures/point-boundary-joined-districts.png`

## Notes

- uses packaged sample records and packaged sample-aligned boundaries
- does not create or depend on a cache
- keeps report-ready figures separate from heavier scratch join outputs
