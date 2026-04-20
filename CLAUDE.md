# CLAUDE.md

Claude-Code-specific conventions for this repo. **The canonical wider guide is
[`AGENTS.md`](AGENTS.md)** (cross-agent-vendor spec format read by Cursor /
Codex / Copilot / Aider / Zed / Windsurf / Gemini CLI). This file layers on the
bits specific to Claude Code — slash-commands, skills, and agents.

See also [`CONTRIBUTING.md`](CONTRIBUTING.md) for the expanded walkthrough and
[`docs/`](docs/) for the full SDK documentation.

## What nyc311 is

A reproducible toolkit for NYC 311 complaint analysis. Two public surfaces:

- **`nyc311` SDK** — typed dataclasses, a factor pipeline
  (`nyc311.factors.Pipeline`), a temporal panel abstraction
  (`nyc311.temporal.PanelDataset`), and 17 statistical modules under
  `nyc311.stats`. See [`docs/sdk.md`](docs/sdk.md).
- **`nyc311` CLI** — `nyc311 fetch`, `nyc311 topics`. See
  [`docs/cli.md`](docs/cli.md).

## Ecosystem position (v1.0.0)

nyc311 sits **downstream** of two libraries and is adopted by **one**:

- Depends on [nyc-geo-toolkit](https://github.com/random-walks/nyc-geo-toolkit)
  for geographic primitives (haversine, boundary collections).
- Depends on [factor-factory](https://github.com/random-walks/factor-factory)
  for causal-inference engines. Adapters are additive:
  `PanelDataset.to_factor_factory_panel()` and
  `Pipeline.as_factor_factory_estimate()` route nyc311 panels into
  factor-factory engines without changing nyc311's own shapes. See
  [`docs/integration.md`](docs/integration.md).
- Optionally depends on [jellycell](https://github.com/random-walks/jellycell)
  via the `tearsheets` extra — the two production case studies and the two new
  ones emit jellycell manuscripts.

## The two load-bearing bridges

Both additive, both backwards-compatible by design:

1. `PanelDataset ↔ factor_factory.tidy.Panel` — adapter at
   [`src/nyc311/temporal/_factor_factory.py`](src/nyc311/temporal/_factor_factory.py).
2. `Pipeline ↔ factor_factory.engines.*.estimate` — bridge at
   [`src/nyc311/factors/_factor_factory.py`](src/nyc311/factors/_factor_factory.py).

Touch either of these and `.claude/skills/factor-compat.md` ceremony applies.
Run the [`factor-compat-auditor`](.claude/agents/factor-compat-auditor.md) agent
before the PR is review-ready.

## Case studies are research artifacts

- [`examples/case_studies/rat_containerization/`](examples/case_studies/rat_containerization/)
- [`examples/case_studies/resolution_equity/`](examples/case_studies/resolution_equity/)

Both produce a formal write-up at `FINDINGS.md` and are cited in `CITATION.cff`.
**Do not overwrite their numbers or rewrite their narrative text** without
explicit user sign-off. If a refactor would change a field in
`data/analysis_results.json`, STOP and ask.

Two more case studies shipped with v1.0.0 as showcases for factor-factory
engines nyc311 didn't have homegrown:

- [`examples/sdid-multi-borough-policy/`](examples/sdid-multi-borough-policy/) —
  `engines.sdid`
- [`examples/mediation-cascade-resolution/`](examples/mediation-cascade-resolution/)
  — `engines.mediation.four_way`

## Dev commands

```
make install         # uv sync --all-groups --all-extras
make test            # uv run --all-extras pytest -m "not integration"
make lint            # ruff + mypy + pylint + public-API audit
make lint-fix        # apply safe autofixes then re-lint
make docs            # mkdocs serve (live preview)
make docs-build      # mkdocs build --strict
make ci              # full local CI-equivalent (lint + build + smoke + docs + tests)
```

## Claude slash-commands (`.claude/commands/`)

- `/bump [patch|minor|major]` — roll `docs/changelog.md` (never touches
  `_version.py` — that's `hatch-vcs`).
- `/release-check` — invoke the
  [`release-auditor`](.claude/agents/release-auditor.md) agent.
- `/run-case-study <slug>` — regenerate one case study's artifacts and
  tearsheets; numeric-parity-checks for the precious two.

## Skills (`.claude/skills/`) — loaded as reminders

- `factor-compat` — ceremony when touching the adapter/bridge.
- `stats-module-discipline` — "factor-factory first" rule for new statistical
  methods.
- `release-bump` — patch/minor/major rubric.

## Agents (`.claude/agents/`)

- `release-auditor` — preflight for `v*` tags.
- `factor-compat-auditor` — diff-audits the factor-factory bridge for drift.

## Versioning policy

SemVer. Patch is the default; breaking changes (renames, removals, dropping a
Python minor, bumping factor-factory major) are major. See
[`.claude/skills/release-bump.md`](.claude/skills/release-bump.md).

Release path: tag `vX.Y.Z` → the `release: published` event fires
`.github/workflows/cd.yml` → build + OIDC publish to PyPI.

## Contracts

- **`PanelDataset.to_factor_factory_panel()`** — stable additive signature.
  Keyword-only args: `outcome_col`, `provenance`, `spatial_weights`. Return:
  `factor_factory.tidy.Panel`.
- **`Pipeline.as_factor_factory_estimate()`** — stable additive signature.
  Keyword-only args: `family`, `method`, `outcome`, `**engine_kwargs`. Return:
  factor-factory `<Family>Results`.
- **Public API audit**: `scripts/audit_public_api.py` is run by CI and exits
  non-zero if a `nyc311.*` public name changes without a corresponding audit
  markdown update.

## Out of scope for this repo

- Migrating docs from MkDocs to Sphinx (MkDocs is working; low ROI).
- Removing `nyc311.factors.Pipeline` or `nyc311.temporal.PanelDataset` — the
  factor-factory adapters are additive.
- Rewriting the case-study research narratives — those are precious.
