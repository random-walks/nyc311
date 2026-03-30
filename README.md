# nyc311

[![Actions Status][actions-badge]][actions-link]
[![Documentation Status][rtd-badge]][rtd-link]
[![PyPI version][pypi-version]][pypi-link]
[![PyPI platforms][pypi-platforms]][pypi-link]

NLP pipeline for extracting topics, anomalies, and resolution gaps from NYC 311 complaint data.

## Status

This repository has been scaffolded as a public-ready package repo before implementation begins.

- Packaging, docs, CI, and release plumbing are present.
- The project is still in the planning and seeding phase.
- There is not yet a stable public API.

## Why This Exists

NYC 311 data is one of the richest public records of neighborhood quality-of-life complaints in the country, but the most interesting signal is locked inside messy short-text fields and temporal patterns that are easy to ignore in the raw dataset.

`nyc311` is intended to turn that raw complaint stream into reusable analytical outputs such as:

- fine-grained complaint topics
- trend and anomaly signals
- geography-aware resolution gaps
- notebook and report inputs for policy analysis

## Planned Outputs

- data loaders for filtered pulls from the Socrata dataset
- topic and trend analysis outputs
- GeoJSON and CSV exports
- neighborhood report-card style notebooks

## Initial Scope

- pull date- and geography-filtered 311 records
- run first-pass topic clustering on key complaint categories
- produce trend summaries and map-friendly outputs
- document methodology clearly enough for reuse and review

## Documentation

- `docs/project-brief.md`: problem framing and package positioning
- `docs/data-sources.md`: dataset assumptions and provenance notes
- `docs/mvp-roadmap.md`: v0.1 scope and stretch path
- `docs/notes/original-spec.md`: preserved project seed notes

## Development

```bash
uv sync --group docs
uv run pytest
uv run mkdocs serve
```

## License

MIT.

<!-- prettier-ignore-start -->
[actions-badge]:            https://github.com/random-walks/nyc311/actions/workflows/ci.yml/badge.svg
[actions-link]:             https://github.com/random-walks/nyc311/actions
[github-discussions-badge]: https://img.shields.io/static/v1?label=Discussions&message=Ask&color=blue&logo=github
[github-discussions-link]:  https://github.com/random-walks/nyc311/discussions
[pypi-link]:                https://pypi.org/project/nyc311/
[pypi-platforms]:           https://img.shields.io/pypi/pyversions/nyc311
[pypi-version]:             https://img.shields.io/pypi/v/nyc311
[rtd-badge]:                https://readthedocs.org/projects/nyc311/badge/?version=latest
[rtd-link]:                 https://nyc311.readthedocs.io/en/latest/?badge=latest
<!-- prettier-ignore-end -->
