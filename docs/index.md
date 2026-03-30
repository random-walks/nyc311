# nyc311

`nyc311` is a Python-first toolkit for turning NYC 311 complaint records into
reusable complaint-intelligence outputs.

## v0.1 status

The repository now includes one real, fully tested foundation workflow:

1. load filtered NYC 311-style service-request records from a local CSV extract
2. derive a deterministic first-pass topic label from short complaint text
3. aggregate those topics by a supported geography field
4. export a reusable CSV summary table

This first release is intentionally narrow. It is designed to be easy to audit,
easy to test, and honest about what is still future work.

## Implemented now

- local CSV loading via `load_service_requests(...)`
- filtering by date range, borough, community district, and complaint type
- deterministic topic extraction for:
  - `Noise - Residential`
  - `Rodent`
- geography-aware aggregation by:
  - `community_district`
  - `borough`
- CSV export via `export_topic_table(...)`

## Planned later

These surfaces are still scaffolded and intentionally raise
`NotImplementedError`:

- Socrata / live API loading
- boundary loading and boundary-backed GeoJSON export
- anomaly detection
- resolution-gap analysis
- report-card generation
- production-ready CLI workflows

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
- [Gap explination](notes/gap-explination.md)
