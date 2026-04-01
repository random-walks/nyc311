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

## Start Here

If you just want the smoothest first run across the report-rich examples, install
the full optional stack once:

```bash
pip install "nyc311[all]"
```

That covers every example in this folder, including the map-heavy spatial ones.
The individual example READMEs still document their minimal extras for advanced
users who want a leaner install.

## Quick Index

The folders stay flat on disk, but the examples group naturally into a few
learning tracks. Use the table below as the fast GitHub skim.

| Example | Skill level | Track | Best for | Default data mode |
| --- | --- | --- | --- | --- |
| `examples/quickstart-sdk/` | Easy | first run | smallest end-to-end SDK walkthrough | packaged sample records |
| `examples/borough-choropleth/` | Easy | visual intro | first polished geospatial tearsheet | packaged sample records |
| `examples/fetch-filtered-snapshot/` | Easy | live data | first cache-backed fetch pattern | live fetch with local cache reuse |
| `examples/community-district-choropleth/` | Intermediate | geospatial storytelling | full-city district choropleth with no-data context | packaged sample records |
| `examples/point-to-boundary-join/` | Intermediate | spatial QA | basic point-in-polygon join diagnostics | packaged sample records |
| `examples/boundary-qa/` | Intermediate | spatial QA | boundary coverage and raw-vs-spatial sanity checks | packaged sample records |
| `examples/spatial-topic-comparison/` | Intermediate | spatial comparison | how the story changes after a full spatial join | packaged sample records |
| `examples/community-district-case-study/` | Advanced | live analysis | larger Brooklyn slice with publish-gated reporting | cache-backed live slice |
| `examples/topic-eda/` | Advanced | live analysis | coverage audits, anomaly flags, and scratch exports | cache-backed live slice |

## Suggested Paths

### Fast visual path

1. `examples/quickstart-sdk/`
2. `examples/borough-choropleth/`
3. `examples/community-district-choropleth/`
4. `examples/spatial-topic-comparison/`

### Spatial QA path

1. `examples/point-to-boundary-join/`
2. `examples/boundary-qa/`

### Live snapshot path

1. `examples/fetch-filtered-snapshot/`
2. `examples/community-district-case-study/`
3. `examples/topic-eda/`

## Non-Example Helpers

- `examples/example-template/`: canonical scaffold for new example folders, not a
  finished tutorial
- `examples/primitive-example-upgrade-handoff.md`: maintenance handoff note, not
  a user-facing example

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
4. only refresh tracked report assets for live examples when the user explicitly
   asks to publish them

That keeps runs fast, reproducible, and self-contained.
