# Contributing to nyc311

Thanks for your interest. This is a small, opinionated toolkit with tight
contracts around a few public surfaces. The quickest path to a merge is to know
what those surfaces are and what ceremony they need.

For agent-style usage (Claude Code, Cursor, etc.), also read
[`CLAUDE.md`](CLAUDE.md).

## Getting set up

```bash
git clone https://github.com/random-walks/nyc311.git
cd nyc311
make install            # uv sync --all-groups --all-extras
make test               # non-integration pytest, ~15 s on warm cache
make lint               # ruff + mypy strict + pylint + public API audit
make docs               # mkdocs live preview at :8000
```

Editor setup: `ruff` and `mypy --strict` via your IDE's LSP. No other config
needed. Python 3.12 or 3.13.

## The two bridges (what changed in v1.0.0)

nyc311 v1.0.0 wires `PanelDataset` and `Pipeline` through to factor-factory's
causal-inference engines. Two **additive**, backwards-compatible bridges were
added:

1. **`PanelDataset.to_factor_factory_panel()`** — adapter to
   `factor_factory.tidy.Panel`.
2. **`Pipeline.as_factor_factory_estimate()`** — dispatcher to
   `factor_factory.engines.*.estimate`.

Both live in small sibling files:
[`src/nyc311/temporal/_factor_factory.py`](src/nyc311/temporal/_factor_factory.py)
and
[`src/nyc311/factors/_factor_factory.py`](src/nyc311/factors/_factor_factory.py).

Touching either is high-consequence. See
[`.claude/skills/factor-compat.md`](.claude/skills/factor-compat.md) for the
decision table, and run
[`.claude/agents/factor-compat-auditor.md`](.claude/agents/factor-compat-auditor.md)
against your diff before the PR is review-ready.

## The stats discipline

nyc311 ships seventeen statistical modules under
[`src/nyc311/stats/`](src/nyc311/stats/). Eleven of them now have factor-factory
equivalents (see [`docs/integration.md`](docs/integration.md) for the
crosswalk); their docstrings cross-reference the upstream engine with a
`.. note::` block. The remaining six are uncovered upstream and remain
authoritative here.

Rule: **new statistical methods go through factor-factory first**. Homegrown
only with an explicit RFC in the PR description. See
[`.claude/skills/stats-module-discipline.md`](.claude/skills/stats-module-discipline.md).

## The case studies are research

Two case studies are production research artifacts, cited in `CITATION.cff`:

- [`examples/case_studies/rat_containerization/`](examples/case_studies/rat_containerization/)
- [`examples/case_studies/resolution_equity/`](examples/case_studies/resolution_equity/)

If your PR would change a number in either study's `data/analysis_results.json`
or modify the research narrative in `FINDINGS.md`, STOP and open a discussion
first. Their numbers are the published result.

Two further case studies — `sdid-multi-borough-policy/` and
`mediation-cascade-resolution/` — are showcases for factor-factory engines that
nyc311 didn't have homegrown coverage for. Those have no "precious" prose;
modify freely.

## Pre-merge checklist

Paste into your PR description:

```
- [ ] `make ci` green locally (or equivalent CI)
- [ ] `CHANGELOG.md` entry under `[Unreleased]` (Added / Changed / Fixed / Contracts)
- [ ] New public API? → exported from the relevant `__init__.py`, appears in `scripts/audit_public_api.py` output
- [ ] Touched the factor-factory bridge? → `/factor-compat-auditor` clean
- [ ] Touched a case study? → numbers match or CASESTUDY.md narrative unchanged
- [ ] New optional-dependency extra? → folded into `all`
- [ ] Docs: if a public surface changed, `docs/sdk.md` or `docs/integration.md` updated
```

## Coding conventions

- `ruff` config is source of truth — see [`pyproject.toml`](pyproject.toml).
- `mypy --strict` is the floor for `nyc311.*`.
- `@dataclass(frozen=True, slots=True)` for public data classes.
- Docstring style: summary line, blank line, `Args` / `Returns` / `Raises`
  blocks when non-obvious. See any file in `nyc311.stats` for the house style.
- Tests live under [`tests/`](tests/). Mark heavier/optional tests with
  `@pytest.mark.optional`. Use `@pytest.mark.integration` for anything that hits
  the network.

## Commits + PRs

- Conventional-commit subject lines: `feat(temporal): ...`, `fix(stats): ...`,
  `docs: ...`, `ci: ...`.
- One logical change per PR. Large refactors may bundle related files, but avoid
  unrelated subsystem touches.
- Link the factor-factory / jellycell / nyc-geo-toolkit version you're testing
  against in the PR description.

## Discussion

Issues and PRs on [GitHub](https://github.com/random-walks/nyc311/issues). No
Slack, no Discord. Keep conversation async and searchable.
