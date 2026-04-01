# Spatial Topic Comparison

This example spatially enriches packaged sample records and compares complaint
mix by community district after the join.

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

## Outputs

- writes `artifacts/spatial-topic-comparison.csv`
- writes `artifacts/spatial-topic-comparison-preview.png`

## Notes

- uses packaged sample records and packaged sample-aligned boundaries
- does not create or depend on a cache
