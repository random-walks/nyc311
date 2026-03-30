from __future__ import annotations

from pathlib import Path

import pytest

from nyc311.loaders import load_service_requests
from nyc311.models import TopicQuery
from nyc311.processors import aggregate_by_geography, extract_topics

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
        "1005": "television_audio",
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


def test_extract_topics_rejects_unsupported_complaint_type() -> None:
    records = load_service_requests(FIXTURE_PATH)

    with pytest.raises(NotImplementedError, match="Water System"):
        extract_topics(records, TopicQuery(complaint_type="Water System"))


def test_aggregate_by_geography_returns_ranked_counts_for_community_district() -> None:
    records = load_service_requests(FIXTURE_PATH)
    assignments = extract_topics(records, TopicQuery(complaint_type="Noise - Residential"))

    summaries = aggregate_by_geography(assignments, geography="community_district")

    assert summaries == [
        summaries[0],
        summaries[1],
        summaries[2],
        summaries[3],
        summaries[4],
        summaries[5],
        summaries[6],
    ]
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
