from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Self

import pytest

from nyc311.cli import main

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "service_requests_fixture.csv"
BOUNDARIES_PATH = (
    Path(__file__).parent / "fixtures" / "community_district_boundaries.geojson"
)

pytestmark = pytest.mark.unit


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self._payload = payload

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        del exc_type, exc, tb

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


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


@pytest.mark.fetch
def test_cli_fetch_command_exports_filtered_socrata_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "fetched.csv"

    def fake_urlopen(request: object, *, timeout: float | None = None) -> FakeResponse:
        del request, timeout
        return FakeResponse(
            [
                {
                    "unique_key": "9001",
                    "created_date": "2025-02-01T10:00:00",
                    "complaint_type": "Rodent",
                    "descriptor": "Rats seen near bags",
                    "borough": "BROOKLYN",
                    "community_district": "BROOKLYN 01",
                    "resolution_description": "Inspection scheduled",
                    "latitude": "40.73",
                    "longitude": "-73.96",
                }
            ]
        )

    monkeypatch.setattr("nyc311.io._service_requests.urlopen", fake_urlopen)

    exit_code = main(
        [
            "fetch",
            "--output",
            str(output_path),
            "--complaint-type",
            "Rodent",
            "--geography",
            "borough",
            "--geography-value",
            "BROOKLYN",
            "--start-date",
            "2025-02-01",
            "--end-date",
            "2025-02-28",
            "--page-size",
            "100",
            "--max-pages",
            "1",
        ]
    )

    assert exit_code == 0
    assert output_path.exists()

    with output_path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows == [
        {
            "unique_key": "9001",
            "created_date": "2025-02-01",
            "complaint_type": "Rodent",
            "descriptor": "Rats seen near bags",
            "borough": "BROOKLYN",
            "community_district": "BROOKLYN 01",
            "resolution_description": "Inspection scheduled",
            "latitude": "40.73",
            "longitude": "-73.96",
        }
    ]


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
