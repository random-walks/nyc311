# Changelog

## Next

- no unreleased changes are currently documented

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
