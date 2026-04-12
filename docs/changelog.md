# Changelog

## Next

- no unreleased changes are currently documented

## 0.3.0

- add composable factor pipeline (`nyc311.factors`) with seven built-in
  domain factors (`ComplaintVolumeFactor`, `ResolutionTimeFactor`,
  `TopicConcentrationFactor`, `SeasonalityFactor`, `AnomalyScoreFactor`,
  `ResponseRateFactor`, `RecurrenceFactor`) and an immutable `Pipeline`
  builder
- add temporal panel module (`nyc311.temporal`) with balanced panel
  construction, treatment-event modeling, and inverse-distance spatial
  weights
- add statistical modeling module (`nyc311.stats`) with interrupted time
  series, PELT changepoint detection, STL seasonal decomposition, global
  and local Moran's I (LISA) spatial autocorrelation, and panel
  fixed/random-effects regression wrappers
- add `nyc311.pipeline.bulk_fetch()` for full-city per-borough downloads
  with `.meta.json` integrity sidecars
- add the resolution-equity case study under
  `examples/case_studies/resolution_equity/`, exercising the full
  v0.3.0 surface against ~1M real records
- upgrade all model dataclasses to `frozen=True, slots=True`
- add the `stats` optional dependency group (`ruptures`, `linearmodels`,
  `esda`, `libpysal`, `statsmodels`)
- add mypy overrides for the new optional dependencies
- align ruff per-file ignores with the example slugs convention so the
  resolution-equity case study scripts lint cleanly
- standardize public docstrings on Google-style `Args:` / `Returns:` /
  `Raises:` so the mkdocstrings-rendered API reference is uniform across
  the package

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
