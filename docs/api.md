# API Reference

The public API is organized around explicit namespaces rather than a flat root
package.

The root `nyc311` package is intentionally minimal and only exposes version
metadata. Import functionality from the canonical public modules below.

`nyc311.geographies` is the one namespace that intentionally fronts another
package: it preserves the 311-facing geography surface while delegating generic
boundary loading and normalization primitives to `nyc-geo-toolkit`.

Update docstrings and exported symbols in `src/nyc311/` rather than editing this
reference structure by hand.

## Root Package

::: nyc311

## Models

::: nyc311.models

## IO

::: nyc311.io

## Analysis

::: nyc311.analysis

## Geographies

::: nyc311.geographies

## Samples

::: nyc311.samples

## Export

::: nyc311.export

## Pipeline

::: nyc311.pipeline

## DataFrames

::: nyc311.dataframes

## Spatial

::: nyc311.spatial

## Plotting

::: nyc311.plotting

## Presets

::: nyc311.presets

## CLI

::: nyc311.cli
