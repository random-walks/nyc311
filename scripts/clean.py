"""Remove common local build, cache, and documentation artifacts."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES_TO_REMOVE = (
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dist",
    "site",
)


def _remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
        return
    if path.exists():
        path.unlink()


def main() -> int:
    """Delete common local output and cache directories for a clean workspace."""
    for relative_path in DIRECTORIES_TO_REMOVE:
        _remove_path(ROOT / relative_path)

    for cache_dir in ROOT.rglob("__pycache__"):
        shutil.rmtree(cache_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
