from __future__ import annotations

import csv
from pathlib import Path

from nyc311.exporters import export_topic_table
from nyc311.loaders import load_service_requests
from nyc311.models import ExportTarget, TopicQuery
from nyc311.processors import aggregate_by_geography, extract_topics

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "service_requests_fixture.csv"


def test_export_topic_table_writes_deterministic_csv(tmp_path: Path) -> None:
    records = load_service_requests(FIXTURE_PATH)
    assignments = extract_topics(
        records, TopicQuery(complaint_type="Noise - Residential")
    )
    summaries = aggregate_by_geography(assignments, geography="community_district")

    output_path = tmp_path / "exports" / "noise_topics.csv"
    written_path = export_topic_table(
        summaries,
        ExportTarget(format="csv", output_path=output_path),
    )

    assert written_path == output_path

    with output_path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows[0] == {
        "geography": "community_district",
        "geography_value": "BROOKLYN 01",
        "complaint_type": "Noise - Residential",
        "topic": "banging",
        "complaint_count": "1",
        "geography_total_count": "2",
        "share_of_geography": "0.500000",
        "topic_rank": "1",
        "is_dominant_topic": "true",
    }
    assert rows[-1] == {
        "geography": "community_district",
        "geography_value": "QUEENS 02",
        "complaint_type": "Noise - Residential",
        "topic": "banging",
        "complaint_count": "1",
        "geography_total_count": "3",
        "share_of_geography": "0.333333",
        "topic_rank": "2",
        "is_dominant_topic": "false",
    }
