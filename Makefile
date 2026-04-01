.PHONY: help install install-dev test test-optional test-fetch test-integration lint format docs docs-build audit clean ci

help:
	@echo "Available targets:"
	@echo "  install      Sync the full contributor environment with all extras"
	@echo "  install-dev  Sync the default dev environment without extras"
	@echo "  test         Run the full non-live pytest suite with all extras"
	@echo "  test-optional Run the optional-feature subset with all extras"
	@echo "  test-fetch   Run fetch-focused tests"
	@echo "  test-integration Run the live/integration test session with all extras"
	@echo "  lint         Run Ruff, mypy, and the public API audit"
	@echo "  format       Apply Ruff fixes and formatting"
	@echo "  docs         Serve the MkDocs site locally"
	@echo "  docs-build   Build the docs with strict checks"
	@echo "  audit        Print the public API audit"
	@echo "  clean        Remove local caches and build artifacts"
	@echo "  ci           Run the local CI-equivalent checks"

install:
	uv sync --all-groups --all-extras

install-dev:
	uv sync

test:
	uv run --all-extras pytest -m "not integration"

test-optional:
	uv run --all-extras pytest -m optional

test-fetch:
	uv run --all-extras pytest -m "fetch and not integration"

test-integration:
	NYC311_RUN_LIVE_FETCH_TESTS=1 uv run --all-extras pytest -m integration

lint:
	uv run ruff check . && uv run mypy && uv run python scripts/audit_public_api.py

format:
	uv run ruff check --fix . && uv run ruff format .

docs:
	uv run mkdocs serve

docs-build:
	uv run mkdocs build --strict

audit:
	uv run python scripts/audit_public_api.py

clean:
	uv run python scripts/clean.py

ci: lint test docs-build
