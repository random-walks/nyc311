# About the data — NYC 311

## Boroughs in this run

- BRONX
- BROOKLYN
- MANHATTAN
- QUEENS
- STATEN ISLAND

## Catalogue

| Borough       | Records | Types seen | Supported-type rows | Date start | Date end   | With coords | With resolution | CDs seen | Cache bytes |
| ------------- | ------: | ---------: | ------------------: | ---------- | ---------- | ----------: | --------------: | -------: | ----------: |
| BRONX         |  100000 |        148 |               60951 | 2026-02-18 | 2026-04-05 |       96921 |           98105 |       17 |    47121280 |
| BROOKLYN      |  100000 |        156 |               57059 | 2026-03-05 | 2026-04-05 |       96889 |           94901 |       21 |    46643749 |
| MANHATTAN     |  100000 |        162 |               45012 | 2026-02-15 | 2026-04-05 |       97148 |           94060 |       15 |    44447120 |
| QUEENS        |  100000 |        154 |               58594 | 2026-02-28 | 2026-04-05 |       91017 |           96147 |       20 |    44299495 |
| STATEN ISLAND |  100000 |        153 |               36979 | 2025-08-21 | 2026-04-05 |       96834 |           97953 |        5 |    37028395 |

## Source layers

| Name                         | URL / file                                            | Rows / features |
| ---------------------------- | ----------------------------------------------------- | --------------: |
| NYC 311 Service Requests     | https://data.cityofnewyork.us/resource/erm2-nwe9.json |          500000 |
| borough                      | borough.geojson                                       |               5 |
| census_tract                 | census_tract.geojson                                  |            2325 |
| community_district           | community_district.geojson                            |              59 |
| council_district             | council_district.geojson                              |              51 |
| neighborhood_tabulation_area | neighborhood_tabulation_area.geojson                  |             262 |
| zcta                         | zcta.geojson                                          |             178 |

## EDA tables (CSV)

Machine-readable slices written next to this report. Preview (truncated) below.

### `sample_summary.csv`

[Download CSV](tables/sample_summary.csv)

| desc_sample_cache | rows_loaded | min_created_date | max_created_date |
| ----------------- | ----------- | ---------------- | ---------------- |
| True              | 500000      | 2025-08-21       | 2026-04-05       |

### `rows_by_borough.csv`

[Download CSV](tables/rows_by_borough.csv)

| borough       | count  |
| ------------- | ------ |
| BRONX         | 100000 |
| BROOKLYN      | 100000 |
| MANHATTAN     | 100000 |
| QUEENS        | 100000 |
| STATEN ISLAND | 100000 |

### `top_complaint_types_citywide.csv`

[Download CSV](tables/top_complaint_types_citywide.csv)

| complaint_type           | count |
| ------------------------ | ----- |
| Illegal Parking          | 71519 |
| Noise - Residential      | 45661 |
| HEAT/HOT WATER           | 42767 |
| Street Condition         | 34187 |
| Blocked Driveway         | 21954 |
| Snow or Ice              | 18860 |
| UNSANITARY CONDITION     | 14410 |
| Noise - Street/Sidewalk  | 14241 |
| Dirty Condition          | 10980 |
| Abandoned Vehicle        | 10958 |
| Water System             | 10189 |
| Traffic Signal Condition | 9906  |
| PLUMBING                 | 9756  |
| Noise                    | 8456  |

### `daily_counts_last_45_days.csv`

[Download CSV](tables/daily_counts_last_45_days.csv)

| day        | count |
| ---------- | ----- |
| 2026-02-20 | 4597  |
| 2026-02-21 | 3982  |
| 2026-02-22 | 3872  |
| 2026-02-23 | 8166  |
| 2026-02-24 | 11375 |
| 2026-02-25 | 6308  |
| 2026-02-26 | 5138  |
| 2026-02-27 | 4893  |
| 2026-02-28 | 5435  |
| 2026-03-01 | 6359  |
| 2026-03-02 | 7568  |
| 2026-03-03 | 7029  |
| 2026-03-04 | 7888  |
| 2026-03-05 | 8486  |

## Figures

![all-scatter-lib-cover](figures/all-scatter-lib-cover.png)

![choropleth-by-borough-bronx](figures/choropleth-by-borough-bronx.png)

![choropleth-by-borough-brooklyn](figures/choropleth-by-borough-brooklyn.png)

![choropleth-complaint-density-by-type](figures/choropleth-complaint-density-by-type.png)

![choropleth-complaint-density-community-district](figures/choropleth-complaint-density-community-district.png)

![choropleth-dominant-topic](figures/choropleth-dominant-topic.png)

![choropleth-resolution-gap](figures/choropleth-resolution-gap.png)

![complaint-type-distribution](figures/complaint-type-distribution.png)

![heatmap-hour-weekday-by-type](figures/heatmap-hour-weekday-by-type.png)

![heatmap-hour-weekday](figures/heatmap-hour-weekday.png)

![map-library-header-horizontal](figures/map-library-header-horizontal.png)

![map-zoom-detail](figures/map-zoom-detail.png)

![record-counts-by-borough](figures/record-counts-by-borough.png)

![records-per-year](figures/records-per-year.png)

![resolution-gap-by-borough](figures/resolution-gap-by-borough.png)

![resolution-rate-sample](figures/resolution-rate-sample.png)

![scatter-all-complaints-nyc](figures/scatter-all-complaints-nyc.png)

![scatter-complaints-bronx](figures/scatter-complaints-bronx.png)

![scatter-complaints-brooklyn](figures/scatter-complaints-brooklyn.png)

![scatter-complaints-by-type-faceted](figures/scatter-complaints-by-type-faceted.png)

![scatter-complaints-manhattan](figures/scatter-complaints-manhattan.png)

![scatter-complaints-queens](figures/scatter-complaints-queens.png)

![scatter-complaints-staten_island](figures/scatter-complaints-staten_island.png)

![timeseries-by-borough-monthly](figures/timeseries-by-borough-monthly.png)

![timeseries-citywide-daily](figures/timeseries-citywide-daily.png)

![timeseries-topic-trends](figures/timeseries-topic-trends.png)

![top-unmatched-descriptors](figures/top-unmatched-descriptors.png)

![topic-anomaly-zscores](figures/topic-anomaly-zscores.png)

![topic-coverage-by-complaint-type](figures/topic-coverage-by-complaint-type.png)
