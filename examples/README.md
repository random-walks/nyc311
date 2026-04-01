# Examples

`examples/` now contains self-contained consumer projects instead of a shared
mix of scripts, notebooks, repo-local utilities, and one global output
directory.

## Contract

Every example lives in its own semantic-slug folder such as
`examples/quickstart-sdk/`.

The canonical starting point for new work is `examples/example-template/`.

Each example must:

- include its own `pyproject.toml`
- include its own `README.md`
- include its own `.gitignore`
- provide a single `main.py` entrypoint
- import only `nyc311.*` as an installed package
- keep caches under `cache/`
- keep scratch and intermediate outputs under ignored `artifacts/`
- use an optional tracked `reports/` folder for markdown and report figures that
  should stay in git
- avoid shared cross-example `utils/`, `data/`, or `output/` directories
- run in memory by default, with local cache reuse for heavier live-fetch flows

Examples are intentionally not part of the main test matrix or CI runtime path.
They are consumer references, not package fixtures.

## Inventory

- `examples/quickstart-sdk/`: zero-network SDK quickstart over packaged sample
  records
- `examples/fetch-filtered-snapshot/`: live fetch to a local example-owned CSV
  cache
- `examples/community-district-case-study/`: larger Brooklyn case study with a
  reusable local cache
- `examples/topic-eda/`: topic coverage, anomaly checks, and markdown report
  generation
- `examples/borough-choropleth/`: borough-level choropleth over packaged sample
  records
- `examples/point-to-boundary-join/`: raw point-in-polygon join preview with
  local artifacts
- `examples/community-district-choropleth/`: community-district dominant-topic
  choropleth
- `examples/spatial-topic-comparison/`: grouped complaint comparison after
  spatial enrichment
- `examples/boundary-qa/`: boundary geometry QA and join-coverage sanity check

## Bootstrap Template

Use `examples/example-template/` when creating a new example folder. It
captures the current conventions for:

- local editable uv wiring
- `cache/` vs `artifacts/` vs tracked `reports/`
- report figure path conventions
- question-driven example design

## Local Repo Usage

Each example is its own uv project. From an example folder:

```bash
uv sync
uv run python main.py
```

The local `pyproject.toml` points to the repo root as an editable path
dependency, so the example imports `nyc311` exactly the way an external
consumer would while still tracking local source edits.

## Public Consumer Shape

These examples are written so the same `main.py` files also work outside the
repo after installing `nyc311` from PyPI with the documented extras for that
example.

## Caching Policy

The examples follow one runtime pattern:

1. load packaged sample data directly when that is enough to teach the feature
2. for heavier live-fetch stories, reuse an example-local cached snapshot when
   present
3. only refetch large inputs when the user explicitly asks to refresh the cache

That keeps runs fast, reproducible, and self-contained.
