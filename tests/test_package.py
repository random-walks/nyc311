from __future__ import annotations

import importlib.metadata
from pathlib import Path

import nyc311 as m
from nyc311.models import (
    AnalysisWindow,
    AnomalyResult,
    ExportTarget,
    GeographyFilter,
    ServiceRequestFilter,
    TopicCoverageReport,
    TopicQuery,
)


def test_version() -> None:
    assert m.__version__.startswith(importlib.metadata.version("nyc311"))


def test_public_surface_exposes_current_alpha_contract() -> None:
    window = AnalysisWindow(days=30)
    anomaly = AnomalyResult(
        geography="borough",
        geography_value="BROOKLYN",
        complaint_type="Noise - Residential",
        topic="party_music",
        complaint_count=10,
        geography_total_count=20,
        share_of_geography=0.5,
        topic_rank=1,
        z_score=2.0,
        is_anomaly=True,
        window_days=30,
        anomaly_threshold=2.0,
    )
    coverage = TopicCoverageReport(
        complaint_type="Noise - Residential",
        total_records=10,
        matched_records=8,
        other_records=2,
        coverage_rate=0.8,
        top_unmatched_descriptors=(("Loud shouting on roof", 2),),
    )
    geography = GeographyFilter(geography="borough", value="brooklyn")
    query = TopicQuery(complaint_type="Noise - Residential", top_n=10)
    service_request_filter = ServiceRequestFilter(geography=geography)
    target = ExportTarget(format="geojson", output_path=Path("topics.geojson"))

    assert window.days == 30
    assert anomaly.is_anomaly is True
    assert coverage.coverage_rate == 0.8
    assert geography.value == m.BOROUGH_BROOKLYN
    assert query.top_n == 10
    assert service_request_filter.geography == geography
    assert target.format == "geojson"
    assert m.normalize_borough_name("bk") == m.BOROUGH_BROOKLYN
    assert callable(m.load_service_requests)
    assert callable(m.fetch_service_requests)
    assert callable(m.load_resolution_data)
    assert callable(m.load_boundaries_geodataframe)
    assert callable(m.extract_topics)
    assert callable(m.aggregate_by_geography)
    assert callable(m.analyze_topic_coverage)
    assert callable(m.analyze_resolution_gaps)
    assert callable(m.detect_anomalies)
    assert callable(m.register_topic_rules)
    assert callable(m.export_anomalies)
    assert callable(m.export_report_card)
    assert callable(m.export_topic_table)
    assert callable(m.export_service_requests_csv)
    assert callable(m.assignments_to_dataframe)
    assert callable(m.anomalies_to_dataframe)
    assert callable(m.coverage_to_dataframe)
    assert callable(m.dataframe_to_records)
    assert callable(m.gaps_to_dataframe)
    assert callable(m.records_to_dataframe)
    assert callable(m.records_to_geodataframe)
    assert callable(m.run_topic_pipeline)
    assert callable(m.spatial_join_records_to_boundaries)
    assert callable(m.summaries_to_dataframe)
    assert callable(m.summaries_to_geodataframe)
    assert "Noise - Residential" in m.supported_topic_queries()
