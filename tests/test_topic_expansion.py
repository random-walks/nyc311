from __future__ import annotations

from pathlib import Path

from nyc311.loaders import load_service_requests
from nyc311.models import TopicQuery, supported_topic_queries
from nyc311.processors import aggregate_by_geography, extract_topics

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "service_requests_fixture.csv"


def test_supported_topic_queries_includes_expanded_complaint_types() -> None:
    assert supported_topic_queries() == (
        "Blocked Driveway",
        "Illegal Parking",
        "Noise - Residential",
        "Rodent",
    )


def test_extract_topics_assigns_illegal_parking_labels() -> None:
    records = load_service_requests(FIXTURE_PATH)

    assignments = extract_topics(records, TopicQuery(complaint_type="Illegal Parking"))

    topic_by_id = {
        assignment.record.service_request_id: assignment.topic
        for assignment in assignments
    }

    assert topic_by_id == {
        "1016": "hydrant_blocking",
        "1017": "double_parked",
        "1018": "other",
    }


def test_extract_topics_assigns_blocked_driveway_labels() -> None:
    records = load_service_requests(FIXTURE_PATH)

    assignments = extract_topics(records, TopicQuery(complaint_type="Blocked Driveway"))

    topic_by_id = {
        assignment.record.service_request_id: assignment.topic
        for assignment in assignments
    }

    assert topic_by_id == {
        "1019": "residential_driveway",
        "1020": "commercial_driveway",
        "1021": "overnight_blocking",
    }


def test_aggregate_by_geography_handles_expanded_complaint_types() -> None:
    records = load_service_requests(FIXTURE_PATH)
    assignments = extract_topics(records, TopicQuery(complaint_type="Blocked Driveway"))

    summaries = aggregate_by_geography(assignments, geography="borough")

    assert [
        (summary.geography_value, summary.topic, summary.complaint_count)
        for summary in summaries
    ] == [
        ("BROOKLYN", "residential_driveway", 1),
        ("MANHATTAN", "overnight_blocking", 1),
        ("QUEENS", "commercial_driveway", 1),
    ]
