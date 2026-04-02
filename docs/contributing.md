# Contributing

Contributions are welcome, especially when they keep the package honest about
what is implemented today and improve the usefulness of the SDK, CLI, or docs.

## Development Setup

The fastest full setup is:

```bash
uv sync --all-groups --all-extras
```

For a leaner edit-test loop without optional extras:

```bash
uv sync
```

You can also use `uvx nox` for session-based development.

## Common Commands

If you use the provided Makefile:

```bash
make install
make install-dev
make test
make test-optional
make test-fetch
make test-integration
make lint
make docs
make audit
make smoke-dist
```

If you prefer direct commands:

```bash
uv run --all-extras pytest -m "not integration"
uv run --all-extras pytest -m optional
uv run --all-extras pytest -m "fetch and not integration"
uv run ruff check .
uv run ruff format --check .
uv run mypy
uvx nox -s lint
uvx nox -s pylint
uvx nox -s tests_integration
uv run mkdocs serve
uv run mkdocs build --strict
uv run python scripts/audit_public_api.py
make smoke-dist
```

## Nox Sessions

```bash
uvx nox -s lint
uvx nox -s tests
uvx nox -s tests_optional
uvx nox -s tests_integration
uvx nox -s docs
uvx nox -s build
```

## Test Organization

- `unit`: fast local tests for day-to-day development
- `fetch`: tests focused on CSV/Socrata loading and fetch-related workflows
- `integration`: heavier or live-service checks
- `network`: tests that reach external services

The default local and CI path now uses the full installed feature set and runs
`pytest -m "not integration"` so pandas-backed and spatial coverage are included
by default. Live fetch checks remain available through the dedicated integration
session instead of running on every commit.

## Pre-commit

Install a local hook if you want checks on commit:

```bash
uv tool install pre-commit
pre-commit install
```

Or run the checks manually:

```bash
pre-commit run --all-files
```

## Documentation

Docs are built with MkDocs Material and live in `docs/`.

The hosted site is [nyc311.readthedocs.io](https://nyc311.readthedocs.io/), and
the source for that site lives in `docs/`.

The repo also includes runnable self-contained consumer projects under
`examples/`, but the canonical narrative docs live in `docs/`.

For local docs work:

```bash
make docs
make docs-build
```

`make docs` runs `mkdocs serve` for local preview, and `make docs-build` runs a
strict build equivalent to the hosted site and CI checks.

`docs/api.md` is generated with `mkdocstrings` from the explicit public
namespaces in `src/nyc311/`. `scripts/audit_public_api.py` verifies that those
namespaces stay explicit, unique, and documented. Prefer updating source
docstrings and exported symbols there rather than hand-editing generated API
content.

## Release Target

The project is now on the stable `0.2` line.

- Use the `0.2` line as the release framing for this branch.
- Use the next semantic version tag that matches the change scope, such as
  `0.2.1`, `0.2.2`, or a future `0.3.0`.
- Prefer patch releases for docs, packaging, workflow, and metadata polish.
- The project version remains VCS-derived through Hatch, so the actual package
  version will come from the eventual git tag rather than a hardcoded file edit.

## Package Publishing

Distribution builds are always enabled in `.github/workflows/cd.yml`, and
package publishing remains gated by the `PYPI_PUBLISH_ENABLED` repository
variable.

By default:

- GitHub releases and manual `CD` runs build, validate, and smoke-test the
  package artifacts.
- The publish job is skipped unless publishing is explicitly enabled.
- Artifact attestations are skipped automatically on private repositories,
  because GitHub does not support them there.

To switch publishing on later:

1. Configure trusted publishing on TestPyPI and PyPI for this repository. The
   current workflow claims use repository `random-walks/nyc311`, workflow
   `.github/workflows/cd.yml`, and environment `pypi`.
2. Ensure the repository variable `PYPI_PUBLISH_ENABLED=true` is set.
3. Use the manual `CD` workflow from the target tag with `publish=true` and
   `repository=testpypi` for a dry run.
4. Publish to real PyPI by either: `a.` creating a GitHub release from the tag
   after enabling the variable, or `b.` running the `CD` workflow manually from
   the target tag with `publish=true` and `repository=pypi`.

The manual dispatch path is useful when you want to keep iterating on the branch
and only publish a selected tag later.

The full public launch checklist, including repo visibility and package-index
setup, lives in `docs/releasing.md`.

## Contribution Expectations

- keep the implemented surface narrow and explicit
- add or update tests for meaningful behavior changes
- update docs when CLI or SDK behavior changes
- keep install guidance aligned with optional dependency boundaries

For reusable NYC boundary assets, canonical layer/value normalization, and other
generic geography helpers, prefer contributing in `nyc-geo-toolkit` first and
then updating `nyc311` only where a 311-specific adapter or compatibility layer
is still needed.

## Release Quality Checks

Before opening a PR, run:

```bash
make ci
make audit
make docs-build
make smoke-dist
```

## More Context

- GitHub contribution notes:
  [random-walks/nyc311/.github/CONTRIBUTING.md](https://github.com/random-walks/nyc311/blob/main/.github/CONTRIBUTING.md)
- Releases: [GitHub Releases](https://github.com/random-walks/nyc311/releases)
