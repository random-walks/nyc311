# Topic EDA Tearsheet

This tearsheet summarizes a cached Brooklyn slice and highlights topic-rule
coverage, unmatched descriptors, anomaly outliers, and resolution gaps. Refresh
and republish only when you intentionally want to update the tracked report
assets.

## Executive Summary

- The cached slice contains `15000` complaint records sourced from
  `cache/topic-eda-snapshot.csv` (`live fetch`).
- The weakest built-in topic coverage in this slice is `HEAT/HOT WATER` at
  `0.0%` matched.
- The strongest built-in topic coverage is `Noise - Residential` at `92.9%`
  matched.
- The biggest unmatched descriptor driver is `ENTIRE BUILDING` with `1618`
  unmatched rows in the coverage audit.
- The largest anomaly by absolute z-score is `BROOKLYN 03 / Party Music` at
  `+3.28`.
- The highest unresolved share in the cached slice appears in
  `Construction Lead Dust` at `100.0%` unresolved.
- In the synthetic Water System demo, custom rules change coverage from `100.0%`
  to `66.7%`.

## Coverage Rates

![Coverage rate by complaint type](./figures/topic-coverage-by-complaint-type.png)

## Top Unmatched Descriptors

![Top unmatched descriptors](./figures/top-unmatched-descriptors.png)

## Anomaly Scores

![Top anomaly z-scores](./figures/topic-anomaly-zscores.png)

## Resolution Gaps

![Resolution gaps by complaint type](./figures/topic-resolution-gap.png)

## Coverage Metrics

| Complaint type          | Matched | Total | Coverage rate | Top unmatched descriptor      |
| ----------------------- | ------- | ----- | ------------- | ----------------------------- |
| HEAT/HOT WATER          | 0       | 2585  | 0.0%          | ENTIRE BUILDING               |
| Blocked Driveway        | 0       | 907   | 0.0%          | No Access                     |
| Abandoned Vehicle       | 0       | 329   | 0.0%          | With License Plate            |
| Noise - Street/Sidewalk | 0       | 213   | 0.0%          | Loud Music/Party              |
| UNSANITARY CONDITION    | 106     | 446   | 23.8%         | PESTS                         |
| Illegal Parking         | 1256    | 3264  | 38.5%         | Posted Parking Sign Violation |
| Street Condition        | 175     | 260   | 67.3%         | Wear & Tear                   |
| Rodent                  | 67      | 98    | 68.4%         | Signs of Rodents              |
| Noise - Residential     | 1313    | 1414  | 92.9%         | Loud Talking                  |

## Resolution Hotspots

| Complaint type                          | Unresolved count | Total requests | Unresolved share |
| --------------------------------------- | ---------------- | -------------- | ---------------- |
| Construction Lead Dust                  | 4                | 4              | 100.0%           |
| Lot Condition                           | 2                | 2              | 100.0%           |
| Unleashed Dog                           | 2                | 2              | 100.0%           |
| For Hire Vehicle Report                 | 1                | 1              | 100.0%           |
| Harboring Bees/Wasps                    | 1                | 1              | 100.0%           |
| Tobacco or Non-Tobacco Sale             | 1                | 1              | 100.0%           |
| Water Quality                           | 2                | 4              | 50.0%            |
| Wood Pile Remaining                     | 1                | 2              | 50.0%            |
| Graffiti                                | 79               | 171            | 46.2%            |
| Special Projects Inspection Team (SPIT) | 7                | 23             | 30.4%            |

## Custom Rule Demo

| Scenario            | Coverage rate | Matched records | Total records |
| ------------------- | ------------- | --------------- | ------------- |
| Before custom rules | 100.0%        | 3               | 3             |
| After custom rules  | 66.7%         | 2               | 3             |
