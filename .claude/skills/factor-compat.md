---
name: factor-compat
description:
  Triggers on any edit to nyc311's factor-factory bridge
  (src/nyc311/temporal/_factor_factory.py,
  src/nyc311/factors/_factor_factory.py, or
  Pipeline.as_factor_factory_estimate). Reminds you of the ceremony for that
  bridge before pushing.
---

# Factor-factory bridge ceremony

You just touched one of the two load-bearing bridges from nyc311 to
factor-factory. Those bridges are **additive** and **backwards-compatible** by
design — nyc311 consumers rely on the public shapes staying stable.

## Decision table

| Change shape                                        | Bump  | Required ceremony                                                                                                   |
| --------------------------------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------- |
| Add a new keyword argument (default-valued)         | minor | Update adapter test, update `docs/integration.md`                                                                   |
| Add a new supported engine family                   | minor | Append to `_SUPPORTED_FAMILIES`, add a test, update integration doc                                                 |
| Rename / remove an existing keyword argument        | major | RFC discussion before merge. Update `docs/migration-v0-to-v1.md` (or a v2 migration doc) with before/after snippets |
| Change the default `Provenance` data_source/license | major | Update `CITATION.cff` and `docs/integration.md` together                                                            |
| Bump factor-factory minimum major version           | major | Run full adapter test + engine parity suite. Flag engine-family removals                                            |
| Internal refactor with no surface change            | patch | Adapter test still passes; no doc changes required                                                                  |

## Ceremony steps

1. Run the parity suite before pushing:
   `uv run pytest tests/test_factor_factory_adapter.py tests/test_factor_factory_engines.py -v`.
2. If you added a family to `_SUPPORTED_FAMILIES`, smoke-check it imports under
   the pinned factor-factory version:
   `uv run python -c "from factor_factory.engines.<new_family> import estimate"`.
3. Invoke `/factor-compat-auditor` before the PR is review-ready.
4. Update `docs/integration.md` if the adapter/bridge surface changed,
   `docs/migration-v0-to-v1.md` if old-API consumers need a migration hint.

## Golden rule

> The adapter is additive. If you're about to rename or remove a kwarg, that's a
> major-version change and probably not what the PR is trying to do.
