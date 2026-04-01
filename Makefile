.PHONY: help install install-dev test test-optional test-fetch test-integration lint lint-fix format docs docs-build audit clean build ci ci-lint ci-build ci-docs ci-tests

help:
	@echo "Available targets:"
	@echo "  install      Sync the full contributor environment with all extras"
	@echo "  install-dev  Sync the default dev environment without extras"
	@echo "  test         Run the full non-live pytest suite with all extras"
	@echo "  test-optional Run the optional-feature subset with all extras"
	@echo "  test-fetch   Run fetch-focused tests"
	@echo "  test-integration Run the live/integration test session with all extras"
	@echo "  lint         Run Ruff, mypy, and the public API audit"
	@echo "  lint-fix     Apply safe automatic fixes, then run the full lint job"
	@echo "  build        Build the source and wheel distributions"
	@echo "  format       Apply Ruff fixes and formatting"
	@echo "  docs         Serve the MkDocs site locally"
	@echo "  docs-build   Build the docs with strict checks"
	@echo "  audit        Print the public API audit"
	@echo "  clean        Remove local caches and build artifacts"
	@echo "  ci           Run the local GitHub-CI-equivalent job sequence with summary output"

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

lint-fix:
	uv sync --frozen --group docs --all-extras
	uv run --frozen ruff check --fix .
	uv run --frozen ruff format .
	env -u NO_COLOR -u FORCE_COLOR uvx nox -s lint -- blacken-docs end-of-file-fixer \
		mixed-line-ending requirements-txt-fixer trailing-whitespace rst-backticks \
		rst-directive-colons rst-inline-touching-normal prettier codespell
	$(MAKE) ci-lint

ci-lint:
	uv sync --frozen --group docs --all-extras
	uv run --frozen ruff check --output-format=github .
	uv run --frozen ruff format --check .
	uv run --frozen mypy
	uv run --frozen pylint nyc311
	uv run --frozen python scripts/audit_public_api.py
	env -u NO_COLOR -u FORCE_COLOR uvx nox -s lint -- blacken-docs check-added-large-files \
		check-case-conflict check-merge-conflict check-symlinks check-yaml \
		debug-statements end-of-file-fixer mixed-line-ending name-tests-test \
		requirements-txt-fixer trailing-whitespace rst-backticks \
		rst-directive-colons rst-inline-touching-normal prettier codespell \
		shellcheck disallow-caps validate-pyproject check-dependabot \
		check-github-workflows check-readthedocs

ci-build:
	uv run --with build python -m build

ci-docs:
	uv sync --frozen --group docs --all-extras
	uv run --frozen mkdocs build --strict

ci-tests:
	uv sync --frozen --all-extras
	uv run --frozen pytest -m "not integration" -ra --cov \
		--cov-report=xml --cov-report=term --durations=20

format:
	uv run ruff check --fix . && uv run ruff format .

docs:
	uv run mkdocs serve

docs-build:
	uv run mkdocs build --strict

audit:
	uv run python scripts/audit_public_api.py

build:
	uv run --with build python -m build

clean:
	uv run python scripts/clean.py

ci:
	@set -u; \
	lint_status=0; \
	build_status=0; \
	docs_status=0; \
	tests_status=0; \
	printf '\n==> [lint]\n'; \
	$(MAKE) ci-lint || lint_status=$$?; \
	printf '\n==> [build]\n'; \
	$(MAKE) ci-build || build_status=$$?; \
	printf '\n==> [docs]\n'; \
	$(MAKE) ci-docs || docs_status=$$?; \
	printf '\n==> [tests]\n'; \
	$(MAKE) ci-tests || tests_status=$$?; \
	printf '\nLocal CI summary:\n'; \
	if [ $$lint_status -eq 0 ]; then printf '  lint  -> success\n'; else printf '  lint  -> failure\n'; fi; \
	if [ $$build_status -eq 0 ]; then printf '  build -> success\n'; else printf '  build -> failure\n'; fi; \
	if [ $$docs_status -eq 0 ]; then printf '  docs  -> success\n'; else printf '  docs  -> failure\n'; fi; \
	if [ $$tests_status -eq 0 ]; then printf '  tests -> success\n'; else printf '  tests -> failure\n'; fi; \
	if [ $$lint_status -ne 0 ] || [ $$build_status -ne 0 ] || [ $$docs_status -ne 0 ] || [ $$tests_status -ne 0 ]; then \
		exit 1; \
	fi
