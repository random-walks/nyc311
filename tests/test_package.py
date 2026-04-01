from __future__ import annotations

import importlib.metadata
from pathlib import Path

import nyc311 as root
from nyc311 import (
    analysis,
    cli,
    dataframes,
    export,
    geographies,
    io,
    models,
    pipeline,
    plotting,
    presets,
    samples,
    spatial,
)
from nyc311.models import (
    BOROUGH_BROOKLYN,
    AnalysisWindow,
    AnomalyResult,
    ExportTarget,
    GeographyFilter,
    ServiceRequestFilter,
    TopicCoverageReport,
    TopicQuery,
)


def _stable_version_prefix(version: str) -> str:
    return version.split("+", maxsplit=1)[0].split(".dev", maxsplit=1)[0]


def test_version() -> None:
    assert _stable_version_prefix(root.__version__) == _stable_version_prefix(
        importlib.metadata.version("nyc311")
    )


def test_root_package_is_minimal() -> None:
    assert root.__all__ == ["__version__"]


def test_public_namespaces_expose_current_contract() -> None:
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
    assert geography.value == BOROUGH_BROOKLYN
    assert query.top_n == 10
    assert service_request_filter.geography == geography
    assert target.format == "geojson"
    assert models.normalize_borough_name("bk") == BOROUGH_BROOKLYN
    assert callable(io.load_service_requests)
    assert callable(pipeline.fetch_service_requests)
    assert callable(io.load_resolution_data)
    assert callable(spatial.load_boundaries_geodataframe)
    assert callable(analysis.extract_topics)
    assert callable(analysis.aggregate_by_geography)
    assert callable(analysis.analyze_topic_coverage)
    assert callable(analysis.analyze_resolution_gaps)
    assert callable(analysis.detect_anomalies)
    assert callable(analysis.register_topic_rules)
    assert callable(export.export_anomalies)
    assert callable(export.export_report_card)
    assert callable(export.export_topic_table)
    assert callable(export.export_service_requests_csv)
    assert callable(dataframes.assignments_to_dataframe)
    assert callable(dataframes.anomalies_to_dataframe)
    assert callable(geographies.boundaries_to_dataframe)
    assert callable(geographies.boundaries_to_geojson)
    assert callable(geographies.clip_boundaries_to_bbox)
    assert callable(dataframes.coverage_to_dataframe)
    assert callable(dataframes.dataframe_to_records)
    assert callable(dataframes.gaps_to_dataframe)
    assert callable(geographies.list_boundary_layers)
    assert callable(geographies.list_boundary_values)
    assert callable(geographies.load_nyc_boundaries)
    assert callable(geographies.load_nyc_council_districts)
    assert callable(geographies.load_nyc_census_tracts)
    assert callable(geographies.load_nyc_boundaries_geodataframe)
    assert callable(geographies.load_nyc_neighborhood_tabulation_areas)
    assert callable(samples.load_sample_boundaries)
    assert callable(samples.load_sample_service_requests)
    assert callable(plotting.plot_boundary_choropleth)
    assert callable(plotting.plot_boundary_preview)
    assert callable(presets.build_filter)
    assert callable(presets.brooklyn_borough_filter)
    assert callable(presets.manhattan_borough_filter)
    assert callable(presets.small_socrata_config)
    assert callable(dataframes.records_to_dataframe)
    assert callable(spatial.records_to_geodataframe)
    assert callable(pipeline.run_topic_pipeline)
    assert callable(geographies.spatially_enrich_records)
    assert callable(spatial.spatial_join_records_to_boundaries)
    assert callable(dataframes.summaries_to_dataframe)
    assert callable(spatial.summaries_to_geodataframe)
    assert callable(cli.main)
    assert "Noise - Residential" in models.supported_topic_queries()
