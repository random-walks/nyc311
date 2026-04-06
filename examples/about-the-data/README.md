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

## Presets

| `--preset` | Sort | Row cap | Default timeout / page |
| --- | --- | --- | --- |
| `full` (default) | Oldest first (`ASC`) | None (full history) | 300s per request, 5k rows/page |
| `smoke` | **Most recent first** (`DESC`) | **10,000 rows per borough** | 120s per request, 5k rows/page |

Smoke mode is for **quick end-to-end checks** across all five boroughs without a multi-hour pull. Full mode is the long-running **chronological** extract.

During download, **per-page progress** lines print by default (`[BRONX] page 1: 5000 rows (running total 5000)`). Use `--no-progress` to silence them.

## Run

```bash
uv sync
uv run python main.py
```

**Smoke test (all boroughs, ~10k rows each, recent data first):**

```bash
uv run python download.py --preset smoke -v
```

**Full history (long run; resumable):**

```bash
uv run python download.py --preset full -v
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

Fast iteration (one borough, narrow dates, bounded rows):

```bash
uv run python main.py \
  --boroughs BROOKLYN \
  --start-date 2025-01-01 --end-date 2025-01-31 \
  --skip-choropleth --skip-scatter --skip-hero \
  --page-size 5000 --max-records-per-borough 50000
```

Set `NYC_OPEN_DATA_APP_TOKEN` (or pass `--app-token`) for higher Socrata rate
limits on large pulls. If you see `TimeoutError` while reading a page, raise
`--request-timeout` (defaults: 300s for `full`, 120s for `smoke`; try `600` on slow links).

**Order of operations:** finish `download.py` (or `main.py` without `--skip-download`)
before `analyze.py`. Figures read from `cache/` only; wiping `cache/` and running
`analyze.py` alone will not pull new data.

## Full history vs small samples

The **`full`** preset uses **no per-borough cap** unless you pass `--max-records-per-borough`
and streams **one CSV per borough** via `nyc311.io.cached_fetch` with
`presets.large_socrata_config()` (**5,000 rows per HTTP page** by default). That is the path to the **full public dataset** (tens of millions of rows
total, hours of runtime, large `cache/`).

If you only see **~20 rows** under `cache/records/...`, that is **not** a live
Socrata pull: it is almost certainly a **local test fixture** copied into
`cache/` for offline figure development. Delete `cache/` and run **without**
`--skip-download` to fetch real data, or use `--preset smoke` / `--max-records-per-borough` when you want a bounded sample on
purpose.

**Different date ranges** produce **different filenames** (dates are baked into
the CSV name). **DESC** (smoke) slices also get a `_desc` suffix so they never collide with chronological `full` extracts. To align boroughs, use the same `--start-date` / `--end-date`
everywhere, or remove older CSVs and re-fetch with `--refresh`.
