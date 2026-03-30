# Data Sources

## Implemented In v0.1

The current release supports **local CSV extracts** of NYC 311-style service
request records.

The implemented happy path expects these columns:

- `unique_key`
- `created_date`
- `complaint_type`
- `descriptor`
- `borough`
- `community_district` (or `community_board`)

An optional `resolution_description` column is also accepted and preserved on
loaded records, but it is not yet used for any shipped analysis.

## Current Loader Scope

`load_service_requests(...)` supports:

- loading from a local CSV path
- filtering by created-date range
- filtering by `borough`
- filtering by `community_district`
- filtering by complaint type

This is intentionally narrow so the first release stays deterministic,
inspectable, and easy to test.

## Planned Later

The following inputs are still planned and are **not implemented** in v0.1:

- live Socrata/API pulls
- caching/downloading workflows for large public extracts
- polygon boundary loading
- spatial joins for tract- or district-level geography derivation
- demographic overlay inputs

## Data Principles

- keep raw data access explicit and easy to audit
- prefer stable local extracts for the current implemented workflow
- avoid hidden geocoding or fuzzy geography standardization
- keep large real-world extracts out of git

## Notes On Text Fields

The descriptor text is short, noisy, and inconsistent. v0.1 therefore uses a
documented deterministic ruleset for first-pass topic labeling instead of
claiming broader NLP coverage than is actually implemented today.
