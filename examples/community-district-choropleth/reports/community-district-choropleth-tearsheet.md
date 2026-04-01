# Community District Choropleth Tearsheet

This tearsheet summarizes the packaged `Noise - Residential` sample at the
community-district level. The map uses the full NYC district layer so grey
polygons show where the packaged sample has no district-level coverage.

## Executive Summary

- The packaged sample contains `9` noise complaints across `4` sampled
  districts.
- The strongest party-music intensity appears in `QUEENS 02` at `66.7%` (2 of
  3).
- The sharpest dominant-topic signal appears in `QUEENS 02`, where `Party Music`
  accounts for `66.7%` of sampled district noise.
- The flattest topic mix appears in `BROOKLYN 01`, where the leading topic
  reaches only `50.0%`.
- The full district layer contains `55` no-data polygons that do not appear in
  the packaged sample.

## Dominant Topic Map

![Dominant noise topic by community district](./figures/community-district-dominant-noise-topics.png)

## Party Music Intensity

![Party music intensity by district](./figures/community-district-party-music-intensity.png)

## Topic Mix Snapshot

![Topic mix for top sampled districts](./figures/community-district-topic-mix-topn.png)

## District Metrics

| District     | Total complaints | Party music share | Dominant topic | Dominant share |
| ------------ | ---------------- | ----------------- | -------------- | -------------- |
| QUEENS 02    | 3                | 66.7%             | Party Music    | 66.7%          |
| BROOKLYN 01  | 2                | 50.0%             | Banging        | 50.0%          |
| MANHATTAN 10 | 2                | 50.0%             | Banging        | 50.0%          |
| BROOKLYN 03  | 2                | 0.0%              | Construction   | 50.0%          |
