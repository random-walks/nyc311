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

This branch is now on the `0.2` alpha prerelease line.

- Use the `0.2` alpha series as the release framing for this branch.
- Follow normal prerelease progression within that line: `0.2.0a2`, `0.2.0a3`,
  and so on.
- The project version remains VCS-derived through Hatch, so the actual package
  version will come from the eventual git tag rather than a hardcoded file edit.

## Package Publishing

Distribution builds are always enabled in `.github/workflows/cd.yml`, but
package publishing is intentionally opt-in.

By default:

- GitHub releases and manual `CD` runs build and inspect the package artifacts.
- The publish job is skipped unless publishing is explicitly enabled.
- Artifact attestations are skipped automatically on private repositories,
  because GitHub does not support them there.

To switch publishing on later:

1. Configure trusted publishing on TestPyPI or PyPI for this repository. The
   current workflow claims use repository `random-walks/nyc311`, workflow
   `.github/workflows/cd.yml`, and environment `pypi`.
2. Set the repository variable `PYPI_PUBLISH_ENABLED=true`.
3. Keep `repository-url: https://test.pypi.org/legacy/` in
   `.github/workflows/cd.yml` while validating against TestPyPI.
4. When you are ready for real PyPI, remove the `repository-url` override so
   `pypa/gh-action-pypi-publish` targets PyPI.
5. Publish by either: `a.` creating a GitHub release from a tag after enabling
   the variable, or `b.` running the `CD` workflow manually from the target tag
   with `publish=true`.

The manual dispatch path is useful when you want to keep iterating on the branch
and only publish a selected tag later.

## Contribution Expectations

- keep the implemented surface narrow and explicit
- add or update tests for meaningful behavior changes
- update docs when CLI or SDK behavior changes
- keep install guidance aligned with optional dependency boundaries

## Release Quality Checks

Before opening a PR, run:

```bash
make ci
make audit
make docs-build
```

## More Context

- GitHub contribution notes:
  [random-walks/nyc311/.github/CONTRIBUTING.md](https://github.com/random-walks/nyc311/blob/main/.github/CONTRIBUTING.md)
- Releases: [GitHub Releases](https://github.com/random-walks/nyc311/releases)
