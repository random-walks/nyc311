"""Planned loader entry points for NYC 311 and related support data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ._not_implemented import planned_surface


def load_service_requests(source: str | Path) -> Any:
    """Load NYC 311 service request records from an API or cached extract."""
    planned_surface("load_service_requests()")


def load_resolution_data(source: str | Path) -> Any:
    """Load or derive resolution-related fields for gap analysis."""
    planned_surface("load_resolution_data()")


def load_boundaries(source: str | Path) -> Any:
    """Load spatial boundaries used for tract, district, or borough aggregation."""
    planned_surface("load_boundaries()")
