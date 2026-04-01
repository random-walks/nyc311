# Quickstart SDK

This example shows the smallest in-memory `nyc311` workflow over packaged
sample records:

1. load records
2. extract deterministic topics
3. aggregate by geography
4. export a CSV artifact

## Local Repo Usage

```bash
cd examples/quickstart-sdk
uv sync
uv run python main.py
```

## Public Package Shape

The same `main.py` works in any fresh environment after:

```bash
pip install nyc311
python main.py
```

## Output

- writes `artifacts/quickstart-topics.csv`

## Notes

- uses packaged sample data only
- does not create or depend on a cache
