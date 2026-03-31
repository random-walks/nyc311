# CLI Reference

The current command-line surface is intentionally small but now covers two
practical workflows:

- `topics` for summary exports from a local CSV snapshot
- `fetch` for pulling a filtered Socrata slice into a local CSV snapshot

## Entry Point

After installation, the package exposes:

```bash
nyc311
```

## Command

### `nyc311 topics`

Load service-request records from a local CSV file, derive deterministic topic
labels for one supported complaint type, aggregate them by geography, and
export either CSV or GeoJSON.

## Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `--source` | yes | Input CSV path |
| `--output` | yes | Output file path |
| `--complaint-type` | yes | Supported complaint type to analyze |
| `--geography` | no | Aggregation geography: `borough` or `community_district` |
| `--start-date` | no | Inclusive start date in `YYYY-MM-DD` format |
| `--end-date` | no | Inclusive end date in `YYYY-MM-DD` format |
| `--geography-value` | no | Optional geography filter value |
| `--top-n` | no | Maximum number of topics to keep, default `20` |
| `--format` | no | Output format: `csv` or `geojson`, default `csv` |
| `--boundaries` | conditionally required | Boundary GeoJSON path for `geojson` output |

## Examples

### Export CSV

```bash
nyc311 topics \
  --source brooklyn-noise-snapshot.csv \
  --complaint-type "Noise - Residential" \
  --geography community_district \
  --output topics.csv
```

### Export GeoJSON

```bash
nyc311 topics \
  --source brooklyn-noise-snapshot.csv \
  --complaint-type "Noise - Residential" \
  --geography community_district \
  --format geojson \
  --boundaries community_district_boundaries.geojson \
  --output topics.geojson
```

### Filter By Date And Geography

```bash
nyc311 topics \
  --source brooklyn-noise-snapshot.csv \
  --complaint-type "Noise - Residential" \
  --geography community_district \
  --start-date 2025-01-01 \
  --end-date 2025-03-31 \
  --geography-value "BROOKLYN 01" \
  --output brooklyn-noise-topics.csv
```

## Current Scope

The `topics` command currently reads local CSV input only. For live data,
start with `nyc311 fetch`, then analyze the resulting snapshot locally.

### `nyc311 fetch`

Fetch a filtered slice of the NYC 311 Socrata dataset and write a reproducible
local CSV snapshot.

This is the preferred workflow for larger or repeated analysis because it keeps
network access separate from downstream EDA and export steps.

## `fetch` Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `--output` | yes | Output CSV path |
| `--complaint-type` | no, repeatable | Optional complaint type filter |
| `--start-date` | no | Inclusive start date in `YYYY-MM-DD` format |
| `--end-date` | no | Inclusive end date in `YYYY-MM-DD` format |
| `--geography` | no | Filter geography: `borough` or `community_district` |
| `--geography-value` | no | Optional geography filter value |
| `--dataset-identifier` | no | Socrata dataset identifier |
| `--base-url` | no | Socrata API base URL |
| `--app-token` | no | Optional Socrata app token |
| `--page-size` | no | Rows per Socrata page |
| `--max-pages` | no | Optional maximum number of pages to fetch |
| `--request-timeout-seconds` | no | Per-request timeout |
| `--where` | no, repeatable | Extra SoQL where clause |

## `fetch` Example

```bash
nyc311 fetch \
  --output rodent-snapshot.csv \
  --complaint-type "Rodent" \
  --geography borough \
  --geography-value BROOKLYN \
  --start-date 2025-01-01 \
  --end-date 2025-01-31 \
  --page-size 500 \
  --max-pages 1
```

## Exit Behavior

- Returns exit code `0` on success.
- Usage and argument-validation errors are handled by `argparse`, which exits
  with code `2`.

## Related Docs

- Use [Getting Started](getting-started.md) for the fastest happy-path run.
- Use [SDK Guide](sdk.md) when you need workflow-style Python composition.
- Use [Examples](examples.md) for copy-paste scripts and notebooks.
