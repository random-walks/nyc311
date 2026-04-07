"""Shared filesystem roots for the about-the-data example."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Repo root (…/nyc311): about-the-data → examples → nyc311
REPO_ROOT = ROOT.parent.parent
DEFAULT_CACHE = ROOT / "cache"
REPORTS_DIR = ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"
ARTIFACTS_DIR = ROOT / "artifacts"
# Root README + PyPI long description (`readme = "README.md"`) use this asset.
README_HERO_IMAGE = REPO_ROOT / "docs" / "images" / "nyc311-hero.png"
SCATTER_LIB_COVER = FIGURES_DIR / "all-scatter-lib-cover.png"
