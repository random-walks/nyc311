# Examples

`nyc311` examples now live as self-contained consumer projects under
`examples/`. There are no repo-level example notebooks, no shared
`examples/utils/`, and no shared `examples/output/`.

## Contract

Every example follows the same structure:

- one semantic-slug folder under `examples/`
- one local `pyproject.toml`
- one local `README.md`
- one local `.gitignore`
- one `main.py` entrypoint
- local `cache/` and `artifacts/` directories created on demand

Each example imports only `nyc311.*`, so it exercises the package the same way
an external user would. In the repo, that happens through a local editable path
dependency. Outside the repo, the same scripts work after installing `nyc311`
from PyPI with the listed extras.

## Overview

| Example | Focus | Default data mode | Extra | Cache | Artifacts | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `examples/quickstart-sdk/` | first in-memory SDK walkthrough | packaged sample records | base | no | CSV summary | implemented |
| `examples/fetch-filtered-snapshot/` | filtered Socrata fetch and local snapshot reuse | live fetch with local cache reuse | base | yes | CSV snapshot | implemented |
| `examples/community-district-case-study/` | Brooklyn case study with topic and resolution summaries | cache-backed live slice | base | yes | CSV summary | implemented |
| `examples/topic-eda/` | coverage audit, anomalies, and markdown report card | cache-backed live slice | `dataframes` | yes | markdown report | implemented |
| `examples/borough-choropleth/` | borough-level dominant-topic map | packaged sample records | `spatial,plotting` | no | PNG map | implemented |
| `examples/point-to-boundary-join/` | raw point-to-boundary join preview | packaged sample records | `spatial,plotting` | no | CSV join + PNG preview | implemented |
| `examples/community-district-choropleth/` | district-level dominant-topic map | packaged sample records | `spatial,plotting` | no | PNG map | implemented |
| `examples/spatial-topic-comparison/` | grouped complaint comparison after spatial enrichment | packaged sample records | `spatial,plotting` | no | CSV comparison + PNG preview | implemented |
| `examples/boundary-qa/` | boundary geometry QA and join coverage | packaged sample records | `spatial,plotting` | no | CSV summary + PNG preview | implemented |

## Data And Cache Strategy

The examples follow one default runtime story:

1. run in memory whenever packaged sample data is enough
2. when a story needs more data, write a cache file inside that example folder
3. reuse that local cache on later runs instead of refetching by default
4. keep all rendered outputs inside the same example folder

That pattern keeps examples reproducible without reintroducing one shared global
dump directory.

## Local Repo Usage

From any example folder:

```bash
uv sync
uv run python main.py
```

Examples are intentionally not executed in the main CI or test matrix. The
package itself remains the tested release surface.

## Snapshot-First Pattern

For larger workflows, fetch once and then iterate against a local snapshot:

```bash
nyc311 fetch \
  --output local-noise-snapshot.csv \
  --complaint-type "Noise - Residential" \
  --geography borough \
  --geography-value BROOKLYN \
  --start-date 2025-01-01 \
  --end-date 2025-01-31 \
  --page-size 500 \
  --max-pages 2
```

Then point analysis at the saved file:

```bash
nyc311 topics \
  --source local-noise-snapshot.csv \
  --complaint-type "Noise - Residential" \
  --geography community_district \
  --output topics.csv
```

That same pattern is mirrored inside the cache-backed example projects.
