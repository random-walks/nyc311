# Quickstart SDK

This example shows the smallest in-memory `nyc311` workflow over packaged sample
records:

1. load records
2. extract deterministic topics
3. aggregate by geography
4. export a scratch CSV artifact
5. write a tracked beginner-friendly markdown tearsheet

## Questions This Example Answers

- How many packaged sample records are loaded?
- Which community districts appear in the sample?
- Which topic dominates each district?
- Which district has the highest complaint count in the quickstart slice?

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

## Output Layout

- `artifacts/`: ignored CSV export for raw topic summaries
- `reports/`: tracked markdown tearsheet

Running the example writes:

- `artifacts/quickstart-topics.csv`
- `reports/quickstart-sdk-tearsheet.md`

## Notes

- uses packaged sample data only
- does not create or depend on a cache
- stays base-only and does not require plotting dependencies
