# Fetch Filtered Snapshot

This example shows the recommended snapshot-first consumer pattern:

1. build a typed filter
2. fetch a narrow live Socrata slice
3. save it under this example's `cache/`
4. reuse that cache on later runs unless `--refresh` is passed
5. write artifact metadata every run so the snapshot is easy to audit later

## Questions This Example Answers

- What exact filters produced the current snapshot?
- How many rows came from cache vs live fetch?
- What complaint mix came back in the saved slice?
- What should the user run next against the cached file?

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

To publish a tracked tearsheet for the current pinned snapshot:

```bash
uv run python main.py --publish-report
```

## Public Package Shape

```bash
pip install nyc311
python main.py
```

Use `--refresh` only when you want to rebuild the local cache and
`--publish-report` only when you intentionally want to update tracked report
content.

## Output Layout

- `cache/`: ignored local CSV snapshot
- `artifacts/`: ignored fetch metadata and next-step summary
- `reports/`: optional tracked tearsheet for a pinned snapshot

Running the example writes or reuses:

- `cache/rodent-snapshot.csv`
- `artifacts/fetch-metadata.json`
- `artifacts/fetch-summary.md`

When `--publish-report` is passed, it also writes:

- `reports/fetch-filtered-snapshot-tearsheet.md`

## Notes

- uses an example-local cache instead of a shared repo dump
- respects `NYC_OPEN_DATA_APP_TOKEN` when present
- stays base-only and does not add plotting dependencies
