# Fetch Filtered Snapshot

This example shows the recommended snapshot-first consumer pattern:

1. build a typed filter
2. fetch a narrow live Socrata slice
3. save it under this example's `cache/`
4. reuse that cache on later runs unless `--refresh` is passed

## Local Repo Usage

```bash
cd examples/fetch-filtered-snapshot
uv sync
uv run python main.py
```

To force a new network fetch:

```bash
uv run python main.py --refresh
```

## Public Package Shape

```bash
pip install nyc311
python main.py --refresh
```

## Output

- writes or reuses `cache/rodent-snapshot.csv`

## Notes

- uses an example-local cache instead of a shared repo dump
- respects `NYC_OPEN_DATA_APP_TOKEN` when present
