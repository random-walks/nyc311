# Findings: NYC 311 Complaint Dynamics and Resolution Patterns, 2023--2024

**Analysis date**: April 2026
**Dataset**: 1,000,000 NYC 311 service requests (May 2023 -- December 2024)
**Source**: NYC Open Data Socrata API (`erm2-nwe9`)
**Toolkit**: `nyc311` v0.3.0 (factors, temporal, stats modules)

---

## 1. Data Summary

| Metric | Value |
| --- | --- |
| Total records | 1,000,000 |
| Date range | May 2023 -- December 2024 (20 months) |
| Geographic units | 76 community districts (incl. unspecified) |
| Panel observations | 1,520 (76 units x 20 periods) |
| Unique complaint types | 199 |
| Mean complaints per district-month | 658 |
| Overall resolution rate | 21.3% |

The dataset was fetched using `nyc311.pipeline.bulk_fetch()` with
per-borough downloads of up to 200,000 recent records each. Records
are sorted most-recent-first, which explains the relatively low
resolution rate --- many recent complaints remain open at the time of
data extraction.

---

## 2. Complaint Type Distribution

NYC 311 receives complaints across 199 distinct categories, but
volume is heavily concentrated in a small number of types.

### Top 10 Complaint Types

| Rank | Complaint Type | Count | Share | Resolution Rate |
| --- | --- | --- | --- | --- |
| 1 | Illegal Parking | 127,533 | 12.75% | 100.0% |
| 2 | Noise - Residential | 127,507 | 12.75% | 100.0% |
| 3 | HEAT/HOT WATER | 120,231 | 12.02% | 100.0% |
| 4 | Blocked Driveway | 45,706 | 4.57% | 100.0% |
| 5 | Noise - Street/Sidewalk | 30,782 | 3.08% | 100.0% |
| 6 | UNSANITARY CONDITION | 29,746 | 2.97% | 100.0% |
| 7 | Street Condition | 20,929 | 2.09% | 99.9% |
| 8 | Water System | 20,409 | 2.04% | 99.6% |
| 9 | Abandoned Vehicle | 20,130 | 2.01% | 100.0% |
| 10 | PLUMBING | 17,166 | 1.72% | 100.0% |

### Concentration Analysis

- **Top 5 types account for 45.2%** of all complaints
- **Top 10 types account for 56.0%** of all complaints
- The remaining 189 categories share the other 44%

The "Big Three" --- Illegal Parking, Noise - Residential, and HEAT/HOT
WATER --- each individually represent approximately 12--13% of all
complaints and together account for over 37% of total volume. This
extreme concentration has important implications for resource allocation:
improvements in processing these three categories would affect over a
third of all service requests.

The near-perfect resolution rates for the top types (all >= 99.6%)
indicate that high-volume categories have well-established response
protocols. Lower resolution rates in the long-tail categories warrant
further investigation.

### Factor Pipeline: Topic Concentration

Using the `TopicConcentrationFactor` (Herfindahl-Hirschman Index), we
measured complaint-type diversity within each community district.

- **Mean HHI: 0.027** --- very low, indicating most districts receive a
  diverse mix of complaint types
- This is consistent with the 199 active categories; no single type
  dominates any individual district

---

## 3. Geographic Variation

### Borough-Level Patterns

| Borough | Mean Monthly Complaints | Resolution Rate |
| --- | --- | --- |
| Staten Island | 2,479 | 99.0% |
| Manhattan | 751 | 19.7% |
| Bronx | 665 | 15.3% |
| Queens | 520 | 14.7% |
| Brooklyn | 496 | 14.9% |

**Key finding**: Staten Island's per-district complaint volume is
3--5x higher than other boroughs, and its resolution rate (99.0%) is
dramatically higher than the citywide average. This anomaly likely
reflects Staten Island's smaller number of community districts (3
primary) concentrating volume, combined with a higher share of
complaint types that have rapid-closure protocols (particularly vehicle
and sanitation complaints).

The remaining four boroughs cluster tightly between 14.7--19.7%
resolution rate, with Manhattan's slightly higher rate (19.7%)
potentially reflecting different agency routing patterns for its
complaint mix.

### District-Level Extremes

**Highest-volume districts** (mean monthly complaints):

| District | Mean Monthly | Borough |
| --- | --- | --- |
| Staten Island 01 | 4,115 | Staten Island |
| Staten Island 03 | 3,131 | Staten Island |
| Bronx 12 | 2,820 | Bronx |
| Staten Island 02 | 2,649 | Staten Island |
| Manhattan 12 | 1,455 | Manhattan |

**Lowest-resolution districts** (resolution rate):

| District | Resolution Rate | Borough |
| --- | --- | --- |
| Queens 80 | 13.0% | Queens |
| Queens 83 | 13.7% | Queens |
| Queens 10 | 14.3% | Queens |
| Brooklyn 01 | 14.6% | Brooklyn |
| Brooklyn 18 | 14.7% | Brooklyn |

Queens districts appear disproportionately in the lowest-resolution
group, with three of the bottom five districts in Queens. This
geographic clustering suggests a borough-level systemic factor rather
than district-specific issues.

### Variation Metrics

- **Coefficient of variation (complaints):** 1.05 --- very high
  dispersion; complaint volume varies enormously across districts
- **Coefficient of variation (resolution):** 0.97 --- similarly high
  dispersion in resolution rates
- These CVs > 1.0 indicate the standard deviation exceeds the mean,
  driven primarily by the Staten Island outlier effect

---

## 4. Seasonal Decomposition (STL)

Using the STL decomposition method (Cleveland et al., 1990) on the
city-wide monthly complaint series:

| Component | Value |
| --- | --- |
| Peak seasonal month | **December** |
| Trough seasonal month | **April** |
| Seasonal amplitude | 269,484 complaints |
| Residual std | ~0 (negligible) |

### Interpretation

The **December peak** is consistent with the dominance of HEAT/HOT
WATER complaints (12% of all volume), which surge during winter
heating season when building heating systems fail. This is the single
largest seasonal driver in NYC 311 data.

The **April trough** aligns with the transition from heating season to
spring, when heating complaints drop before summer noise and pest
complaints rise.

The near-zero residual standard deviation indicates the 20-month
series is almost entirely explained by trend + seasonal components,
leaving virtually no unexplained variation. This is expected for a
short series where the trend component absorbs most non-seasonal
dynamics.

---

## 5. Changepoint Detection

The PELT algorithm (Killick et al., 2012) detected **one structural
break** in the city-wide monthly complaint series:

| Breakpoint | Date | Nearest Known Event |
| --- | --- | --- |
| 1 | **August 2024** | --- |

### Interpretation

The August 2024 breakpoint likely reflects a seasonal inflection
point: the transition from summer peak (noise, street-condition
complaints) to fall patterns (heating-season ramp-up). With only 20
months of data, the algorithm identifies the most prominent
volume-level shift.

In a longer time series spanning the full 2020--2024 period, we would
expect additional breakpoints corresponding to:

- **March 2020**: COVID-19 lockdown (NYC PAUSE order), which caused a
  dramatic drop in commercial-noise and parking complaints
- **June--July 2020**: Phased reopening, with complaints rebounding
- **Early 2022**: Omicron wave effects on staffing and service delivery

The single breakpoint in our dataset underscores the importance of
longer time horizons for policy evaluation via changepoint methods.

---

## 6. Factor Pipeline Results

We composed a four-factor pipeline using the `nyc311.factors` module
and ran it across all 1,520 panel contexts:

| Factor | Mean | Interpretation |
| --- | --- | --- |
| `complaint_volume` | 657.9 | Avg complaints per district-month |
| `response_rate` | 21.3% | Low due to recency bias in dataset |
| `topic_concentration` (HHI) | 0.027 | Highly diverse complaint mix |
| `recurrence_rate` | 8.2% | ~8% of locations see repeat complaints |

### Recurrence Analysis

The **8.2% recurrence rate** (fraction of unique complaint locations
with more than one complaint) indicates that repeat-complaint
locations are a meaningful but minority phenomenon. This recurrence
rate is likely an underestimate because:

1. Coordinate precision limits (4 decimal places = ~11m) may split
   genuinely co-located complaints
2. The 20-month window is too short to capture full recurrence cycles
   for chronic issues like structural building problems

Policy implication: targeted intervention at the ~8% of locations
generating repeat complaints could yield outsized efficiency gains.

---

## 7. Equity Implications

### What the Data Shows

The most striking equity-relevant finding is the **5:1 ratio** between
Staten Island's resolution rate (99%) and the other boroughs'
(~15%). While some of this gap reflects complaint-type composition
(SI has proportionally more quick-closure categories), the magnitude
warrants further investigation into whether borough-level resource
allocation systematically favors certain communities.

Within the four core boroughs (Bronx, Brooklyn, Manhattan, Queens),
the variation is smaller (14.7--19.7%) but still present. The cluster
of low-resolution Queens districts merits investigation --- is it driven
by complaint complexity, agency staffing patterns, or systemic
under-resourcing?

### Limitations

1. **Recency bias**: The dataset is sorted most-recent-first, so many
   complaints are still in-progress. Resolution rates should be
   interpreted as lower bounds.
2. **Reporting bias**: As documented by O'Brien et al. (2015), 311
   complaint filing rates correlate with neighborhood socioeconomic
   characteristics. Higher complaint volumes in some districts may
   reflect greater civic engagement rather than worse underlying
   conditions.
3. **No demographic covariates**: This analysis did not join ACS
   demographic data. A full equity assessment requires controlling for
   median income, racial composition, and housing tenure.
4. **20-month window**: The most-recent-first sampling strategy
   captured May 2023 -- December 2024, limiting temporal analysis.
   A complete 2020--2024 panel would enable more robust
   difference-in-differences designs.

### Recommended Next Steps

1. **Join ACS 5-year estimates** to community districts and run the
   two-way fixed effects regression (script `04_equity_analysis.py`)
   with demographic covariates
2. **Extend the time series** using `bulk_fetch()` with
   `created_date_sort="asc"` to capture the full 2020--2024 period
3. **Apply interrupted time series** to evaluate specific policy
   interventions (e.g., the 2024 rat containerization mandate)
4. **Run spatial weights and Moran's I** with
   `nyc311.stats.global_morans_i()` to test whether resolution-time
   clusters are statistically significant

---

## 8. Methodological Notes

### Tools Used

| Component | nyc311 Module | Method |
| --- | --- | --- |
| Data acquisition | `nyc311.pipeline.bulk_fetch()` | Per-borough Socrata streaming |
| Panel construction | `nyc311.temporal.build_complaint_panel()` | Balanced (unit x period) |
| Factor computation | `nyc311.factors.Pipeline` | 4-factor composition |
| Seasonal decomposition | `nyc311.stats.seasonal_decompose()` | STL (period=12) |
| Changepoint detection | `nyc311.stats.detect_changepoints()` | PELT (BIC penalty) |

### Reproducibility

All results can be reproduced by running:

```bash
pip install nyc311[stats,dataframes]
python examples/case_studies/resolution_equity/run_analysis.py
```

The analysis script uses deterministic caching --- re-runs skip
already-downloaded boroughs. Raw results are persisted to
`data/analysis_results.json`.

---

## References

- Cleveland, R. B., Cleveland, W. S., McRae, J. E., & Terpenning, I.
  J. (1990). STL: A seasonal-trend decomposition procedure based on
  loess. _Journal of Official Statistics_, 6(1), 3--33.
- Killick, R., Fearnhead, P., & Eckley, I. A. (2012). Optimal
  detection of changepoints with a linear computational cost. _Journal
  of the American Statistical Association_, 107(500), 1590--1598.
- O'Brien, D. T., Sampson, R. J., & Winship, C. (2015). Ecometrics in
  the age of big data: Measuring and assessing "broken windows" using
  large-scale administrative records. _Sociological Methodology_,
  45(1), 101--147.
- Wooldridge, J. M. (2010). _Econometric analysis of cross section and
  panel data_ (2nd ed.). MIT Press.
