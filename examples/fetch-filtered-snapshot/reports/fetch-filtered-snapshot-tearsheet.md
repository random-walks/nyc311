# Fetch Filtered Snapshot Tearsheet

This tearsheet documents the current pinned snapshot for the fetch-first
consumer workflow. Regenerate it only when you intentionally want to
update the tracked snapshot description.

## Executive Summary

- Snapshot source: `live fetch`.
- Saved rows: `500` at `/Users/blaise/Desktop/blaise-oss/nyc311/examples/fetch-filtered-snapshot/cache/rodent-snapshot.csv`.
- Primary complaint mix leader: `Rodent` with `500` rows (100.0%).
- Applied filters: `borough = BROOKLYN`, `2025-01-01` to `2025-01-31`, complaint types `Rodent`.

## Complaint Mix

| Complaint type | Count | Share |
| --- | --- | --- |
| Rodent | 500 | 100.0% |

## Next Step

```bash
nyc311 topics --source /Users/blaise/Desktop/blaise-oss/nyc311/examples/fetch-filtered-snapshot/cache/rodent-snapshot.csv --complaint-type "Rodent" --geography community_district --output artifacts/topic-summary.csv
```
