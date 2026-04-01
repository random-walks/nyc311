from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / "cache"
ARTIFACTS_DIR = ROOT / "artifacts"
REPORTS_DIR = ROOT / "reports"
REPORT_FIGURES_DIR = REPORTS_DIR / "figures"

# Replace these placeholders after copying the template.
EXAMPLE_TITLE = "Example Template"
EXAMPLE_SLUG = "example-template"
DATA_MODE = "replace-me"  # sample-backed or cache-backed-live


def cache_path(filename: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / filename


def artifact_path(filename: str) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    return ARTIFACTS_DIR / filename


def report_path(filename: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR / filename


def report_figure_path(filename: str) -> Path:
    REPORT_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    return REPORT_FIGURES_DIR / filename


def print_bootstrap_checklist() -> None:
    print(EXAMPLE_TITLE)
    print("-" * len(EXAMPLE_TITLE))
    print("This folder is a bootstrap template, not a finished example.")
    print("Next steps:")
    print("- copy this folder to a new semantic slug")
    print("- update `EXAMPLE_TITLE`, `EXAMPLE_SLUG`, and `DATA_MODE`")
    print("- choose the right `nyc311` extras in `pyproject.toml`")
    print("- replace the placeholder logic in `main.py` with a real story")
    print("- keep caches in `cache/` and scratch outputs in `artifacts/`")
    print("- put stable markdown and report figures in `reports/`")


def main() -> None:
    # Suggested implementation order for a copied example:
    #
    # 1. Load data.
    #    - Sample-backed examples should prefer `nyc311.samples`.
    #    - Live examples should write or reuse a local cache file.
    #
    # 2. Build one clear analytic story.
    #    - Start from 2-4 concrete questions.
    #    - Generate only the outputs needed to answer those questions.
    #
    # 3. Split outputs by purpose.
    #    - `artifacts/` for ignored scratch CSVs and intermediates.
    #    - `reports/` for tracked markdown and tracked figures.
    #
    # 4. Write the report with relative image paths.
    #    - Use `./figures/<name>.png` from inside the markdown file.
    #
    # 5. Keep the README short and user-facing.
    print_bootstrap_checklist()


if __name__ == "__main__":
    main()
