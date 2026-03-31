from __future__ import annotations

import csv
from pathlib import Path

from nyc311.cli import main

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "service_requests_fixture.csv"
BOUNDARIES_PATH = (
    Path(__file__).parent / "fixtures" / "community_district_boundaries.geojson"
)


def test_cli_topics_command_exports_csv(tmp_path: Path) -> None:
    output_path = tmp_path / "cli-output.csv"

    exit_code = main(
        [
            "topics",
            "--source",
            str(FIXTURE_PATH),
            "--output",
            str(output_path),
            "--complaint-type",
            "Noise - Residential",
            "--geography",
            "community_district",
        ]
    )

    assert exit_code == 0
    assert output_path.exists()

    with output_path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows[0]["geography"] == "community_district"
    assert rows[0]["complaint_type"] == "Noise - Residential"
    assert rows[0]["topic"] == "banging"


def test_cli_topics_command_exports_geojson(tmp_path: Path) -> None:
    output_path = tmp_path / "cli-output.geojson"

    exit_code = main(
        [
            "topics",
            "--source",
            str(FIXTURE_PATH),
            "--output",
            str(output_path),
            "--complaint-type",
            "Noise - Residential",
            "--geography",
            "community_district",
            "--format",
            "geojson",
            "--boundaries",
            str(BOUNDARIES_PATH),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
