from __future__ import annotations

from datetime import date
from pathlib import Path

from nyc311.loaders import load_service_requests
from nyc311.models import ServiceRequestRecord, TopicQuery, supported_topic_queries
from nyc311.processors import aggregate_by_geography, extract_topics

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "service_requests_fixture.csv"


def test_supported_topic_queries_includes_expanded_complaint_types() -> None:
    assert supported_topic_queries() == (
        "Abandoned Vehicle",
        "Blocked Driveway",
        "HEAT/HOT WATER",
        "Illegal Parking",
        "Noise - Residential",
        "Noise - Street/Sidewalk",
        "Rodent",
        "Street Condition",
        "UNSANITARY CONDITION",
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


def test_extract_topics_supports_new_high_volume_default_rules() -> None:
    records = [
        ServiceRequestRecord(
            service_request_id="2001",
            created_date=date(2025, 1, 1),
            complaint_type="HEAT/HOT WATER",
            descriptor="Apartment has no heat and radiator is cold",
            borough="BRONX",
            community_district="BRONX 01",
        ),
        ServiceRequestRecord(
            service_request_id="2002",
            created_date=date(2025, 1, 2),
            complaint_type="Street Condition",
            descriptor="Large pothole in traffic lane",
            borough="BRONX",
            community_district="BRONX 01",
        ),
        ServiceRequestRecord(
            service_request_id="2003",
            created_date=date(2025, 1, 3),
            complaint_type="Noise - Street/Sidewalk",
            descriptor="Bar patrons shouting outside at closing time",
            borough="BRONX",
            community_district="BRONX 01",
        ),
        ServiceRequestRecord(
            service_request_id="2004",
            created_date=date(2025, 1, 4),
            complaint_type="UNSANITARY CONDITION",
            descriptor="Garbage and trash piling up in rear yard",
            borough="BRONX",
            community_district="BRONX 01",
        ),
        ServiceRequestRecord(
            service_request_id="2005",
            created_date=date(2025, 1, 5),
            complaint_type="Abandoned Vehicle",
            descriptor="Abandoned stripped vehicle has not moved for months",
            borough="BRONX",
            community_district="BRONX 01",
        ),
    ]

    assert extract_topics(records, TopicQuery("HEAT/HOT WATER"))[0].topic == "no_heat"
    assert extract_topics(records, TopicQuery("Street Condition"))[0].topic == "pothole"
    assert (
        extract_topics(records, TopicQuery("Noise - Street/Sidewalk"))[0].topic
        == "bar_noise"
    )
    assert (
        extract_topics(records, TopicQuery("UNSANITARY CONDITION"))[0].topic
        == "garbage"
    )
    assert (
        extract_topics(records, TopicQuery("Abandoned Vehicle"))[0].topic
        == "derelict_vehicle"
    )
