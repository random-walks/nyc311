from __future__ import annotations

import csv
from pathlib import Path

import pytest

from nyc311.exporters import (
    export_anomalies,
    export_report_card,
    export_service_requests_csv,
    export_topic_table,
)
from nyc311.loaders import load_service_requests
from nyc311.models import AnalysisWindow, ExportTarget, TopicQuery
from nyc311.processors import (
    aggregate_by_geography,
    analyze_resolution_gaps,
    detect_anomalies,
    extract_topics,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "service_requests_fixture.csv"
pytestmark = pytest.mark.unit


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


@pytest.mark.fetch
def test_export_service_requests_csv_writes_snapshot_rows(tmp_path: Path) -> None:
    records = load_service_requests(FIXTURE_PATH)
    output_path = tmp_path / "exports" / "service_requests.csv"

    written_path = export_service_requests_csv(
        records,
        ExportTarget(format="csv", output_path=output_path),
    )

    assert written_path == output_path

    with output_path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows[0] == {
        "unique_key": "1001",
        "created_date": "2025-01-05",
        "complaint_type": "Noise - Residential",
        "descriptor": "Loud party music after midnight",
        "borough": "BROOKLYN",
        "community_district": "BROOKLYN 01",
        "resolution_description": "Officers advised occupants to lower music",
    }


def test_export_anomalies_writes_csv(tmp_path: Path) -> None:
    records = load_service_requests(FIXTURE_PATH)
    assignments = extract_topics(
        records,
        TopicQuery(complaint_type="Noise - Residential"),
    )
    summaries = aggregate_by_geography(assignments, geography="community_district")
    anomalies = detect_anomalies(summaries, AnalysisWindow(days=30), z_threshold=1.0)
    output_path = tmp_path / "exports" / "anomalies.csv"

    written_path = export_anomalies(
        anomalies,
        ExportTarget(format="csv", output_path=output_path),
    )

    assert written_path == output_path
    with output_path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert rows
    assert "z_score" in rows[0]


def test_export_report_card_writes_markdown(tmp_path: Path) -> None:
    records = load_service_requests(FIXTURE_PATH)
    assignments = extract_topics(
        records,
        TopicQuery(complaint_type="Noise - Residential"),
    )
    summaries = aggregate_by_geography(assignments, geography="community_district")
    gaps = analyze_resolution_gaps(
        records,
        [record for record in records if record.resolution_description is not None],
    )
    anomalies = detect_anomalies(summaries, AnalysisWindow(days=30), z_threshold=1.0)
    output_path = tmp_path / "exports" / "report-card.md"

    written_path = export_report_card(
        {
            "topic_summaries": summaries,
            "resolution_gaps": gaps,
            "anomalies": anomalies,
        },
        ExportTarget(format="md", output_path=output_path),
    )

    assert written_path == output_path
    content = output_path.read_text(encoding="utf-8")
    assert "# NYC311 Report Card" in content
    assert "Dominant topic" in content
