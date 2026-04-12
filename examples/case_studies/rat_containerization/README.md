# Rat Containerization Policy Evaluation

Applies the full `nyc311` causal inference toolkit to evaluate the
2024 NYC rat containerization mandate using **real rodent complaint
data** from NYC Open Data (Socrata dataset `erm2-nwe9`).

## Policy Background

New York City's containerization mandate required businesses and
residences to set out trash in sealed containers rather than loose
bags.  The pilot program launched in lower Manhattan community
districts in June 2024, with citywide enforcement beginning
November 12, 2024.

## Data

- **Source**: 81,467 real Rodent-type 311 complaints (Jan 2023 -- Dec 2024)
- **Panel**: 70 community districts x 24 monthly periods = 1,680 observations
- **Treatment**: 9 Manhattan districts (CDs 01--09) treated beginning June 2024
- **Control**: 61 remaining community districts across all five boroughs
- **Demographics**: ACS 2022 5-year estimates (population, race, income, tenure)
  from the Census Bureau, shipped in `data/demographics.csv`

## Key Findings

### Brooklyn dominates rodent complaints; Manhattan has the worst hotspots

The factor pipeline across 1,680 district-month cells reveals Brooklyn
accounts for **37.9%** of all rodent complaints (30,861), followed by
Manhattan (26.3%) and Queens (17.8%).  The overall resolution rate is
high at **97.3%**, with "Rat Sighting" (62%) and "Condition Attracting
Rodents" (18%) the dominant descriptors.  Topic concentration is very
high (HHI = 0.88), meaning most complaints fall into just a few
categories.  Recurrence rate is 13.1% --- roughly 1 in 8 complaints
comes from a location that has filed before.

The worst-hit districts are **Manhattan 11** (East Harlem, 188
complaints/month), **Brooklyn 03** (Bedford-Stuyvesant, 151/month),
and **Brooklyn 01** (Williamsburg, 150/month).

### Rodent complaints peak in August and show no structural break

STL decomposition reveals a strong seasonal cycle peaking in **August**
and troughing in **December**, with a seasonal amplitude of 2,464
complaints.  One anomalous month was detected: **August 2023**
(z = +2.21), an unusually large summer spike.  PELT changepoint
detection found **no structural breaks** in the 24-month series ---
the containerization mandate did not produce a visible shift in the
aggregate city-wide trend.

Per-borough trends show modest declines everywhere (Manhattan -9.0%,
Brooklyn -3.8%, Bronx -3.7%, Staten Island -3.9%, Queens -0.3%),
consistent with a city-wide downward drift rather than a
treatment-specific effect.

### Rodent complaint inequality is driven by within-borough variation

The Theil T inequality index is **T = 0.165**, with **67.6%**
attributable to within-borough differences and 32.4% between boroughs.
Unlike resolution equity (where between-borough differences dominate),
the rodent burden varies dramatically *within* boroughs: Manhattan 11
has 5x the city median while Manhattan 01 has near zero.

Moran's I is 0.19 (p = 0.064), marginally insignificant --- rodent
complaints show weak spatial clustering.  LISA identifies 2 HH
hotspots (Brooklyn 04, Queens 05) and 11 LL coldspots.

### The causal evidence on containerization is mixed

**Synthetic control** (Manhattan 03 vs. counterfactual): ATT = **-2.6
complaints/month**, suggesting a modest reduction.  However,
pre-treatment MSPE = 24.4 indicates an imperfect donor match (Bronx 01
at 39%, Staten Island 02 at 20%).

**Staggered DiD** (9 treated Manhattan CDs vs. control): ATT = **+6.8
complaints/month** (p = 0.011, 95% CI [+1.6, +12.0]).  Contrary to
expectations, treated districts saw a *rise* relative to controls.
The pre-trend F-test (F = 0.48, p = 0.78) strongly supports parallel
trends, so the increase appears real.  This likely reflects a
**reporting-awareness surge** from media coverage rather than more rats.

**Event study**: Post-treatment coefficients range from -2.1 to +10.1,
largest immediately post-mandate, consistent with a surge that
attenuates over time.

**RDD** (haversine distance from treated-zone centroid): estimate =
-91.2, p = 0.88 --- no significant discontinuity at the spatial
boundary.

### Power analysis confirms detection limits

The MDE is **17.2 complaints** at 80% power.  The SCM ATT (-2.6) and
DiD ATT (+6.8) both fall below this threshold.  A definitive evaluation
would require longer post-treatment data, rodent activity measures
beyond 311 complaints (e.g., DOH inspections), and explicit modeling
of the reporting-awareness channel.

## Methods

| Script | Method | Citation |
|--------|--------|----------|
| `03_descriptive_and_factors.py` | Factor pipeline (volume, response, HHI, recurrence) | -- |
| `04_temporal_analysis.py` | STL decomposition, anomaly detection, PELT changepoints | Cleveland et al. (1990); Killick et al. (2012) |
| `05_spatial_analysis.py` | Moran's I, LISA, Theil T index, equity gap factor | Rey & Anselin (2007); Theil (1967) |
| `06_synthetic_control.py` | Synthetic control (Abadie SCM) | Abadie, Diamond, & Hainmueller (2010) |
| `07_staggered_did.py` | Staggered DiD + event study | Callaway & Sant'Anna (2021) |
| `08_spatial_discontinuity.py` | Sharp RDD (real lat/lon + boundaries) | Calonico, Cattaneo, & Titiunik (2014) |
| `09_power_analysis.py` | Cluster-RCT MDE calculator | Standard panel-design power formula |

## Quick Start

```bash
pip install "nyc311[stats,spatial,dataframes]"
cd examples/case_studies/rat_containerization
python run_analysis.py
```

The first run fetches ~2 years of Rodent complaints from Socrata
(requires internet).  Subsequent runs use the cached data.

## Scripts

| File | Purpose |
|------|---------|
| `01_fetch_data.py` | Fetch Rodent complaints from Socrata (2023--2024) |
| `02_build_panel.py` | Build balanced panel with real treatment events |
| `03_descriptive_and_factors.py` | Borough profile, descriptor breakdown, factor pipeline |
| `04_temporal_analysis.py` | STL decomposition, anomaly detection, changepoints, borough trends |
| `05_spatial_analysis.py` | Moran's I, LISA clusters, Theil inequality, equity gap |
| `06_synthetic_control.py` | Abadie synthetic control for MANHATTAN 03 |
| `07_staggered_did.py` | Callaway-Sant'Anna DiD + event-study pre-trend test |
| `08_spatial_discontinuity.py` | RDD using real lat/lon and `nyc_geo_toolkit` boundaries |
| `09_power_analysis.py` | MDE calculation for the panel design |
| `10_generate_findings.py` | Compile FINDINGS.md and JSON output |
| `run_analysis.py` | Orchestrator that runs all steps in sequence |
| `main.py` | Entry point (calls `run_analysis.main()`) |

Each step can be run independently or via the orchestrator.

## Output

- `FINDINGS.md` -- auto-generated analysis report with diagnostic interpretations
- `data/analysis_results.json` -- machine-readable results

## References

- Abadie, A., Diamond, A., & Hainmueller, J. (2010). Synthetic control
  methods for comparative case studies. *JASA*, 105(490), 493--505.
- Callaway, B., & Sant'Anna, P. H. C. (2021). Difference-in-differences
  with multiple time periods. *J. Econometrics*, 225(2), 200--230.
- Calonico, S., Cattaneo, M. D., & Titiunik, R. (2014). Robust
  nonparametric confidence intervals for regression-discontinuity
  designs. *Econometrica*, 82(6), 2295--2326.
- Cleveland, R. B., Cleveland, W. S., McRae, J. E., & Terpenning, I. J.
  (1990). STL: A seasonal-trend decomposition procedure based on loess.
  *J. Official Statistics*, 6(1), 3--33.
- Killick, R., Fearnhead, P., & Eckley, I. A. (2012). Optimal detection
  of changepoints with a linear computational cost. *JASA*, 107(500),
  1590--1598.
- Rey, S. J., & Anselin, L. (2007). PySAL: A Python library of spatial
  analytical methods. *Review of Regional Studies*, 37(1), 5--27.
- Theil, H. (1967). *Economics and Information Theory*. North-Holland.
