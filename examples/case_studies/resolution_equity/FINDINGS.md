# Resolution Equity in NYC 311 Service Delivery: Findings

*Generated on 2026-04-12 using nyc311 v0.4.0.*

---

## Data Summary

The analysis examines **1,000,000 NYC 311 service requests** covering 2023-05 to 2024-12. The balanced panel contains **76 community districts** observed over **20 monthly periods** (1,520 total observations).

Mean monthly complaints per district: 657.9 (median: 0.0). Mean resolution rate: 21.3% (SD = 0.406).

## Seasonal Decomposition and Anomalies

STL decomposition reveals complaints peak in **December** and trough in **April**, with a seasonal amplitude of **269,484** complaints. The trend moved from -50,504 to 108,271 over the study period.

**STL Anomaly Detection** (threshold: 2.0 sigma)

Detected **1** anomalous observation(s) with |z-score| > 2.0 (residual mean = -0.00, residual std = 0.00).

Anomaly dates: 2024-07-01
Z-scores: +2.47

## Equity Analysis

Two-way fixed effects panel regression with entity and time fixed effects, clustered SE at the district level (N = 328, R-sq = **0.3278**).

  - **log_complaints**: coeff = +4.0083, SE = 0.9733, p < 0.001 (***)

Higher complaint volume significantly predicts longer resolution times. A 1-unit increase in log complaints is associated with +4.0 additional days of median resolution time.

**Theil T Index** (N = 51 units)

Total inequality: T = 0.2247.
Between-group component: 0.1657 (73.7% of total). Within-group component: 0.0590 (26.3% of total).
The majority of inequality is attributable to differences *between* groups rather than within them.

Largest contributors: STATEN ISLAND 01 (+0.1556), STATEN ISLAND 03 (+0.0890), BRONX 12 (+0.0703), STATEN ISLAND 02 (+0.0550), MANHATTAN 12 (+0.0198)

**Oaxaca-Blinder decomposition** (low- vs. high-income districts): total gap = -0.77 days. Explained = -0.62 (-80%), Unexplained = -0.15 (-20%).

## Spatial Analysis

**Global Moran's I**: I = 0.3787 (z = 2.574, p = 0.0070 (**)), indicating positive spatial autocorrelation: similar values tend to cluster together geographically. The result is statistically significant at the 1% level (p = 0.0070 (**)), providing strong evidence to reject the null hypothesis for spatial autocorrelation.

LISA cluster distribution: HH: 3; HL: 9; LL: 7; ns: 40.

## Policy Evaluation

**Changepoint detection** (PELT): 1 break(s) dividing the series into 2 segment(s).
  - 2024-08-01

**Interrupted time series** (intervention: March 2024 rat mandate):
  - Pre-intervention trend: +23.2/period
  - Level change: -425,361 (p < 0.001 (***))
  - Trend change: +34,886 (p < 0.001 (***))
  - Post-intervention trend: +34,909/period

## Reporting Bias

Latent EM converged after 2 iterations. Reporting probabilities: 0.500 -- 0.500 (mean = 0.500).

The near-uniform reporting probabilities suggest the model cannot distinguish reporting heterogeneity with the available covariates. More granular data (per complaint type, with additional covariates) would be needed.

## Limitations

- Demographic covariates are from ACS 2022 PUMA-level estimates mapped to community districts. Some CDs share PUMAs and thus have identical demographic values.
- The reporting bias EM model assumes a Poisson-logistic structure that may not hold for all complaint types.
- Spatial weights use a 3 km distance threshold; results are sensitive to this choice.
- Clustered standard errors with ~70 clusters may under-reject; wild bootstrap inference is recommended for robustness.

## References

- Cleveland et al. (1990). STL decomposition. *J. Official Statistics*.
- Killick et al. (2012). PELT changepoint detection. *JASA*.
- O'Brien et al. (2015). Ecometrics. *Sociological Methodology*.
- Rey & Anselin (2007). PySAL. *Review of Regional Studies*.
- Theil (1967). *Economics and Information Theory*.
- Wooldridge (2010). *Econometric Analysis of Cross Section and Panel Data*.
