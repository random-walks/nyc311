# factor-factory quickstart — no jellycell

The minimal showcase for the v1.0.0 adapter:
`PanelDataset → factor_factory.tidy.Panel → engine → pandas`.

**No jellycell.** No tearsheet rendering, no `manuscripts/` directory, no
`jellycell.toml`. If you want the causal-inference engine adapter but not
the reporting machinery, start here.

## What this exercises

- Build an nyc311 `PanelDataset` with a `TreatmentEvent`.
- Convert via `PanelDataset.to_factor_factory_panel()`.
- Fit `factor_factory.engines.did.estimate(panel, methods=("twfe",))`.
- Print the ATT / SE / 95% CI / p-value as a pandas row.

Total: ~50 lines in `main.py`.

## Running

```bash
pip install "nyc311>=1.0,<2" "factor-factory[did]>=1.0.2,<2"
cd examples/factor-factory-quickstart
python main.py
```

Expected output:

```
-- built 6 units x 24 periods PanelDataset --
-- adapted to factor_factory.tidy.Panel --
   outcome_col=complaint_count, dimension=community_district
-- fitting DiD (TWFE) --
   method         att       se  ci_95_lower  ci_95_upper  p_value  n
0    twfe -4.98...  0.18...    -5.34...    -4.62...    < 0.001  144
```

The synthetic panel bakes in a true ATT of `-5` on the single treated unit
(`MANHATTAN 03`, treated from period 13). TWFE recovers within noise.

## Next steps

- Swap `methods=("twfe",)` for `("cs",)` (Callaway-Sant'Anna),
  `("sa",)` (Sun-Abraham), or `("bjs",)` (Borusyak-Jaravel-Spiess) —
  all DiD variants ship in `factor_factory.engines.did`.
- Swap the engine family: `factor_factory.engines.{sdid, scm, rdd,
  mediation, panel_reg, inequality, spatial, changepoint, stl,
  reporting_bias, hawkes, event_study, survival, het_te, dml, ...}`
  all accept the same `Panel`.
- Use `Pipeline.as_factor_factory_estimate(panel, family=..., method=...)`
  if you want the dispatch to flow out of a `nyc311.factors.Pipeline`.
- For a publication-ready tearsheet bundle alongside the engine fit, see
  `examples/sdid-multi-borough-policy/` and
  `examples/mediation-cascade-resolution/` — same adapter, with
  `nyc311[tearsheets]` + jellycell manuscripts.
