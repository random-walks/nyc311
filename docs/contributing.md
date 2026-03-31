# Contributing

Contributions are welcome, especially when they keep the package honest about
what is implemented today and improve the usefulness of the SDK, CLI, or docs.

## Development Setup

The fastest full setup is:

```bash
uv sync --all-groups
```

You can also use `uvx nox` for session-based development.

## Common Commands

If you use the provided Makefile:

```bash
make install
make test
make test-fetch
make test-integration
make lint
make docs
make audit
```

If you prefer direct commands:

```bash
uv run pytest
uv run pytest -m fetch
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

## Contribution Expectations

- keep the implemented surface narrow and explicit
- add or update tests for meaningful behavior changes
- update docs when CLI or SDK behavior changes
- avoid presenting planned placeholders as shipped features

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
