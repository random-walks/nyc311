"""Top-level package for the planned ``nyc311`` API surface.

The repository is intentionally seeded with typed placeholders so contributors
can see the target shape of the library before the implementation lands.
"""

from __future__ import annotations

from ._version import version as __version__
from .cli import main
from .exporters import export_anomalies, export_geojson, export_report_card, export_topic_table
from .loaders import load_boundaries, load_resolution_data, load_service_requests
from .models import AnalysisWindow, ExportTarget, GeographyFilter, TopicQuery
from .processors import aggregate_by_geography, analyze_resolution_gaps, detect_anomalies, extract_topics

__all__ = [
    "AnalysisWindow",
    "ExportTarget",
    "GeographyFilter",
    "TopicQuery",
    "__version__",
    "aggregate_by_geography",
    "analyze_resolution_gaps",
    "detect_anomalies",
    "export_anomalies",
    "export_geojson",
    "export_report_card",
    "export_topic_table",
    "extract_topics",
    "load_boundaries",
    "load_resolution_data",
    "load_service_requests",
    "main",
]
