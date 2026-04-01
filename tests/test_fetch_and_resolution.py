from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

import pytest
from typing_extensions import Self

from nyc311.analysis import analyze_resolution_gaps
from nyc311.io import load_resolution_data
from nyc311.models import (
    BOROUGH_BROOKLYN,
    BOROUGH_MANHATTAN,
    BOROUGH_QUEENS,
    GeographyFilter,
    ServiceRequestFilter,
    ServiceRequestRecord,
    SocrataConfig,
    normalize_borough_name,
)
from nyc311.pipeline import fetch_service_requests

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


def test_normalize_borough_name_supports_common_aliases() -> None:
    assert normalize_borough_name("bk") == BOROUGH_BROOKLYN
    assert normalize_borough_name("new york") == BOROUGH_MANHATTAN
    assert GeographyFilter("borough", "queens").value == BOROUGH_QUEENS


@pytest.mark.fetch
def test_fetch_service_requests_returns_in_memory_records_and_can_export(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "snapshot.csv"

    def fake_urlopen(request: object, *, timeout: float | None = None) -> FakeResponse:
        del request, timeout
        return FakeResponse(
            [
                {
                    "unique_key": "9101",
                    "created_date": "2025-02-01T10:00:00",
                    "complaint_type": "Rodent",
                    "descriptor": "Rats seen behind building",
                    "borough": "BK",
                    "community_board": "BROOKLYN 01",
                    "resolution_description": "Inspection scheduled",
                }
            ]
        )

    monkeypatch.setattr("nyc311.io._service_requests.urlopen", fake_urlopen)

    records = fetch_service_requests(
        filters=ServiceRequestFilter(
            geography=GeographyFilter("borough", "Brooklyn"),
            complaint_types=("Rodent",),
        ),
        socrata_config=SocrataConfig(page_size=100, max_pages=1),
        output=output_path,
    )

    assert len(records) == 1
    assert records[0].borough == BOROUGH_BROOKLYN
    assert output_path.exists()

    with output_path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows[0]["borough"] == BOROUGH_BROOKLYN
    assert rows[0]["complaint_type"] == "Rodent"


def test_load_resolution_data_returns_only_rows_with_resolution_text(
    tmp_path: Path,
) -> None:
    csv_path = tmp_path / "resolution.csv"
    csv_path.write_text(
        (
            "unique_key,created_date,complaint_type,descriptor,borough,community_district,resolution_description\n"
            "1,2025-01-01,Rodent,Rats in alley,BROOKLYN,BROOKLYN 01,Inspection completed\n"
            "2,2025-01-02,Rodent,Rats behind trash,BROOKLYN,BROOKLYN 01,\n"
        ),
        encoding="utf-8",
    )

    resolution_records = load_resolution_data(csv_path)

    assert [record.service_request_id for record in resolution_records] == ["1"]


def test_analyze_resolution_gaps_summarizes_borough_level_resolution() -> None:
    service_requests = [
        ServiceRequestRecord(
            service_request_id="1",
            created_date=date(2025, 1, 1),
            complaint_type="Rodent",
            descriptor="Rat in alley",
            borough="BK",
            community_district="BROOKLYN 01",
            resolution_description="Inspection completed",
        ),
        ServiceRequestRecord(
            service_request_id="2",
            created_date=date(2025, 1, 2),
            complaint_type="Rodent",
            descriptor="Rat in yard",
            borough="Brooklyn",
            community_district="BROOKLYN 01",
        ),
        ServiceRequestRecord(
            service_request_id="3",
            created_date=date(2025, 1, 3),
            complaint_type="Noise - Residential",
            descriptor="Loud party music",
            borough="Queens",
            community_district="QUEENS 02",
        ),
    ]
    resolution_records = [service_requests[0]]

    summaries = analyze_resolution_gaps(service_requests, resolution_records)

    assert summaries[0].geography == "borough"
    assert summaries[0].geography_value == BOROUGH_QUEENS
    assert summaries[0].unresolved_request_count == 1
    assert summaries[0].unresolved_share == 1.0
    assert summaries[1].geography_value == BOROUGH_BROOKLYN
    assert summaries[1].resolved_request_count == 1
    assert summaries[1].unresolved_request_count == 1
