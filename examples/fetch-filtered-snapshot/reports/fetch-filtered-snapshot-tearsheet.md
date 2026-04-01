# Fetch Filtered Snapshot Tearsheet

This tearsheet documents the current pinned snapshot for the fetch-first
consumer workflow. Regenerate it only when you intentionally want to
update the tracked snapshot description.

## Executive Summary

- Snapshot source: `live fetch`.
- Saved rows: `6000` at `/Users/blaise/Desktop/blaise-oss/nyc311/examples/fetch-filtered-snapshot/cache/brooklyn-noise-snapshot.csv`.
- Primary complaint mix leader: `Noise - Residential` with `6000` rows (100.0%).
- Applied filters: `borough = BROOKLYN`, `2025-01-01` to `2025-03-31`, complaint types `Noise - Residential`.

## Complaint Mix

| Complaint type | Count | Share |
| --- | --- | --- |
| Noise - Residential | 6000 | 100.0% |

## Next Step

```bash
nyc311 topics --source /Users/blaise/Desktop/blaise-oss/nyc311/examples/fetch-filtered-snapshot/cache/brooklyn-noise-snapshot.csv --complaint-type "Noise - Residential" --geography community_district --output artifacts/topic-summary.csv
```
