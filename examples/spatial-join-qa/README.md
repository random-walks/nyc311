# Spatial Join QA

This is the canonical spatial QA example for `nyc311`. It combines the old
boundary-coverage audit and the old point-to-boundary join preview into one
report-rich workflow over a cached live 311 slice and the full packaged
community-district layer.

## Questions This Example Answers

- What share of cached live requests joins successfully to a community district?
- Which rows remain unmatched?
- How often does the raw `community_district` text agree with the spatial join?
- Which districts receive no matched requests?
- Which districts receive the most matched records?
- Which complaint types dominate the QA slice?

## Local Repo Usage

```bash
cd examples/spatial-join-qa
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

- `artifacts/`: ignored boundary inventory, join preview, unmatched rows, and
  raw-vs-spatial QA tables
- `cache/`: ignored cached live snapshot reused between runs
- `reports/`: tracked tearsheet and tracked report figures published on demand

Running the example writes:

- `cache/spatial-join-qa-snapshot.csv`
- `artifacts/spatial-join-qa-boundary-summary.csv`
- `artifacts/spatial-join-qa-join-preview.csv`
- `artifacts/spatial-join-qa-complaint-mix.csv`
- `artifacts/spatial-join-qa-unmatched-points.csv`
- `artifacts/spatial-join-qa-text-vs-spatial.csv`
- `artifacts/spatial-join-qa-joined-district-counts.csv`

When `--publish-report` is passed, it also writes:

- `reports/spatial-join-qa-tearsheet.md`
- `reports/figures/spatial-join-qa-match-status-map.png`
- `reports/figures/spatial-join-qa-coverage-breakdown.png`
- `reports/figures/spatial-join-qa-joined-district-counts.png`

## Notes

- defaults to a larger cached January 2025 citywide mixed-complaint slice
- keeps the full city district layer as the QA target, with borough outlines for
  orientation
- updates tracked report assets only when `--publish-report` is passed
