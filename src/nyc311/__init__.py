"""Top-level package for the implemented v0.1 ``nyc311`` surface."""

from __future__ import annotations

from ._version import version as __version__
from .boundaries import BoundaryFeature
from .cli import main
from .exporters import (
    export_anomalies,
    export_geojson,
    export_report_card,
    export_topic_table,
)
from .loaders import (
    REQUIRED_SERVICE_REQUEST_COLUMNS,
    load_boundaries,
    load_resolution_data,
    load_service_requests,
)
from .models import (
    AnalysisWindow,
    BoundaryGeoJSONExport,
    ExportTarget,
    GeographyFilter,
    GeographyTopicSummary,
    SocrataConfig,
    ServiceRequestFilter,
    ServiceRequestRecord,
    TopicAssignment,
    TopicQuery,
    supported_topic_queries,
)
from .processors import (
    aggregate_by_geography,
    analyze_resolution_gaps,
    detect_anomalies,
    extract_topics,
)

__all__ = [
    "__version__",
    "AnalysisWindow",
    "BoundaryFeature",
    "BoundaryGeoJSONExport",
    "ExportTarget",
    "GeographyFilter",
    "GeographyTopicSummary",
    "REQUIRED_SERVICE_REQUEST_COLUMNS",
    "SocrataConfig",
    "ServiceRequestFilter",
    "ServiceRequestRecord",
    "TopicAssignment",
    "TopicQuery",
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
    "supported_topic_queries",
]
