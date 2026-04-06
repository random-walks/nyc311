"""Shared filesystem roots for the about-the-data example."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_CACHE = ROOT / "cache"
REPORTS_DIR = ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
ARTIFACTS_DIR = ROOT / "artifacts"
