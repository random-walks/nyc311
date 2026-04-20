# Changelog

## Unreleased

### Added

### Changed

### Fixed

### Deprecated

### Contracts

### Security

## 1.0.0 - 2026-04-19

First major release. The headline is integration with
[factor-factory](https://github.com/random-walks/factor-factory) — every
`PanelDataset` can now feed factor-factory's 17 causal-inference engine families
without leaving the nyc311 API.

### Changed

- **Drop Python 3.10 and 3.11 support.** Minimum is now 3.12, to match upstream
  factor-factory. Existing `nyc311` 0.3.x consumers on Python 3.10/3.11 should
  either stay on 0.3 or upgrade Python first. See
  [migration-v0-to-v1.md](migration-v0-to-v1.md).
- Bump `nyc-geo-toolkit` minimum to `>=0.3.0,<0.4` (from `>=0.1.7,<0.2.0`), to
  pick up the v0.3.0 modernization pass (Claude Code infra parity,
  factor-factory/jellycell showcase example, pin bumps). Existing nyc311
  consumers of `nyc311.geographies` and the haversine helpers see no API changes
  — the upstream bump is additive.
- CI: bump `actions/checkout` to `v6`, `setup-uv` to `v8.1.0` (exact — no moving
  tag), `upload-artifact` to `v7`, keep `download-artifact@v8`. Add macOS and
  Windows runners to the `tests` job matrix.

### Added — factor-factory integration

- **`PanelDataset.to_factor_factory_panel()`** — additive adapter returning a
  `factor_factory.tidy.Panel` with full treatment-event and spatial-weights
  round-trip.
- **`Pipeline.as_factor_factory_estimate()`** — thin bridge that dispatches into
  `factor_factory.engines.<family>.estimate` on a converted Panel. Supports
  every factor-factory engine family (did, sdid, rdd, scm, mediation,
  changepoint, stl, panel_reg, inequality, spatial, reporting_bias, hawkes,
  survival, event_study, het_te, dml, climate, diffusion).
- **`nyc311.temporal.panel_dataset_to_factor_factory`** and
  **`spatial_weights_from_panel`** as the function-style equivalents.
- **`nyc311.factors.dispatch_factor_factory_engine`** for direct engine dispatch
  independently of the `Pipeline` API.

### Added — jellycell tearsheets

- New `tearsheets` optional extra: `pip install nyc311[tearsheets]` pulls
  `jellycell>=1.3.5,<2`.
- Both production case studies (`examples/case_studies/rat_containerization/`,
  `examples/case_studies/resolution_equity/`) gained a new tearsheet-generation
  step that emits
  `manuscripts/{METHODOLOGY,DIAGNOSTICS_CHECKLIST,FINDINGS,MANUSCRIPT,AUDIT}.md`
  alongside the authoritative `FINDINGS.md`. Numbers are unchanged — the
  tearsheet is a parallel deliverable.

### Added — new case studies

- **`examples/sdid-multi-borough-policy/`** — self-contained showcase for
  `factor_factory.engines.sdid` over a synthetic 5-borough 311 rollout. Runs
  offline in seconds.
- **`examples/mediation-cascade-resolution/`** — self-contained showcase for
  `factor_factory.engines.mediation.four_way` over a synthetic pilot →
  triage-time → resolution-rate cascade.

### Added — Claude Code infrastructure

- `.claude/agents/release-auditor.md` and
  `.claude/agents/factor-compat-auditor.md` — read-only auditors for release
  preflight and factor-factory-bridge drift.
- `.claude/commands/{bump,release-check,run-case-study}.md`.
- `.claude/skills/{factor-compat,stats-module-discipline,release-bump}.md`.
- `.claude/settings.local.json` permissions allowlist, `.claude/launch.json`
  dev-server configs.
- Top-level `AGENTS.md` (canonical cross-agent-vendor guide — Cursor / Codex /
  Copilot / Aider / Zed / Windsurf read this), `CLAUDE.md` (Claude-specific
  overlay), `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md`,
  `CITATION.cff`.

### Added — examples showcases

- **`examples/factor-factory-quickstart/`** — minimal no-jellycell showcase that
  exercises `PanelDataset.to_factor_factory_panel()` →
  `factor_factory.engines.did.estimate` → pandas in ~50 lines. Starting point
  for consumers who want the adapter without the reporting machinery.

### Added — docs

- `docs/integration.md` — crosswalk between `nyc311` and `factor_factory` (Panel
  schema, stats-module map, engine families).
- `docs/migration-v0-to-v1.md` — before/after snippets for consumer upgrades.
- README — new "factor-factory integration" section + links to all four new
  engine-showcase examples.
- `docs/sdk.md`, `docs/architecture.md`, `docs/index.md`, `docs/releasing.md`,
  `docs/getting-started.md`, `docs/cli.md`, `docs/contributing.md`,
  `docs/examples.md` — refreshed to v1.x framing; `docs/architecture.md` mermaid
  now shows the two new bridges and the jellycell branch.

### Added — previously-unreleased content

The causal-inference, spatial-econometrics, equity, reporting-bias, Bayesian,
and point-process statistical methods listed under `## 0.3.0` below shipped in
source on `main` under that tag, but additional polish, docstring
cross-references to factor-factory, and case-study wiring land together under
v1.0.0.

### Changed — examples isolation

- `examples/*/uv.lock` and `examples/*/.venv/` are gitignored repo-wide. Example
  reproducibility comes from pinned version ranges in each `pyproject.toml`, not
  from committed lockfiles. Four previously-committed `uv.lock` files (~5,000
  lines) were dropped.
- Root prose tooling (prettier) scoped with `exclude: ^examples/` so showcase
  narratives keep their voice.
- Ruff `per-file-ignores` for `examples/**/*.py` broadened to the
  showcase-friendly set (unicode ambiguity, cross-platform shebang, print
  progress) — protects future examples from surprise lint failures.
- Root pre-commit `exclude` regex extended to
  `^examples/.*/(manuscripts|artifacts)/` so committed jellycell tearsheets and
  engine-result JSONs stay off-limits to content-rewriting hygiene hooks
  (blacken-docs, end-of-file-fixer, trailing-whitespace, prettier).

### Changed — jellycell tearsheet reproducibility

- The four case studies commit their `manuscripts/*.md` tearsheets and
  `artifacts/*.json` result files so the jellycell site is reproducible from a
  fresh clone without running the pipeline.
  `factor_factory.jellycell.tearsheets.*` is called with `template_overrides`
  pinning `project` to a stable display name and `generated_at` to a fixed
  string — committed output is byte-identical across machines.

### Known issues

Two upstream factor-factory bugs that the adapter test suite catches and
`xfail`s with clear remediation notes. Neither affects the nyc311 adapter path
itself — the PanelDataset → Panel conversion is correct in both cases.

- `factor_factory.engines.panel_reg.pyfixest` references a `'Coefficient'`
  column that `pyfixest>=0.50` no longer emits. Workaround upstream is a
  column-name update.
- `factor_factory.engines.stl.sktime_stl` reads freq from the DataFrame
  MultiIndex, but pandas doesn't preserve `DatetimeIndex.freq` on MultiIndex
  levels after `set_index`/`sort_index`. Workaround upstream is to fall back on
  `panel.metadata.freq`.

### Contracts

v1.0.0 introduces three new public contracts. All are additive and any change to
them after this release requires the
[`factor-compat-auditor`](https://github.com/random-walks/nyc311/blob/main/.claude/agents/factor-compat-auditor.md)
ceremony:

- `PanelDataset.to_factor_factory_panel(*, outcome_col, provenance, spatial_weights) -> factor_factory.tidy.Panel`
- `Pipeline.as_factor_factory_estimate(panel, *, family, method, outcome, **engine_kwargs)`
- `Pipeline ↔ factor_factory.engines.*` supported-family list
  (`_SUPPORTED_FAMILIES` in
  [`src/nyc311/factors/_factor_factory.py`](https://github.com/random-walks/nyc311/blob/main/src/nyc311/factors/_factor_factory.py)).

Each of the 11 `nyc311.stats` modules with a factor-factory equivalent gained a
`.. note::` block cross-referencing the upstream engine as the preferred
backend. The homegrown functions continue to work for backwards compatibility.

## 0.3.0

- add composable factor pipeline (`nyc311.factors`) with seven built-in domain
  factors (`ComplaintVolumeFactor`, `ResolutionTimeFactor`,
  `TopicConcentrationFactor`, `SeasonalityFactor`, `AnomalyScoreFactor`,
  `ResponseRateFactor`, `RecurrenceFactor`) and an immutable `Pipeline` builder
- add temporal panel module (`nyc311.temporal`) with balanced panel
  construction, treatment-event modeling, and inverse-distance spatial weights
- add statistical modeling module (`nyc311.stats`) with interrupted time series,
  PELT changepoint detection, STL seasonal decomposition, global and local
  Moran's I (LISA) spatial autocorrelation, and panel fixed/random-effects
  regression wrappers
- add `nyc311.pipeline.bulk_fetch()` for full-city per-borough downloads with
  `.meta.json` integrity sidecars
- add the resolution-equity case study under
  `examples/case_studies/resolution_equity/`, exercising the full v0.3.0 surface
  against ~1M real records
- upgrade all model dataclasses to `frozen=True, slots=True`
- add the `stats` optional dependency group (`ruptures`, `linearmodels`, `esda`,
  `libpysal`, `statsmodels`)
- add mypy overrides for the new optional dependencies
- align ruff per-file ignores with the example slugs convention so the
  resolution-equity case study scripts lint cleanly
- standardize public docstrings on Google-style `Args:` / `Returns:` / `Raises:`
  so the mkdocstrings-rendered API reference is uniform across the package

## 0.2.6

- align the published changelog with the docs refresh that already shipped in
  `0.2.5`
- keep the public docs, release notes, and package history in sync after the
  docs-only follow-up patch

## 0.2.5

- sharpen the README and core docs around the stable `0.2.x` package surface
- document the `nyc311` and `nyc-geo-toolkit` relationship more clearly across
  user-facing and maintainer docs
- refresh install, contributor, and release guidance to match the current
  workflow

## 0.2.4

- delegate duplicated geography conversion and boundary-loading helpers back to
  `nyc-geo-toolkit`
- add CI coverage against `nyc-geo-toolkit` on `main` so downstream breakage is
  caught before release
- stabilize compatibility and version checks across local CI, release builds,
  and the toolkit-main validation path

## 0.2.3

- refresh public authorship metadata to credit Blaise Albis-Burdige directly
- add `blaiseab.com` as the portfolio link on package and docs surfaces
- align README, docs, and site metadata with the same attribution model

## 0.2.2

- migrate reusable geography ownership to `nyc-geo-toolkit`
- preserve the public `nyc311.geographies` API through compatibility adapters
- remove duplicated bundled boundary assets from `nyc311` and depend on the
  published toolkit package instead

## 0.2.1

- polish the README and package metadata for a cleaner PyPI project page
- align docs wording with the shipped stable `0.2.x` line
- keep the release workflow current with the validated TestPyPI then PyPI path

## 0.2.0

- ship the first public stable release in the `0.2` line
- include topic coverage, resolution gaps, anomaly detection, report-card
  export, dataframe helpers, and the refreshed `uv` extras/groups and CI setup

## Earlier History

- `0.2.0a1`: internal milestone that retired the older `v0.1` framing in favor
  of an explicit `0.2` release line

## Release history

`nyc311` tracks release history through GitHub Releases and tags.

- `0.1.0`: original foundation release from the earlier narrow project phase

- [View releases](https://github.com/random-walks/nyc311/releases)
- [View tags](https://github.com/random-walks/nyc311/tags)

GitHub Releases remains the authoritative public record of shipped artifacts.
