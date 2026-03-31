from __future__ import annotations

import csv
from pathlib import Path

from nyc311.exporters import export_anomalies, export_report_card
from nyc311.models import AnalysisWindow, ExportTarget, GeographyTopicSummary
from nyc311.processors import detect_anomalies


def test_detect_anomalies_returns_empty_list_for_empty_input() -> None:
    assert detect_anomalies([], AnalysisWindow(days=30)) == []


def test_implemented_exporters_write_outputs(tmp_path: Path) -> None:
    anomaly_path = tmp_path / "anomalies.csv"
    report_path = tmp_path / "report.md"

    written_anomaly_path = export_anomalies(
        [],
        ExportTarget(format="csv", output_path=anomaly_path),
    )
    written_report_path = export_report_card(
        {
            "topic_summaries": [
                GeographyTopicSummary(
                    geography="borough",
                    geography_value="BROOKLYN",
                    complaint_type="Noise - Residential",
                    topic="party_music",
                    complaint_count=3,
                    geography_total_count=4,
                    share_of_geography=0.75,
                    topic_rank=1,
                    is_dominant_topic=True,
                )
            ],
            "resolution_gaps": [],
            "anomalies": [],
        },
        ExportTarget(format="md", output_path=report_path),
    )

    assert written_anomaly_path == anomaly_path
    assert written_report_path == report_path
    with anomaly_path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert rows == []
    assert report_path.read_text(encoding="utf-8").startswith("# NYC311 Report Card")
