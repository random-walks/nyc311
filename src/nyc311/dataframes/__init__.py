"""Optional pandas conversion helpers for notebook and data-science workflows."""

from __future__ import annotations

from ._analysis import (
    anomalies_to_dataframe,
    coverage_to_dataframe,
    gaps_to_dataframe,
    summaries_to_dataframe,
)
from ._records import (
    assignments_to_dataframe,
    dataframe_to_records,
    records_to_dataframe,
)

__all__ = [
    "anomalies_to_dataframe",
    "assignments_to_dataframe",
    "coverage_to_dataframe",
    "dataframe_to_records",
    "gaps_to_dataframe",
    "records_to_dataframe",
    "summaries_to_dataframe",
]
