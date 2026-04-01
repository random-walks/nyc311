# Topic EDA

This example reuses a local snapshot, audits topic coverage, shows a small
custom-rule experiment, and writes a markdown report card artifact.

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

## Public Package Shape

```bash
pip install "nyc311[dataframes]"
python main.py --refresh
```

## Outputs

- writes or reuses `cache/topic-eda-snapshot.csv`
- writes `artifacts/topic-eda-report.md`

## Notes

- uses the `dataframes` extra for tabular inspection
- keeps both cache and artifacts inside this example folder
