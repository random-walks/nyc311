from __future__ import annotations

import importlib.metadata
from pathlib import Path

import nyc311 as m
from nyc311.models import (
    AnalysisWindow,
    ExportTarget,
    GeographyFilter,
    ServiceRequestFilter,
    TopicQuery,
)


def test_version() -> None:
    assert importlib.metadata.version("nyc311") == m.__version__


def test_public_surface_exposes_v0_1_contract() -> None:
    window = AnalysisWindow(days=30)
    geography = GeographyFilter(geography="borough", value="brooklyn")
    query = TopicQuery(complaint_type="Noise - Residential", top_n=10)
    service_request_filter = ServiceRequestFilter(geography=geography)
    target = ExportTarget(format="geojson", output_path=Path("topics.geojson"))

    assert window.days == 30
    assert geography.value == "brooklyn"
    assert query.top_n == 10
    assert service_request_filter.geography == geography
    assert target.format == "geojson"
    assert callable(m.load_service_requests)
    assert callable(m.extract_topics)
    assert callable(m.aggregate_by_geography)
    assert callable(m.export_topic_table)
    assert "Noise - Residential" in m.supported_topic_queries()
