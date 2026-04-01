# Community District Case Study

This example loads a larger Brooklyn slice, reuses an example-local cache, and
then builds a small community-district case study around topic summaries and
resolution gaps.

## Local Repo Usage

```bash
cd examples/community-district-case-study
uv sync
uv run python main.py
```

To refetch the cache:

```bash
uv run python main.py --refresh
```

## Public Package Shape

```bash
pip install nyc311
python main.py --refresh
```

## Outputs

- writes or reuses `cache/brooklyn-case-study.csv`
- writes `artifacts/brooklyn-noise-community-districts.csv`

## Notes

- keeps its live slice local to this folder
- uses in-memory analysis after the cache is loaded
