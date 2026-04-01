# Spatial Join QA Tearsheet

This canonical example audits the packaged sample points against the packaged
sample-aligned `community_district` subset, then turns the results into one
report that covers join success, unmatched rows, boundary coverage, and raw-vs-spatial agreement.

## Executive Summary

- The packaged sample contains `18` point-capable service requests and the sampled spatial join succeeds for `12` of them (`66.7%`).
- `6` rows remain outside every polygon in the sampled boundary subset.
- Raw district text agrees with the spatial join for `100.0%` of matched rows (`12` of `12`).
- The following sampled polygons receive no matched sample points: `BRONX 05, QUEENS 02`.
- The busiest sampled polygon is `BROOKLYN 01` with `5` matched records.

## Match Status Map

![Matched versus unmatched sample points](./figures/spatial-join-qa-match-status-map.png)

## Coverage Breakdown

![Matched versus unmatched breakdown](./figures/spatial-join-qa-coverage-breakdown.png)

## Joined District Counts

![Matched records by sampled district](./figures/spatial-join-qa-joined-district-counts.png)

## Boundary Geometry Inventory

| Boundary | Geometry type | Matched point count |
| --- | --- | --- |
| MANHATTAN 10 | MultiPolygon | 4 |
| BRONX 05 | MultiPolygon | 0 |
| BROOKLYN 01 | MultiPolygon | 5 |
| BROOKLYN 03 | MultiPolygon | 3 |
| QUEENS 02 | MultiPolygon | 0 |

## Joined District Metrics

| Sampled district | Matched count |
| --- | --- |
| BROOKLYN 01 | 5 |
| MANHATTAN 10 | 4 |
| BROOKLYN 03 | 3 |

## Agreement Summary

Scratch QA tables are available under `artifacts/`:
`spatial-join-qa-unmatched-points.csv`, `spatial-join-qa-text-vs-spatial.csv`, and `spatial-join-qa-joined-district-counts.csv`.

| Metric | Value |
| --- | --- |
| Matched rows | 12 |
| Unmatched rows | 6 |
| Agreement rows | 12 |
| Agreement rate among matched rows | 100.0% |
