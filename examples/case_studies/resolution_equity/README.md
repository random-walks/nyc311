# Seasonal Complaint Dynamics and Resolution Equity Across NYC Community Districts, 2020--2024

A longitudinal case study using the `nyc311` toolkit to investigate whether
311 complaint resolution times differ systematically by neighborhood
demographics after controlling for complaint volume and type.

## Research Questions

1. **Seasonal structure**: What are the dominant seasonal patterns in NYC 311
   complaints, and do they differ by complaint type?
2. **Structural breaks**: Did COVID-19 lockdowns and subsequent reopenings
   cause detectable changepoints in complaint volume?
3. **Resolution equity**: After controlling for complaint volume, complaint
   type, and time trends, do community district demographics (median income,
   racial composition, housing tenure) predict resolution time?
4. **Spatial clustering**: Do slow-resolution districts cluster spatially,
   suggesting systemic rather than idiosyncratic causes?

## Methodology

### Data

- **Source**: NYC Open Data 311 Service Requests (Socrata dataset `erm2-nwe9`)
- **Period**: January 2020 through December 2024 (60 months)
- **Unit of analysis**: 59 NYC community districts x 60 monthly periods = 3,540 observations
- **Complaint types**: All types, with per-type breakdowns

### Panel Construction

Balanced panel built with `nyc311.temporal.build_complaint_panel()`:

- Complaint counts (total and by type)
- Resolution rate (fraction with `resolution_description`)
- Median resolution days (days from `created_date` to period end for resolved complaints)
- ACS 5-year demographic covariates (median household income, percent non-white,
  percent renter-occupied, population density)

### Statistical Methods

1. **STL Decomposition** (Cleveland et al., 1990): Extract trend, seasonal, and
   residual components from city-wide monthly complaint series by type.

2. **PELT Changepoint Detection** (Killick et al., 2012): Identify structural
   breaks in complaint volume corresponding to known policy events (COVID-19
   lockdown March 2020, reopening phases, rat containerization mandate 2024).

3. **Two-Way Fixed Effects Panel Regression**: District FE + month FE with
   clustered standard errors at the district level.
   - Outcome: median resolution days
   - Regressors: log per-capita complaint volume, complaint-type HHI,
     percent non-white, log median income, percent renter

4. **Global Moran's I** (Rey & Anselin, 2007): Test for spatial autocorrelation
   in mean resolution time across community districts.

5. **Local Moran's I (LISA)**: Identify hot/cold spot clusters of slow/fast
   resolution.

### Reporting Bias Caveat

NYC 311 complaint data reflects *reporting behavior*, not underlying conditions.
More affluent and civically engaged neighborhoods tend to file more complaints
per capita (O'Brien et al., 2015). This study focuses on *resolution time
conditional on a complaint being filed*, which is the testable equity
dimension---every filed complaint deserves equal service regardless of
neighborhood demographics.

## Scripts

| Script | Description |
| --- | --- |
| `01_fetch_data.py` | Download 5 years of 311 data via `bulk_fetch()` |
| `02_build_panel.py` | Construct balanced community-district x month panel |
| `03_seasonal_decomposition.py` | STL decomposition of city-wide series |
| `04_equity_analysis.py` | Two-way FE regression for resolution equity |
| `05_spatial_analysis.py` | Moran's I and LISA cluster analysis |
| `06_changepoint_detection.py` | PELT changepoint detection |

## Dependencies

```bash
pip install nyc311[stats,spatial,dataframes]
```

## References

- Bernal, J. L., Cummins, S., & Gasparrini, A. (2017). Interrupted time series
  regression for the evaluation of public health interventions: a tutorial.
  _International Journal of Epidemiology_, 46(1), 348--355.
- Cleveland, R. B., Cleveland, W. S., McRae, J. E., & Terpenning, I. J. (1990).
  STL: A seasonal-trend decomposition procedure based on loess. _Journal of
  Official Statistics_, 6(1), 3--33.
- Killick, R., Fearnhead, P., & Eckley, I. A. (2012). Optimal detection of
  changepoints with a linear computational cost. _JASA_, 107(500), 1590--1598.
- O'Brien, D. T., Sampson, R. J., & Winship, C. (2015). Ecometrics in the age
  of big data: Measuring and assessing "broken windows" using large-scale
  administrative records. _Sociological Methodology_, 45(1), 101--147.
- Rey, S. J., & Anselin, L. (2007). PySAL: A Python library of spatial
  analytical methods. _Review of Regional Studies_, 37(1), 5--27.
- Wooldridge, J. M. (2010). _Econometric analysis of cross section and panel
  data_ (2nd ed.). MIT Press.
