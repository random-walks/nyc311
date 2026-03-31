# Architecture

`nyc311` currently implements a narrow but end-to-end pipeline for deterministic
topic summarization over NYC 311-style complaint data.

## Pipeline

```mermaid
flowchart LR
    sourceData[SourceData] --> loaders[load_service_requests]
    loaders --> records[ServiceRequestRecordList]
    records --> extract[extract_topics]
    records --> coverage[analyze_topic_coverage]
    records --> gaps[analyze_resolution_gaps]
    extract --> assignments[TopicAssignmentList]
    assignments --> aggregate[aggregate_by_geography]
    aggregate --> summaries[GeographyTopicSummaryList]
    summaries --> anomalies[detect_anomalies]
    summaries --> csvExport[export_topic_table]
    summaries --> geojsonPrep[load_boundaries]
    geojsonPrep --> geojsonExport[export_geojson]
    summaries --> report[export_report_card]
    gaps --> report
    anomalies --> report
```

## Module Responsibilities

| Module | Responsibility |
| --- | --- |
| `nyc311.models` | Typed dataclasses and package-level constants |
| `nyc311.loaders` | CSV and Socrata ingestion, filter application, boundary-loading entry point |
| `nyc311.processors` | Deterministic topic extraction and geography aggregation |
| `nyc311.exporters` | CSV and GeoJSON output generation |
| `nyc311.boundaries` | GeoJSON parsing into boundary models |
| `nyc311.pipeline` | High-level SDK helper that mirrors the CLI happy path |
| `nyc311.cli` | Argparse-powered fetch and analysis entry points |

## Design Principles

- Keep the implemented surface honest and narrow.
- Prefer typed inputs and outputs over implicit dictionaries.
- Make the SDK composable for workflows and notebooks.
- Keep the CLI thin by delegating real work to importable functions.
- Keep optional dependency boundaries explicit for dataframe and notebook helpers.

## Implemented Scope

- service-request loading from CSV and Socrata
- service-request snapshot export for reproducible local staging
- topic extraction for four supported complaint types
- topic-coverage analysis for descriptor-rule match rates
- aggregation by borough or community district
- resolution-gap summaries
- anomaly detection over aggregated topic counts
- CSV export
- boundary-backed GeoJSON export
- markdown report-card export
- optional pandas dataframe conversion helpers
- a one-call SDK pipeline helper
- thin CLI fetch and export paths

The repository includes `scripts/audit_implementation.py` to summarize the
current public surface and keep docs aligned with shipped behavior.

## Boundaries

GeoJSON export is intentionally narrow today. Boundary files must provide
feature properties with both:

- `geography`
- `geography_value`

This keeps export behavior deterministic without adding a larger spatial join
layer yet.

## Maintainer Notes

- `docs/og-context/` contains archived planning and original product framing.
- The primary source of truth for public package behavior is the tested code in
  `src/nyc311/` and the user-facing docs in this folder.
