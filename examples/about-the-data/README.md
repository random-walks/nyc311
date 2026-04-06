# About the data

Kitchen-sink catalogue and figure pipeline for NYC 311: maximum Socrata surface
(cached CSVs), packaged boundary GeoJSON, and a markdown tearsheet with PNGs.

## Run

```bash
uv sync
uv run python main.py
```

Fast iteration (one borough, narrow dates, fewer maps):

```bash
uv run python main.py \
  --boroughs BROOKLYN \
  --start-date 2025-01-01 --end-date 2025-01-31 \
  --skip-choropleth --skip-scatter --skip-hero \
  --page-size 5000 --max-records-per-borough 50000
```

Regenerate figures without re-downloading:

```bash
uv run python main.py --skip-download
```

Set `NYC_OPEN_DATA_APP_TOKEN` (or pass `--app-token`) for higher Socrata rate
limits on large pulls.

## Full history vs small samples

The default `main.py` run uses **no per-borough cap** (`--max-records-per-borough`
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
