from __future__ import annotations

from pathlib import Path

from nyc311.loaders import load_service_requests
from nyc311.models import TopicQuery, supported_topic_queries
from nyc311.processors import aggregate_by_geography, extract_topics

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "service_requests_fixture.csv"


def test_supported_topic_queries_includes_expanded_complaint_types() -> None:
    assert supported_topic_queries() == (
        "Illegal Parking",
        "Noise - Residential",
        "Rodent",
        "Street Condition",
    )


def test_extract_topics_assigns_street_condition_labels() -> None:
    records = load_service_requests(FIXTURE_PATH)

    assignments = extract_topics(records, TopicQuery(complaint_type="Street Condition"))

    topic_by_id = {
        assignment.record.service_request_id: assignment.topic
        for assignment in assignments
    }

    assert topic_by_id == {
        "1013": "pothole",
        "1014": "sinkhole_or_cave_in",
        "1015": "road_surface_damage",
    }


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
        "1018": "sidewalk_blocking",
    }


def test_aggregate_by_geography_handles_expanded_complaint_types() -> None:
    records = load_service_requests(FIXTURE_PATH)
    assignments = extract_topics(records, TopicQuery(complaint_type="Illegal Parking"))

    summaries = aggregate_by_geography(assignments, geography="borough")

    assert [
        (summary.geography_value, summary.topic, summary.complaint_count)
        for summary in summaries
    ] == [
        ("BRONX", "hydrant_blocking", 1),
        ("BROOKLYN", "double_parked", 1),
        ("QUEENS", "sidewalk_blocking", 1),
    ]
