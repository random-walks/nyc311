from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from nyc311.loaders import REQUIRED_SERVICE_REQUEST_COLUMNS, load_service_requests
from nyc311.models import GeographyFilter, ServiceRequestFilter

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "service_requests_fixture.csv"


def test_load_service_requests_without_filters_returns_all_fixture_rows() -> None:
    records = load_service_requests(FIXTURE_PATH)

    assert len(records) == 10
    assert records[0].service_request_id == "1000001"
    assert records[-1].community_district == "Manhattan 06"


def test_load_service_requests_filters_by_date_geography_and_complaint_type() -> None:
    filters = ServiceRequestFilter(
        start_date=date(2025, 1, 5),
        end_date=date(2025, 1, 10),
        geography=GeographyFilter(geography="community_district", value="Brooklyn 01"),
        complaint_types=("Noise - Residential",),
    )

    records = load_service_requests(FIXTURE_PATH, filters=filters)

    assert [record.service_request_id for record in records] == ["1000002", "1000003"]


def test_load_service_requests_filters_by_borough() -> None:
    records = load_service_requests(
        FIXTURE_PATH,
        filters=ServiceRequestFilter(
            geography=GeographyFilter(geography="borough", value="Brooklyn"),
        ),
    )

    assert len(records) == 5
    assert {record.borough for record in records} == {"Brooklyn"}


def test_load_service_requests_requires_expected_columns(tmp_path: Path) -> None:
    invalid_csv = tmp_path / "invalid_fixture.csv"
    invalid_csv.write_text(
        "unique_key,created_date,complaint_type,descriptor,borough\n"
        "1,2025-01-01,Noise - Residential,Loud party,Brooklyn\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        load_service_requests(invalid_csv)


def test_required_service_request_columns_are_documented() -> None:
    assert REQUIRED_SERVICE_REQUEST_COLUMNS == (
        "unique_key",
        "created_date",
        "complaint_type",
        "descriptor",
        "borough",
        "community_district",
    )
