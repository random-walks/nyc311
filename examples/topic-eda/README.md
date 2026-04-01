# Topic EDA

This example reuses a local Brooklyn snapshot, audits built-in topic coverage,
surfaces unmatched descriptors and anomaly candidates, keeps the package-level
report card as a scratch artifact, and publishes a custom tearsheet on demand.

## Questions This Example Answers

- Which complaint types have the strongest and weakest built-in topic coverage?
- Which unmatched descriptors drive the biggest coverage gaps?
- Which geography/topic summaries look anomalous?
- Which complaint groups have the highest unresolved share?

## Local Repo Usage

```bash
cd examples/topic-eda
uv sync
uv run python main.py
```

To rebuild the local cache:

```bash
uv run python main.py --refresh
```

To refresh the tracked report assets:

```bash
uv run python main.py --publish-report
```

## Public Package Shape

```bash
pip install "nyc311[dataframes,plotting]"
python main.py
```

Use `--refresh` only when you want to rebuild the snapshot and
`--publish-report` only when you intentionally want to update the tracked
tearsheet and figures.

## Output Layout

- `cache/`: ignored local snapshot reused between runs
- `artifacts/`: ignored baseline report card plus CSV summaries
- `reports/`: tracked tearsheet and tracked report figures

Running the example writes or reuses:

- `cache/topic-eda-snapshot.csv`
- `artifacts/topic-eda-report.md`
- `artifacts/topic-coverage-summary.csv`
- `artifacts/topic-unmatched-descriptors.csv`
- `artifacts/topic-anomalies.csv`
- `artifacts/topic-resolution-gaps.csv`

When `--publish-report` is passed, it also writes:

- `reports/topic-eda-tearsheet.md`
- `reports/figures/topic-coverage-by-complaint-type.png`
- `reports/figures/top-unmatched-descriptors.png`
- `reports/figures/topic-anomaly-zscores.png`
- `reports/figures/topic-resolution-gap.png`

## Notes

- uses `dataframes` for local tabular inspection and `plotting` for report figures
- keeps both cache and artifacts inside this example folder
- treats the generic package-level report card as scratch, not the final tracked report
