# Resolution Equity in NYC 311 Service Delivery

A longitudinal case study using the `nyc311` toolkit to investigate whether
311 complaint resolution times differ systematically by neighborhood
demographics after controlling for complaint volume, type, and seasonal
patterns.

## Data

- **Source**: 1,000,000 NYC 311 service requests from NYC Open Data
  (Socrata dataset `erm2-nwe9`)
- **Panel**: 76 community districts x 20 monthly periods = 1,520 observations
- **Demographics**: ACS 2022 5-year estimates (population, race, income,
  tenure) from the Census Bureau, shipped in `data/demographics.csv`
  covering 51 community districts
- **Boundaries**: Real community district polygons and centroids via
  `nyc_geo_toolkit`

## Key Findings

### Resolution time increases with complaint volume

The two-way fixed effects regression (entity + time FE, clustered SE)
finds that **log complaint volume** is a highly significant predictor
of median resolution days (coeff = +4.01, SE = 0.97, p < 0.001,
R-sq = 0.33).  Districts with higher complaint burdens take longer to
resolve cases, even after absorbing district-specific and month-specific
unobservables.

### Complaint inequality is driven by between-borough differences

The Theil T index on complaint rates is **T = 0.225**, decomposing as
73.7% between-group (borough-level) and 26.3% within-group.  This means
nearly three-quarters of the inequality in complaint burden across
community districts is attributable to differences *between* boroughs
rather than variation within the same borough.  Staten Island districts
are the largest contributors (STATEN ISLAND 01 = +0.156, SI 03 = +0.089),
reflecting their outsized complaint-to-population ratio.

### Most of the resolution-time gap is explained by observables

The Oaxaca-Blinder decomposition splits districts into above- and
below-median income groups (using real ACS 2022 data) and finds:

- **Total gap**: low-income districts resolve 0.77 days *faster* on average
- **Explained component**: 80% of the gap is accounted for by differences
  in renter percentage (the dominant contributor at -0.76), non-white
  population share (+0.22), and complaint volume (-0.07)
- **Unexplained component**: only 20% remains unexplained

The finding that low-income districts resolve faster is counterintuitive
and likely reflects the composition of complaint types: high-income
districts may file more complaints that require longer bureaucratic
processes (e.g., building permits, noise), while low-income districts
file more complaints with fast turnaround (e.g., heat/hot water with
legally mandated response times).

### Resolution times cluster spatially

Global Moran's I for mean resolution time is **I = 0.379** (z = 2.68,
p = 0.007), indicating statistically significant positive spatial
autocorrelation.  Slow-resolving districts tend to neighbor other
slow-resolving districts.  LISA analysis identifies 2 high-high clusters
(slow-resolution hotspots), 9 high-low outliers, and 6 low-low clusters
(fast-resolution coldspots).  The spatial lag factor confirms that Queens
districts (CDs 03, 04, 06, 07) form a contiguous slow-resolution
cluster with neighborhood averages near 14.7 days, while Brooklyn
districts (CDs 06, 07, 14, 15) form a fast-resolution cluster
averaging 10--11 days.

### A structural break occurred in August 2024

PELT changepoint detection identifies a single breakpoint at
**August 2024**, dividing the 20-month series into two segments.  The
interrupted time series model at the March 2024 rat containerization
mandate date finds a statistically significant level change (-425,361,
p < 0.001) and trend change (+34,886, p = 0.001).  These large
magnitudes reflect the model operating on city-wide aggregated complaint
volume; the sharp rise in the second segment coincides with the
post-summer complaint surge and the expanded 311 categories in late
2024.

### Reporting bias estimation is inconclusive with current data

The latent EM model converges in 2 iterations but estimates a uniform
reporting probability of 0.50 across all 51 districts.  This flat
result indicates that with only 3 ACS covariates and aggregated
complaint counts, the model cannot distinguish between differential
true rates and differential reporting propensity.  A more granular
analysis --- per complaint type, with additional covariates like 311
app adoption rates or social media engagement --- would be needed to
detect meaningful reporting heterogeneity.

### Equity implications

The combination of findings paints a nuanced picture: complaint
*burden* is highly unequal (Theil T = 0.225) and concentrated across
boroughs, but resolution *speed* does not systematically disadvantage
low-income or majority-minority neighborhoods after controlling for
complaint volume.  The spatial clustering of slow resolution in Queens
and fast resolution in Brooklyn suggests that operational factors
(staffing, agency workflows) rather than demographic composition drive
resolution disparities.

## Research Questions

1. **Seasonal structure**: What are the dominant seasonal patterns in NYC 311
   complaints, and do they differ by complaint type?
2. **Structural breaks**: Did COVID-19 lockdowns and subsequent reopenings
   cause detectable changepoints in complaint volume?
3. **Resolution equity**: After controlling for complaint volume, complaint
   type, and time trends, do community district demographics predict
   resolution time?
4. **Spatial clustering**: Do slow-resolution districts cluster spatially,
   suggesting systemic rather than idiosyncratic causes?
5. **Reporting bias**: Do neighborhoods differ in their propensity to report
   complaints, and how does this affect equity conclusions?

## Methods

| Method | Implementation | Purpose |
| --- | --- | --- |
| STL Decomposition | `nyc311.stats.seasonal_decompose()` | Extract trend, seasonal, and residual components |
| STL Anomaly Detection | `nyc311.stats.detect_stl_anomalies()` | Flag observations with extreme residuals |
| PELT Changepoint Detection | `nyc311.stats.detect_changepoints()` | Identify structural breaks in complaint volume |
| Two-Way Fixed Effects | `linearmodels.PanelOLS` | District + time FE regression for resolution equity |
| Interrupted Time Series | `nyc311.stats.interrupted_time_series()` | Evaluate level/trend changes at policy interventions |
| Theil T Index | `nyc311.stats.theil_index()` | Decompose inequality between/within boroughs |
| Oaxaca-Blinder Decomposition | `nyc311.stats.oaxaca_blinder_decomposition()` | Decompose resolution-time gap by income group |
| Global Moran's I | `nyc311.stats.global_morans_i()` | Test for spatial autocorrelation in resolution times |
| Local Moran's I (LISA) | `nyc311.stats.local_morans_i()` | Identify hot/cold spot clusters |
| Spatial Lag Factor | `nyc311.factors.SpatialLagFactor` | Neighborhood-average resolution metric |
| Equity Gap Factor | `nyc311.factors.EquityGapFactor` | Ratio of district resolution time to citywide median |
| Latent Reporting Bias (EM) | `nyc311.stats.latent_reporting_bias_em()` | Separate observed counts into true rates and reporting probabilities |

## Scripts

| Script | Description |
| --- | --- |
| `01_fetch_data.py` | Download 311 data via `bulk_fetch()` |
| `02_build_panel.py` | Construct balanced community-district x month panel |
| `03_decomposition_and_anomalies.py` | STL decomposition + anomaly detection |
| `04_equity_analysis.py` | Panel FE, Theil index, Oaxaca-Blinder, EquityGapFactor |
| `05_spatial_analysis.py` | Moran's I, LISA clusters, spatial lag factor |
| `06_policy_evaluation.py` | PELT changepoints + interrupted time series |
| `07_reporting_bias.py` | Latent reporting bias estimation via EM |
| `08_generate_findings.py` | Compile all results into FINDINGS.md |
| `run_analysis.py` | Orchestrator: runs all steps in sequence |
| `main.py` | Entry point (delegates to `run_analysis.py`) |

## Quick Start

```bash
pip install "nyc311[stats,spatial,dataframes]"
cd examples/case_studies/resolution_equity
python run_analysis.py
```

The first run fetches ~1M complaints from Socrata (requires internet).
Subsequent runs use the cached data.

## Demographic Covariates

The `data/demographics.csv` file contains **real ACS 2022 5-year
estimates** from the Census Bureau for 51 NYC community districts
(mapped from PUMAs).  Columns: `unit_id`, `population`, `pct_nonwhite`,
`log_median_income`, `pct_renter`.  This file is required for the
equity analysis and reporting bias steps.

## References

- Bernal, J. L., Cummins, S., & Gasparrini, A. (2017). Interrupted time series
  regression for the evaluation of public health interventions: a tutorial.
  *Int. J. Epidemiology*, 46(1), 348--355.
- Cleveland, R. B., Cleveland, W. S., McRae, J. E., & Terpenning, I. J. (1990).
  STL: A seasonal-trend decomposition procedure based on loess. *J. Official
  Statistics*, 6(1), 3--33.
- Killick, R., Fearnhead, P., & Eckley, I. A. (2012). Optimal detection of
  changepoints with a linear computational cost. *JASA*, 107(500), 1590--1598.
- O'Brien, D. T., Sampson, R. J., & Winship, C. (2015). Ecometrics in the age
  of big data. *Sociological Methodology*, 45(1), 101--147.
- Oaxaca, R. (1973). Male-female wage differentials in urban labor markets.
  *Int. Economic Review*, 14(3), 693--709.
- Rey, S. J., & Anselin, L. (2007). PySAL: A Python library of spatial
  analytical methods. *Review of Regional Studies*, 37(1), 5--27.
- Theil, H. (1967). *Economics and Information Theory*. North-Holland.
- Wooldridge, J. M. (2010). *Econometric analysis of cross section and panel
  data* (2nd ed.). MIT Press.
