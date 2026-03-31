# nyc311 Archived Context

`nyc311` is a Python-first toolkit for turning NYC 311 complaint records into
reusable complaint-intelligence outputs.

This section preserves the original planning documents from the earlier `v0.1`
phase of the project.

Those pages intentionally use older scope language and do not describe the
current `0.2.0a1` alpha target. For current behavior, use the main docs in the
root `docs/` tree.

## Archived `v0.1` status

The repository now includes several real, fully tested workflows:

1. load filtered NYC 311-style service-request records from a local CSV extract
   or the live Socrata API
2. derive deterministic first-pass topic labels from short complaint text
3. aggregate those topics by a supported geography field
4. export either a reusable CSV summary table or a boundary-backed GeoJSON layer

This first release is intentionally narrow. It is designed to be easy to audit,
easy to test, and honest about what is still future work.

## Implemented now

- local CSV loading via `load_service_requests(...)`
- live Socrata loading via `load_service_requests(SocrataConfig(...))`
- filtering by date range, borough, community district, and complaint type
- deterministic topic extraction for:
  - `Noise - Residential`
  - `Rodent`
  - `Illegal Parking`
  - `Blocked Driveway`
- geography-aware aggregation by:
  - `community_district`
  - `borough`
- CSV export via `export_topic_table(...)`
- boundary-backed GeoJSON export via `load_boundaries(...)` +
  `export_geojson(...)`
- a thin CLI command:
  - `nyc311 topics ...`

## Planned later

These surfaces are still scaffolded and intentionally raise
`NotImplementedError`:

- anomaly detection
- resolution-gap analysis
- report-card generation
- richer multi-command CLI workflows

## Project focus

- keep the first release reproducible and explainable
- favor transparent first-pass methods over overclaiming advanced NLP
- connect text analysis with geography through clearly supported fields
- make outputs useful for civic analysis, journalism, and research

## Read next

- [Project brief](project-brief.md)
- [Data sources](data-sources.md)
- [MVP roadmap](mvp-roadmap.md)
- [Agent kickoff TODO](agent-kickoff-todo.md)
- [Agent handoff prompt](agent-handoff-prompt.md)
- [Original seed spec](notes/original-spec.md)
- [Gap explanation](notes/gap-explination.md)
