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
uv run pytest -m "not integration and not optional"
uv run --extra dataframes pytest -m optional
uv run pytest -m "fetch and not integration"
uv run ruff check .
uv run ruff format --check .
uv run mypy
uvx nox -s lint
uvx nox -s pylint
uvx nox -s tests_integration
uv run mkdocs serve
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

The default local and CI path stays fast. Live fetch checks are available
through the dedicated integration session instead of running on every commit.
Optional pandas-backed checks live in `make test-optional` and
`uvx nox -s tests_optional`.

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

The archived context in `docs/og-context/` is intentionally preserved as
historical reference. New user-facing documentation should be added to the root
docs tree instead.

The repo also includes runnable scripts and notebooks under `examples/`.

## Release Target

This branch is currently being prepared for a `0.2.0a1` alpha prerelease.

- Use `0.2.0a1` as the docs/release framing for the next cut from this branch.
- Follow normal prerelease progression after that: `0.2.0a2`, `0.2.0a3`, and so
  on.
- The project version remains VCS-derived through Hatch, so the actual package
  version will come from the eventual git tag rather than a hardcoded file edit.

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
