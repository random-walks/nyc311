# Python API

The public API now mixes a small implemented v0.1 slice with planned placeholder
surfaces.

## Implemented in v0.1

- `nyc311.loaders.load_service_requests`
- `nyc311.loaders.load_boundaries`
- `nyc311.processors.extract_topics`
- `nyc311.processors.aggregate_by_geography`
- `nyc311.exporters.export_topic_table`
- `nyc311.exporters.export_geojson`
- `nyc311.cli.main` via the `nyc311 topics ...` command
- supporting models in `nyc311.models`

## Still planned

These remain importable but intentionally raise `NotImplementedError`:

- `nyc311.loaders.load_resolution_data`
- `nyc311.processors.detect_anomalies`
- `nyc311.processors.analyze_resolution_gaps`
- `nyc311.exporters.export_anomalies`
- `nyc311.exporters.export_report_card`

## Models

::: nyc311.models

## Loaders

::: nyc311.loaders

## Processors

::: nyc311.processors

## Exporters

::: nyc311.exporters

## CLI

::: nyc311.cli
