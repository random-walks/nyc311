from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from nyc311.loaders import load_service_requests
from nyc311.models import (
    AnalysisWindow,
    GeographyTopicSummary,
    ServiceRequestRecord,
    TopicQuery,
)
from nyc311.processors import (
    aggregate_by_geography,
    analyze_topic_coverage,
    detect_anomalies,
    extract_topics,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "service_requests_fixture.csv"


def test_extract_topics_assigns_deterministic_noise_labels() -> None:
    records = load_service_requests(FIXTURE_PATH)

    assignments = extract_topics(
        records,
        TopicQuery(complaint_type="Noise - Residential", top_n=10),
    )

    topic_by_id = {
        assignment.record.service_request_id: assignment.topic
        for assignment in assignments
    }

    assert topic_by_id == {
        "1001": "party_music",
        "1002": "banging",
        "1003": "construction",
        "1004": "pet_noise",
        "1005": "party_music",
        "1006": "banging",
        "1010": "party_music",
        "1011": "party_music",
        "1012": "banging",
    }


def test_extract_topics_assigns_deterministic_rodent_labels() -> None:
    records = load_service_requests(FIXTURE_PATH)

    assignments = extract_topics(records, TopicQuery(complaint_type="Rodent"))

    topic_by_id = {
        assignment.record.service_request_id: assignment.topic
        for assignment in assignments
    }

    assert topic_by_id == {
        "1007": "rats_seen",
        "1008": "mouse_condition",
        "1009": "extermination_request",
    }


def test_extract_topics_falls_back_to_descriptor_grouping_for_unknown_complaint_type() -> (
    None
):
    water_records = [
        ServiceRequestRecord(
            service_request_id="fallback-1",
            created_date=date(2025, 1, 1),
            complaint_type="Water System",
            descriptor="Low water pressure in kitchen sink",
            borough="BROOKLYN",
            community_district="BROOKLYN 01",
        ),
        ServiceRequestRecord(
            service_request_id="fallback-2",
            created_date=date(2025, 1, 2),
            complaint_type="Water System",
            descriptor="Low water pressure in kitchen sink",
            borough="BROOKLYN",
            community_district="BROOKLYN 01",
        ),
        ServiceRequestRecord(
            service_request_id="fallback-3",
            created_date=date(2025, 1, 3),
            complaint_type="Water System",
            descriptor="Leaking hydrant on corner",
            borough="BROOKLYN",
            community_district="BROOKLYN 01",
        ),
    ]

    assignments = extract_topics(
        water_records, TopicQuery(complaint_type="Water System")
    )

    assert [assignment.topic for assignment in assignments] == [
        "low water pressure in kitchen sink",
        "low water pressure in kitchen sink",
        "leaking hydrant on corner",
    ]


def test_extract_topics_handles_missing_descriptor_as_other() -> None:
    records = [
        ServiceRequestRecord(
            service_request_id="blank-descriptor",
            created_date=date(2025, 1, 1),
            complaint_type="Noise - Residential",
            descriptor="",
            borough="BROOKLYN",
            community_district="BROOKLYN 01",
        )
    ]

    assignments = extract_topics(
        records, TopicQuery(complaint_type="Noise - Residential")
    )

    assert len(assignments) == 1
    assert assignments[0].topic == "other"
    assert assignments[0].normalized_text == "unspecified"


def test_aggregate_by_geography_returns_ranked_counts_for_community_district() -> None:
    records = load_service_requests(FIXTURE_PATH)
    assignments = extract_topics(
        records, TopicQuery(complaint_type="Noise - Residential")
    )

    summaries = aggregate_by_geography(assignments, geography="community_district")

    assert len(summaries) == 8
    assert summaries[0].geography_value == "BROOKLYN 01"
    assert summaries[0].topic == "banging"
    assert summaries[0].complaint_count == 1
    assert summaries[0].share_of_geography == 0.5
    assert summaries[0].topic_rank == 1
    assert summaries[0].is_dominant_topic is True

    assert summaries[1].geography_value == "BROOKLYN 01"
    assert summaries[1].topic == "party_music"
    assert summaries[1].complaint_count == 1
    assert summaries[1].topic_rank == 2
    assert summaries[1].is_dominant_topic is False

    queens_topics = [
        (summary.topic, summary.complaint_count, summary.topic_rank)
        for summary in summaries
        if summary.geography_value == "QUEENS 02"
    ]
    assert queens_topics == [("party_music", 2, 1), ("banging", 1, 2)]


def test_aggregate_by_geography_supports_borough() -> None:
    records = load_service_requests(FIXTURE_PATH)
    assignments = extract_topics(records, TopicQuery(complaint_type="Rodent"))

    summaries = aggregate_by_geography(assignments, geography="borough")

    assert [
        (summary.geography_value, summary.topic, summary.complaint_count)
        for summary in summaries
    ] == [
        ("BROOKLYN", "mouse_condition", 1),
        ("BROOKLYN", "rats_seen", 1),
        ("MANHATTAN", "extermination_request", 1),
    ]


def test_aggregate_by_geography_rejects_unsupported_geography() -> None:
    records = load_service_requests(FIXTURE_PATH)
    assignments = extract_topics(records, TopicQuery(complaint_type="Rodent"))

    with pytest.raises(ValueError, match="postal_code"):
        aggregate_by_geography(assignments, geography="postal_code")


def test_analyze_topic_coverage_reports_other_bucket_descriptors() -> None:
    records = load_service_requests(FIXTURE_PATH)

    coverage = analyze_topic_coverage(records, TopicQuery("Illegal Parking"))

    assert coverage.complaint_type == "Illegal Parking"
    assert coverage.total_records == 3
    assert coverage.matched_records == 2
    assert coverage.other_records == 1
    assert coverage.coverage_rate == pytest.approx(2 / 3)
    assert coverage.top_unmatched_descriptors == (
        ("Truck blocking driveway entrance", 1),
    )


def test_detect_anomalies_returns_scored_results() -> None:
    summaries = [
        GeographyTopicSummary(
            geography="borough",
            geography_value="BROOKLYN",
            complaint_type="Noise - Residential",
            topic="party_music",
            complaint_count=5,
            geography_total_count=5,
            share_of_geography=1.0,
            topic_rank=1,
            is_dominant_topic=True,
        ),
        GeographyTopicSummary(
            geography="borough",
            geography_value="MANHATTAN",
            complaint_type="Noise - Residential",
            topic="party_music",
            complaint_count=6,
            geography_total_count=6,
            share_of_geography=1.0,
            topic_rank=1,
            is_dominant_topic=True,
        ),
        GeographyTopicSummary(
            geography="borough",
            geography_value="QUEENS",
            complaint_type="Noise - Residential",
            topic="party_music",
            complaint_count=25,
            geography_total_count=25,
            share_of_geography=1.0,
            topic_rank=1,
            is_dominant_topic=True,
        ),
    ]

    anomalies = detect_anomalies(
        summaries,
        AnalysisWindow(days=30),
        z_threshold=1.4,
    )

    assert len(anomalies) == 3
    assert anomalies[0].geography == "borough"
    assert anomalies[0].window_days == 30
    assert anomalies[0].is_anomaly is True
