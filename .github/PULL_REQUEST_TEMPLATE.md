<!-- nyc311 PR template — short, non-bureaucratic. Delete sections that don't apply. -->

## Summary

<!-- 1–3 bullets. What does this PR do and why? -->

## Issue ref

<!-- Link the GitHub issue, if any. Use "Closes #N" to auto-close. -->

## Bridge touches (v1.0.0 contracts)

<!-- Tick any that apply. If any are ticked, the /factor-compat-auditor agent should return clean. -->

- [ ] `PanelDataset.to_factor_factory_panel` / adapter at
      `src/nyc311/temporal/_factor_factory.py`
- [ ] `Pipeline.as_factor_factory_estimate` / bridge at
      `src/nyc311/factors/_factor_factory.py`
- [ ] `factor-factory` version pin in `pyproject.toml`
- [ ] `jellycell` version pin in the `tearsheets` extra
- [ ] None of the above

## Case-study touches

<!-- Tick any that apply. The precious two case studies have numeric-parity rules. -->

- [ ] `examples/case_studies/rat_containerization/` — prose or numbers
- [ ] `examples/case_studies/resolution_equity/` — prose or numbers
- [ ] `examples/sdid-multi-borough-policy/`
- [ ] `examples/mediation-cascade-resolution/`
- [ ] None of the above

If a **precious** case study's numbers or narrative changed, the PR description
MUST explain why, and the new numbers MUST be scientifically justified.
Otherwise, revert and open a discussion.

## Checklist

- [ ] `make ci` green locally (or equivalent CI)
- [ ] `CHANGELOG.md` entry under `[Unreleased]` (Added / Changed / Fixed /
      Contracts)
- [ ] Touched the factor-factory bridge? → `/factor-compat-auditor` clean
- [ ] New public API? → re-exported from the relevant `__init__.py`; appears in
      `scripts/audit_public_api.py` output
- [ ] New optional-dependency extra? → folded into `all`
- [ ] Docs: if a public surface changed, `docs/sdk.md` / `docs/integration.md`
      updated

## Test plan

<!-- What did you run to convince yourself this works? -->
