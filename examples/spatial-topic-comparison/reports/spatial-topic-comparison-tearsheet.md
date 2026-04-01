# Spatial Topic Comparison Tearsheet

This tearsheet compares residential-noise topics before and after spatially
joining the packaged sample points to the full NYC community-district layer.

## Executive Summary

- The packaged sample contributes `9` residential-noise points, and `9` of them
  land inside a district polygon when the full layer is used.
- The strongest party-music intensity after the spatial join appears in
  `QUEENS 01` at `66.7%`.
- The sharpest dominant-topic signal appears in `QUEENS 01`, where `Party Music`
  reaches `66.7%`.
- The most balanced joined district is `BROOKLYN 01`, where the leading topic
  reaches only `50.0%`.
- Spatial enrichment changes the raw district label for `3` sample rows, which
  is why this example reports both raw and spatial district views.

## Spatial Join Preview

![Spatial join preview](./figures/spatial-topic-comparison-preview.png)

## Dominant Topic Map

![Dominant topic after spatial enrichment](./figures/spatial-dominant-noise-topics.png)

## Party Music Intensity

![Party music intensity by joined district](./figures/spatial-party-music-intensity.png)

## Topic Mix By Joined District

![Normalized topic mix after spatial enrichment](./figures/spatial-topic-mix-by-district.png)

## Raw vs Spatial District Summary

| View             | District     | Total complaints | Dominant topic | Dominant share | Party music share |
| ---------------- | ------------ | ---------------- | -------------- | -------------- | ----------------- |
| Raw record label | QUEENS 02    | 3                | Party Music    | 66.7%          | 66.7%             |
| Raw record label | BROOKLYN 01  | 2                | Banging        | 50.0%          | 50.0%             |
| Raw record label | MANHATTAN 10 | 2                | Banging        | 50.0%          | 50.0%             |
| Raw record label | BROOKLYN 03  | 2                | Construction   | 50.0%          | 0.0%              |
| Spatial join     | QUEENS 01    | 3                | Party Music    | 66.7%          | 66.7%             |
| Spatial join     | BROOKLYN 01  | 2                | Banging        | 50.0%          | 50.0%             |
| Spatial join     | MANHATTAN 10 | 2                | Banging        | 50.0%          | 50.0%             |
| Spatial join     | BROOKLYN 03  | 2                | Construction   | 50.0%          | 0.0%              |

## Reassigned Rows

| Request ID | Raw district | Spatial district | Topic       | Descriptor                                   |
| ---------- | ------------ | ---------------- | ----------- | -------------------------------------------- |
| 1010       | QUEENS 02    | QUEENS 01        | Party Music | Neighbors arguing loudly with bass music     |
| 1011       | QUEENS 02    | QUEENS 01        | Party Music | Party speakers shaking shared wall           |
| 1012       | QUEENS 02    | QUEENS 01        | Banging     | Repetitive thumping noise from upstairs unit |

## Joined District Metrics

| Joined district | Total complaints | Dominant topic | Dominant share | Party music share |
| --------------- | ---------------- | -------------- | -------------- | ----------------- |
| QUEENS 01       | 3                | Party Music    | 66.7%          | 66.7%             |
| BROOKLYN 01     | 2                | Banging        | 50.0%          | 50.0%             |
| MANHATTAN 10    | 2                | Banging        | 50.0%          | 50.0%             |
| BROOKLYN 03     | 2                | Construction   | 50.0%          | 0.0%              |
