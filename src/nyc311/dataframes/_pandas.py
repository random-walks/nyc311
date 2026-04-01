"""Shared pandas dependency helpers for nyc311.dataframes."""

from __future__ import annotations

from importlib import import_module
from typing import Any


def require_pandas() -> Any:
    """Import pandas on demand for optional dataframe helpers."""
    try:
        return import_module("pandas")
    except ImportError as exc:  # pragma: no cover - exercised in tests via monkeypatch
        raise ImportError(
            "pandas is required for nyc311.dataframes helpers. Install it with "
            "`pip install nyc311[dataframes]`, `pip install nyc311[science]`, "
            "or `pip install pandas`."
        ) from exc
