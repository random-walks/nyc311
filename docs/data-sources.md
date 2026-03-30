# Data Sources

## Primary Inputs

- NYC 311 Service Requests dataset via Socrata
- supporting geographic boundary files for borough, tract, district, or neighborhood aggregation
- optional demographic overlays for contextual analysis

## Initial Data Principles

- prefer direct documented pulls from the public dataset
- cache filtered extracts locally for reproducibility
- keep data-loading logic transparent and easy to audit
- separate raw dataset access from downstream topic-model outputs

## Early Technical Notes

- the text fields are short and noisy
- some useful fields may vary in completeness across years
- spatial joins and geography standardization should be explicit
- large extracts should stay out of git

## Documentation Follow-Up

As implementation starts, this page should grow to include:

- exact dataset identifiers and URLs
- field notes for the first supported workflow
- geography assumptions
- caveats about text cleanliness and missingness
