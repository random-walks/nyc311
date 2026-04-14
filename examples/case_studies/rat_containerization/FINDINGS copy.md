# Rat Containerization Policy Evaluation: Findings

*Generated on 2026-04-12 using nyc311 v0.4.0.*
 
---

## Data

Real NYC 311 Rodent complaint data fetched from NYC Open Data (Socrata dataset erm2-nwe9). Balanced panel: 70 community districts x 24 monthly periods (1680 observations total). Treatment: rat containerization mandate pilot applied to 9 Manhattan districts beginning 2024-06-01.

## Descriptive Profile

81,467 rodent complaints analyzed (79,243 resolved, 97.3% resolution rate).

Factor pipeline (mean across all district-month cells): complaint volume = 48.5, response rate = 0.838, topic concentration (HHI) = 0.8833, recurrence rate = 0.131.

## Temporal Patterns

STL decomposition reveals peak rodent complaints in Aug and a trough in Dec (seasonal amplitude: 2,464).

1 anomalous month(s) detected: 2023-08-01.

No structural breaks detected.

## Synthetic Control

**Synthetic Control Method** (treated unit: MANHATTAN 03)

The treatment is associated with a reduction of 2.6 complaints.
The synthetic control is constructed from 6 donor unit(s), with BRONX 01 contributing the largest weight (39.4%).
Pre-treatment fit: MSPE = 24.3830. The relatively high MSPE suggests the synthetic match may be imperfect; interpret the ATT with caution.

Average Treatment Effect on the Treated (ATT): **-2.60** complaints per period.

## Staggered Difference-in-Differences

**Staggered Difference-in-Differences** (Callaway & Sant'Anna 2021)

Estimated 1 treatment cohort(s) across 24 time periods, yielding 24 group-time ATT estimates aggregated via inverse-variance weighting.

The aggregated ATT is +6.79 (95% CI: [+1.55, +12.04]).

The result is statistically significant at the 5% level (p = 0.0112 (*)), providing strong evidence to reject the null hypothesis for the average treatment effect.

## Event Study

**Event Study** (reference period: t = -1)

Estimated 6 pre-treatment and 6 post-treatment relative-period coefficients.

**Pre-trend test**: The joint F-test of pre-treatment coefficients fails to reject the null hypothesis of parallel pre-trends (F = 0.480, p = 0.780). This supports the identifying assumption of the difference-in-differences design.

Post-treatment coefficients are predominantly positive, ranging from -2.09 to +10.06.

## Regression Discontinuity

**Regression Discontinuity Design** (kernel: triangular)

The RD treatment effect is -91.20 (95% CI: [-1273.82, +1091.42]).

Bandwidth: [1121.460, 1121.460]; effective sample: 20 obs. (left) and 26 obs. (right).

The test fails to reject the null hypothesis at alpha = 0.05 (p = 0.880), suggesting insufficient evidence for the discontinuity.

## Power Analysis

**Power Analysis** (MDE Calculator)

Design: 70 units, 24 periods, ICC = 0.05, alpha = 0.05, power = 80%.

**Minimum Detectable Effect: 17.21** (in outcome units).

Any true treatment effect smaller than 17.21 would have less than 80% probability of being detected as statistically significant at alpha = 0.05 with this design. Increasing the number of units or periods would lower the MDE.

## Synthesis

### Summary of Evidence

- **Synthetic control**: ATT = -2.6 complaints/month
- **Staggered DiD**: ATT = +6.8 (p = 0.011)
- **RDD**: effect = -91.2 (p = 0.880)
- **MDE**: 17.2 (80% power at alpha = 0.05)

## Limitations

- Treatment assignment is based on reported pilot rollout dates; exact enforcement timing may vary by district.
- The RDD running variable uses haversine distance from the treated-zone centroid, not the precise mandate boundary polygon.
- Rodent complaints reflect reporting behavior, not underlying rodent populations; reporting propensity may shift with policy awareness.
- The panel uses monthly frequency, which may smooth out short-term policy dynamics.
