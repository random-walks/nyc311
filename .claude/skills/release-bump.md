---
name: release-bump
description:
  Decision rubric for whether the next release is patch/minor/major. Consulted
  by `/bump`.
---

# Release bump rubric

nyc311 follows [SemVer](https://semver.org). We bump small and often (target 1–2
releases per month during steady-state).

## Decision table

| Change shape                                                           | Bump  |
| ---------------------------------------------------------------------- | ----- |
| Doc-only change, CI/workflow pin, dev-tooling                          | patch |
| Fix that makes existing code work as documented                        | patch |
| New public API added (a class, a function, a CLI subcommand, an extra) | minor |
| New adapter/engine-bridge method added                                 | minor |
| Dropping a Python minor version (e.g. 3.10 → 3.12)                     | major |
| Renaming or removing a public name (class, function, kwarg, CLI flag)  | major |
| Changing the default of a public kwarg in a behavior-affecting way     | major |
| Breaking the `PanelDataset` or `Pipeline` public shape                 | major |
| Bumping factor-factory's minimum major version                         | major |
| Changing the default `Provenance.data_source` citation on the adapter  | major |

## Minimum-bump policy

When in doubt, **take the stronger bump**. Users downstream pin
`nyc311>=X,<X+1`; the tighter the range, the less a hidden breaking change can
do.

## Major-bump narrative requirement

A major bump MUST include a `### Changed` subsection in its CHANGELOG entry that
leads with the breaking change(s) in plain English ("dropped Python 3.10/3.11
support"; "renamed `PanelDataset.geography` to `PanelDataset.unit_type`").
Downstream consumers read the `### Changed` block before anything else.

A major bump SHOULD include a `docs/migration-v<N>-to-v<M>.md` page with
before/after code snippets for the most common consumer patterns.

## Anti-patterns to avoid

- **Bundling a breaking change inside a "minor" release.** Don't.
- **Shipping multiple breaking changes in unrelated subsystems in one major
  release.** Each breaking change is already a tax; piling them up compounds the
  cost.
- **Rewriting the case-study narratives as part of a release.** The two precious
  case studies are research artifacts; their prose text is not release-scoped.

## Golden rule

> Patch is the default. Only go higher when the change table says you must.
