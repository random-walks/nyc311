# Data Sources

> Archived planning note: this page reflects the original `v0.1` data-source
> framing. For the active release framing, use the main docs for the current
> `0.2` alpha line.

## Implemented now

The current release supports two real service-request input paths:

- **local CSV extracts**
- **live Socrata loading** via the NYC 311 dataset

The CSV loader expects these columns:

- `unique_key`
- `created_date`
- `complaint_type`
- `descriptor`
- `borough`
- `community_district` (or `community_board`)

An optional `resolution_description` column is also accepted and preserved on
loaded records, but it is not yet used for shipped analysis.

## Current loader scope

`load_service_requests(...)` supports:

- loading from a local CSV path
- loading from a `SocrataConfig(...)` source
- filtering by created-date range
- filtering by `borough`
- filtering by `community_district`
- filtering by complaint type

The live Socrata path intentionally keeps the projection and filter set narrow
so the implementation remains transparent and easy to validate.

## Implemented boundary support

`load_boundaries(...)` now supports loading a GeoJSON FeatureCollection for
supported geographies.

Current boundary support is still intentionally narrow:

- field-backed joins only
- boundary features must include:
  - `geography`
  - `geography_value`
- currently useful for boundary-backed GeoJSON export of aggregated results

## Planned later

The following inputs are still planned:

- caching/downloading workflows for large public extracts
- broader spatial joins for tract- or district-level geography derivation
- demographic overlay inputs
- richer live-ingestion ergonomics beyond the current focused Socrata path

## Data principles

- keep raw data access explicit and easy to audit
- prefer stable local extracts for reproducible tests and examples
- avoid hidden geocoding or fuzzy geography standardization
- keep large real-world extracts out of git

## Notes on text fields

The descriptor text is short, noisy, and inconsistent. The current release
therefore uses a documented deterministic ruleset for first-pass topic labeling
instead of claiming broader NLP coverage than is actually implemented today.
