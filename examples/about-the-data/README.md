# About the data

Kitchen-sink catalogue and figure pipeline for NYC 311: maximum Socrata surface
(cached CSVs), packaged boundary GeoJSON, and a markdown tearsheet with PNGs.

Layout mirrors the ecosystem pattern used in
[`subway-access` about-the-data](https://github.com/random-walks/subway-access/tree/main/examples/about-the-data):

| Script | Role |
| --- | --- |
| [`download.py`](./download.py) | Socrata bulk slices + boundary GeoJSON under `cache/` |
| [`analyze.py`](./analyze.py) | Catalogue + PNG figures + `reports/about-the-data-tearsheet.md` |
| [`main.py`](./main.py) | Runs download then analysis (same flags as both) |

## Run

```bash
uv sync
uv run python main.py
```

### Borough-by-borough (resumable)

Each borough writes **one** deterministic CSV under `cache/records/<borough_slug>/`. Completed files are **skipped** on the next run unless you pass `--refresh`. Interrupted runs only leave a `*.csv.part` file (never a complete `*.csv`); the next run removes the partial and retries that slice.

**All five** (default):

```bash
uv run python download.py -v
```

**One borough** (repeat for others as needed):

```bash
uv run python download.py --boroughs MANHATTAN -v
# or:
./scripts/download-borough.sh BROOKLYN -v
```

Underscores in comma-lists are accepted (`STATEN_ISLAND` → `STATEN ISLAND`).

**Analysis only** (reuse `cache/`, regenerate figures + tearsheet):

```bash
uv run python analyze.py
```

**Full refresh of tracked report + PNGs** (after cache is complete):

```bash
uv run python analyze.py --clear-figures --clear-report
```

**End-to-end** without re-downloading:

```bash
uv run python main.py --skip-download --clear-figures --clear-report
```

Fast iteration (one borough, narrow dates, fewer maps):

```bash
uv run python main.py \
  --boroughs BROOKLYN \
  --start-date 2025-01-01 --end-date 2025-01-31 \
  --skip-choropleth --skip-scatter --skip-hero \
  --page-size 5000 --max-records-per-borough 50000
```

Set `NYC_OPEN_DATA_APP_TOKEN` (or pass `--app-token`) for higher Socrata rate
limits on large pulls. If you see `TimeoutError` while reading a page, raise
`--request-timeout` (default 300 seconds per request; try `600` on slow links).

**Order of operations:** finish `download.py` (or `main.py` without `--skip-download`)
before `analyze.py`. Figures read from `cache/` only; wiping `cache/` and running
`analyze.py` alone will not pull new data.

## Full history vs small samples

The default run uses **no per-borough cap** (`--max-records-per-borough`
defaults to unlimited) and streams **one CSV per borough** via
`nyc311.io.cached_fetch` with `presets.large_socrata_config()` (50k rows per
page). That is the path to the **full public dataset** (tens of millions of rows
total, hours of runtime, large `cache/`).

If you only see **~20 rows** under `cache/records/...`, that is **not** a live
Socrata pull: it is almost certainly a **local test fixture** copied into
`cache/` for offline figure development. Delete `cache/` and run **without**
`--skip-download` to fetch real data, or use the “fast iteration” command above
with an explicit `--max-records-per-borough` when you want a bounded sample on
purpose.

**Different date ranges** produce **different filenames** (dates are baked into
the CSV name). To align boroughs, use the same `--start-date` / `--end-date`
everywhere, or remove older CSVs and re-fetch with `--refresh`.
