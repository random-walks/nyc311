# Boundary QA

This example sanity-checks packaged sample-aligned boundaries, measures join
coverage for the packaged sample records, and writes local QA artifacts.

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

## Outputs

- writes `artifacts/boundary-summary.csv`
- writes `artifacts/boundary-preview.png`

## Notes

- uses packaged sample records and packaged sample-aligned boundaries
- does not create or depend on a cache
