"""Shared output-path helpers for example scripts and notebooks."""

from __future__ import annotations

from pathlib import Path

EXAMPLES_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXAMPLES_ROOT.parent
DATA_DIR = EXAMPLES_ROOT / "data"
OUTPUT_DIR = EXAMPLES_ROOT / "output"


def ensure_output_dir() -> Path:
    """Create the shared examples output directory if needed."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def output_path(filename: str) -> Path:
    """Return a path inside the shared examples output directory."""
    return ensure_output_dir() / filename


def data_path(filename: str) -> Path:
    """Return a path inside the shared examples data directory."""
    return DATA_DIR / filename
