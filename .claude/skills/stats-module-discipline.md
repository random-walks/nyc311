---
name: stats-module-discipline
description: Triggers on any addition to src/nyc311/stats/. Reminds you of the "factor-factory first" rule before introducing a new statistical method in this repo.
---

# Stats module discipline

nyc311 ships seventeen statistical modules under `src/nyc311/stats/`.
As of v1.0.0, the rule is:

> **New statistical methods go through factor-factory first.**
> Homegrown modules only with an explicit RFC.

## Decision table

| Scenario                                                    | Action                                                                                    |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Wrapping a method factor-factory already covers             | DON'T add a homegrown module. Use `PanelDataset.to_factor_factory_panel()` and the engine |
| Tweaking an existing homegrown module (bug fix, doc improvement) | Fine. Keep the `.. note::` cross-reference to the factor-factory equivalent accurate      |
| Introducing a new homegrown method factor-factory lacks     | RFC in the PR description: *why is this not a factor-factory engine PR instead?*          |
| Adding a utility helper used only within nyc311             | Fine, but place it outside `src/nyc311/stats/` so it doesn't read like a statistical method |

## Acceptable homegrown modules in v1.0.0 (no ff equivalent)

- `_bym2` (Bayesian small-area smoothing — PyMC-native)
- `_gwr` (geographically-weighted regression)
- `_equity.oaxaca_blinder` (the non-Theil half of equity)
- `_power` (power analysis helper)
- `_spatial_regression` (spatial lag / error)

Everything else should cross-reference factor-factory in its module
docstring.

## Ceremony for adding a homegrown method

1. Check `docs/integration.md`'s crosswalk — is the method actually
   uncovered?
2. If it IS covered by factor-factory, don't ship it here. Contribute
   to factor-factory instead.
3. If it IS NOT covered, the PR description must include:
   - The canonical paper citation.
   - A one-paragraph RFC: why it goes here rather than being a
     factor-factory engine PR.
   - A mention in `docs/integration.md`'s "uncovered methods" list.
4. Add the module under `src/nyc311/stats/_<name>.py` with a
   referenced-first docstring.

## Golden rule

> If factor-factory has an engine for it, the answer is `PanelDataset.to_factor_factory_panel()`, not a new nyc311 stats module.
