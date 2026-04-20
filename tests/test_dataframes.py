from __future__ import annotations

from pathlib import Path

import pytest

from nyc311 import analysis, dataframes, io, models

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "service_requests_fixture.csv"
pytest.importorskip(
    "pandas",
    reason="Install nyc311[dataframes] or nyc311[science] to run dataframe helper tests.",
)
pytestmark = pytest.mark.optional


def test_records_dataframe_round_trip_preserves_core_fields() -> None:
    records = io.load_service_requests(FIXTURE_PATH)

    dataframe = dataframes.records_to_dataframe(records)
    round_tripped_records = dataframes.dataframe_to_records(dataframe)

    assert list(dataframe.columns) == [
        "service_request_id",
        "created_date",
        "complaint_type",
        "descriptor",
        "borough",
        "community_district",
        "resolution_description",
        "closed_date",
        "latitude",
        "longitude",
    ]
    assert str(dataframe["created_date"].dtype).startswith("datetime64")
    assert round_tripped_records == records


def test_summary_and_gap_dataframe_helpers_return_expected_columns() -> None:
    records = io.load_service_requests(FIXTURE_PATH)
    assignments = analysis.extract_topics(
        records,
        models.TopicQuery("Noise - Residential"),
    )
    summaries = analysis.aggregate_by_geography(
        assignments,
        geography="community_district",
    )
    gaps = analysis.analyze_resolution_gaps(
        records,
        [record for record in records if record.resolution_description is not None],
    )
    anomalies = analysis.detect_anomalies(summaries, models.AnalysisWindow(days=30))
    coverage = analysis.analyze_topic_coverage(
        records,
        models.TopicQuery("Noise - Residential"),
    )

    assignments_dataframe = dataframes.assignments_to_dataframe(assignments)
    summaries_dataframe = dataframes.summaries_to_dataframe(summaries)
    gaps_dataframe = dataframes.gaps_to_dataframe(gaps)
    anomalies_dataframe = dataframes.anomalies_to_dataframe(anomalies)
    coverage_dataframe = dataframes.coverage_to_dataframe([coverage])

    assert "topic" in assignments_dataframe.columns
    assert "is_dominant_topic" in summaries_dataframe.columns
    assert "resolution_rate" in gaps_dataframe.columns
    assert "z_score" in anomalies_dataframe.columns
    assert coverage_dataframe.loc[0, "complaint_type"] == "Noise - Residential"
