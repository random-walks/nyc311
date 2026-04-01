"""Public typed models and constants for the nyc311 package."""

from __future__ import annotations

from ._analysis import (
    AnalysisWindow,
    AnomalyResult,
    ExportTarget,
    GeographyTopicSummary,
    ResolutionGapSummary,
    TopicCoverageReport,
    TopicQuery,
)
from ._boundaries import BoundaryCollection, BoundaryFeature, BoundaryGeoJSONExport
from ._constants import (
    BOROUGH_BRONX,
    BOROUGH_BROOKLYN,
    BOROUGH_MANHATTAN,
    BOROUGH_QUEENS,
    BOROUGH_STATEN_ISLAND,
    SOCRATA_DATASET_IDENTIFIER,
    SUPPORTED_BOROUGHS,
    SUPPORTED_BOUNDARY_GEOGRAPHIES,
    SUPPORTED_GEOGRAPHIES,
    SUPPORTED_RECORD_GEOGRAPHIES,
    BoroughName,
    supported_topic_queries,
)
from ._filters import GeographyFilter, ServiceRequestFilter, SocrataConfig
from ._normalize import normalize_borough_name
from ._records import ServiceRequestRecord, TopicAssignment

__all__ = [
    "AnalysisWindow",
    "AnomalyResult",
    "BOROUGH_BRONX",
    "BOROUGH_BROOKLYN",
    "BOROUGH_MANHATTAN",
    "BOROUGH_QUEENS",
    "BOROUGH_STATEN_ISLAND",
    "BoundaryCollection",
    "BoundaryFeature",
    "BoundaryGeoJSONExport",
    "BoroughName",
    "ExportTarget",
    "GeographyFilter",
    "GeographyTopicSummary",
    "ResolutionGapSummary",
    "SOCRATA_DATASET_IDENTIFIER",
    "SUPPORTED_BOUNDARY_GEOGRAPHIES",
    "SUPPORTED_BOROUGHS",
    "SUPPORTED_GEOGRAPHIES",
    "SUPPORTED_RECORD_GEOGRAPHIES",
    "ServiceRequestFilter",
    "ServiceRequestRecord",
    "SocrataConfig",
    "TopicAssignment",
    "TopicCoverageReport",
    "TopicQuery",
    "normalize_borough_name",
    "supported_topic_queries",
]
