.PHONY: help install install-dev test test-optional test-fetch test-integration lint format docs docs-build audit clean ci

help:
	@echo "Available targets:"
	@echo "  install      Sync the full contributor environment"
	@echo "  install-dev  Sync the default dev environment without extras"
	@echo "  test         Run the default fast pytest suite"
	@echo "  test-optional Run pandas-backed optional-feature tests"
	@echo "  test-fetch   Run fetch-focused tests"
	@echo "  test-integration Run the live/integration test session"
	@echo "  lint         Run Ruff and mypy"
	@echo "  format       Apply Ruff fixes and formatting"
	@echo "  docs         Serve the MkDocs site locally"
	@echo "  docs-build   Build the docs with strict checks"
	@echo "  audit        Print the implemented/planned API audit"
	@echo "  clean        Remove local caches and build artifacts"
	@echo "  ci           Run the local CI-equivalent checks"

install:
	uv sync --all-groups --all-extras

install-dev:
	uv sync

test:
	uv run pytest -m "not integration and not optional"

test-optional:
	uv run --extra dataframes pytest -m optional

test-fetch:
	uv run pytest -m "fetch and not integration"

test-integration:
	uvx nox -s tests_integration

lint:
	uv run ruff check . && uv run mypy

format:
	uv run ruff check --fix . && uv run ruff format .

docs:
	uv run mkdocs serve

docs-build:
	uv run mkdocs build --strict

audit:
	uv run python scripts/audit_implementation.py

clean:
	uv run python scripts/clean.py

ci: lint test test-optional docs-build
