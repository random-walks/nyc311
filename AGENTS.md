# AGENTS.md — nyc311

Canonical agent guide for this repo. Native readers: Cursor, Codex, GitHub
Copilot, Aider, Zed, Warp, Windsurf, Gemini CLI. Claude Code reads
[`CLAUDE.md`](CLAUDE.md), which delegates here and layers on Claude-specific
conventions (slash-commands, skills, agents).

## What this repo is

`nyc311` is the reproducible toolkit for NYC 311 complaint analysis in the
`random-walks` NYC OSS ecosystem. See [`README.md`](README.md) for the
elevator pitch.

Two public surfaces:

- **SDK** — typed dataclasses, `nyc311.factors.Pipeline`,
  `nyc311.temporal.PanelDataset`, seventeen `nyc311.stats` modules. See
  [`docs/sdk.md`](docs/sdk.md).
- **CLI** — `nyc311 fetch`, `nyc311 topics`. See
  [`docs/cli.md`](docs/cli.md).

## Where to start

**For new agents shipping analysis code**: read
[`docs/sdk.md`](docs/sdk.md), then [`docs/integration.md`](docs/integration.md)
for the factor-factory bridges.

**For agents adding a new statistical method**: first consult
[`.claude/skills/stats-module-discipline.md`](.claude/skills/stats-module-discipline.md).
Rule: **factor-factory first**. Homegrown `nyc311.stats` modules only with an
explicit RFC in the PR description.

**For agents touching either factor-factory bridge**
(`PanelDataset.to_factor_factory_panel()` or
`Pipeline.as_factor_factory_estimate()`): read
[`.claude/skills/factor-compat.md`](.claude/skills/factor-compat.md) for the
additive/backwards-compatibility decision table, then run
[`.claude/agents/factor-compat-auditor.md`](.claude/agents/factor-compat-auditor.md)
against your diff.

**For agents cutting a release**: read
[`docs/releasing.md`](docs/releasing.md) and
[`.claude/skills/release-bump.md`](.claude/skills/release-bump.md).

## Hard rules

- **The two factor-factory bridges are additive contracts**. Renaming or
  removing a keyword argument on
  `PanelDataset.to_factor_factory_panel()` or
  `Pipeline.as_factor_factory_estimate()` is a **major** version bump. A
  new keyword argument (with a default) is a minor bump.
- **The two production case studies are research artifacts**. Do NOT modify
  the numbers in `examples/case_studies/rat_containerization/data/analysis_results.json`
  or rewrite the narrative in either `FINDINGS.md`. If a refactor would
  change those, STOP and open a discussion first. Both are cited in
  [`CITATION.cff`](CITATION.cff).
- **Jellycell tearsheets (`manuscripts/*.md`) and engine-result artifacts
  (`artifacts/*.json`) are committed**, so the rendered site is reproducible
  from git without running the pipeline. Don't gitignore them.
- **`ruff check`, `ruff format --check`, `mypy --strict`, `pylint` (errors
  only) all pass on `src/` and `tests/`** before a PR is merge-ready.
- **`mkdocs build --strict` is clean**. No warnings; the docs ship with the
  release.
- **Python ≥ 3.12** (factor-factory upstream floor). Don't try to add back
  3.10 / 3.11 support.
- **`_version.py` is `hatch-vcs`-generated**. Never hand-edit.
- **MIT license**.

## Conventions

- **Imports**: absolute (`from nyc311.temporal import PanelDataset`) in
  library code. `import nyc311 as n311` is fine in notebooks / examples.
- **Types**: `@dataclass(frozen=True, slots=True)` for public data classes;
  pydantic models for runtime-validated contracts (rare — most live in
  factor-factory). Vanilla type hints elsewhere. `mypy --strict` on
  `nyc311.*` — no `type: ignore` without a reason comment.
- **Docstrings**: Google-style (`Args:` / `Returns:` / `Raises:`) for public
  symbols. `mkdocstrings` renders the API reference from these.
- **Tests**: `pytest`, colocated under `tests/` mirroring source layout.
  Mark heavier tests with `@pytest.mark.optional`; network tests with
  `@pytest.mark.integration`.
- **Examples**: self-contained projects under `examples/` with their own
  `pyproject.toml`. Source of truth is
  `pyproject.toml` + `main.py` + `README.md` + per-example `.gitignore`
  (+ `jellycell.toml` + `manuscripts/` + `artifacts/` for jellycell-using
  cases). `uv.lock` and `.venv/` are gitignored repo-wide.
- **CHANGELOG**: `docs/changelog.md` (NOT root `CHANGELOG.md`). Entries
  under `[Unreleased]` roll out on `/bump`.
- **Commits**: Conventional-commit subject lines —
  `feat(temporal): ...`, `fix(stats): ...`, `docs: ...`, `ci: ...`,
  `chore(release): ...`.

## Case-study layout

- `examples/case_studies/rat_containerization/` — real Socrata data,
  cited.
- `examples/case_studies/resolution_equity/` — real Socrata data,
  cited.
- `examples/sdid-multi-borough-policy/` — synthetic, offline, SDID
  showcase.
- `examples/mediation-cascade-resolution/` — synthetic, offline, four-way
  mediation showcase.
- `examples/factor-factory-quickstart/` — no-jellycell minimal adapter
  showcase.

## The rest

- [`docs/architecture.md`](docs/architecture.md) — module responsibilities
  + the mermaid pipeline diagram (includes the two factor-factory bridges).
- [`docs/migration-v0-to-v1.md`](docs/migration-v0-to-v1.md) — consumer
  upgrade path from v0.3 to v1.0.
- [`.claude/`](.claude/) — Claude-Code-specific agents, commands, skills,
  settings.
