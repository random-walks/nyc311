# Resolution-cascade mediation — four-way decomposition case study

A self-contained showcase for
[`factor_factory.engines.mediation.four_way`](https://github.com/random-walks/factor-factory)
as wired through nyc311's adapter. Uses synthetic data so it runs
offline in seconds.

## Scenario

A (fictional) 311 operational pilot rolls out to half the community
districts. The pilot is believed to improve complaint
*resolution rates* via a specific causal pathway: the pilot
streamlines intake, which reduces *triage time*, which in turn
raises the share of complaints that get resolved. Triage time is
the **mediator** in this cascade:

```
pilot (treatment) ─► triage_time_days (mediator) ─► resolution_rate (outcome)
                   ╲                                                   ╱
                    ╲─────── direct effect of pilot on resolution ────╱
```

The four-way decomposition (VanderWeele 2014, *Epidemiology*) splits
the total effect into:

- **Controlled Direct Effect (CDE)** — treatment's impact on outcome
  with the mediator held fixed.
- **Reference Interaction (INTref)** — effect from the
  treatment-mediator interaction at the reference mediator level.
- **Mediated Interaction (INTmed)** — effect from the
  treatment-mediator interaction mediated by treatment-induced
  mediator change.
- **Pure Indirect Effect (PIE)** — effect mediated entirely by
  treatment-induced mediator change, no interaction.

The question: is the pilot's measured impact on resolution primarily
*direct* (operational changes beyond triage time), or does it
operate *through* the triage-time mediator?

## Running

```bash
cd examples/mediation-cascade-resolution
uv run python run_analysis.py
```

Outputs:

- `data/panel.parquet` — the synthetic mediated panel (pandas parquet).
- `artifacts/mediation_results.json` — four-way decomposition dict,
  factor-factory schema.
- `manuscripts/FINDINGS.md`, `METHODOLOGY.md`, `DIAGNOSTICS_CHECKLIST.md`,
  `MANUSCRIPT.md`, `AUDIT.md` — jellycell tearsheets.

## What's exercised

- `nyc311.temporal.PanelDataset` with a custom per-observation
  covariate (the mediator).
- `PanelDataset.to_factor_factory_panel()` adapter, using the
  mediator column.
- `factor_factory.engines.mediation.four_way` — the headline.
- `factor_factory.jellycell.tearsheets.*` renderers.
