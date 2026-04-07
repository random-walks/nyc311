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
from ._timeseries import (
    resample_and_fill,
    to_panel,
    to_timeseries,
    to_topic_timeseries,
)

__all__ = [
    "anomalies_to_dataframe",
    "assignments_to_dataframe",
    "coverage_to_dataframe",
    "dataframe_to_records",
    "gaps_to_dataframe",
    "records_to_dataframe",
    "resample_and_fill",
    "summaries_to_dataframe",
    "to_panel",
    "to_timeseries",
    "to_topic_timeseries",
]
