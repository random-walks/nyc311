from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from nyc311.io import load_service_requests
from nyc311.models import GeographyFilter, ServiceRequestFilter

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "service_requests_fixture.csv"


def test_load_service_requests_without_filters_returns_all_fixture_rows() -> None:
    records = load_service_requests(FIXTURE_PATH)

    assert len(records) == 18
    assert records[0].service_request_id == "1001"
    assert records[0].latitude == pytest.approx(40.73)
    assert records[0].longitude == pytest.approx(-73.96)
    assert records[-1].community_district == "MANHATTAN 10"


def test_load_service_requests_filters_by_date_geography_and_complaint_type() -> None:
    filters = ServiceRequestFilter(
        start_date=date(2025, 1, 5),
        end_date=date(2025, 1, 11),
        geography=GeographyFilter(geography="community_district", value="BROOKLYN 01"),
        complaint_types=("Noise - Residential",),
    )

    records = load_service_requests(FIXTURE_PATH, filters=filters)

    assert [record.service_request_id for record in records] == ["1001", "1002"]


def test_load_service_requests_filters_by_borough() -> None:
    records = load_service_requests(
        FIXTURE_PATH,
        filters=ServiceRequestFilter(
            geography=GeographyFilter(geography="borough", value="Brooklyn"),
        ),
    )

    assert len(records) == 8
    assert {record.borough for record in records} == {"BROOKLYN"}


def test_load_service_requests_requires_expected_columns(tmp_path: Path) -> None:
    invalid_csv = tmp_path / "invalid_fixture.csv"
    invalid_csv.write_text(
        "unique_key,created_date,complaint_type,descriptor,borough\n"
        "1,2025-01-01,Noise - Residential,Loud party,Brooklyn\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="community-district column"):
        load_service_requests(invalid_csv)


def test_load_service_requests_allows_csvs_without_coordinate_columns(
    tmp_path: Path,
) -> None:
    csv_path = tmp_path / "no_coordinates.csv"
    csv_path.write_text(
        (
            "unique_key,created_date,complaint_type,descriptor,borough,community_district,resolution_description\n"
            "1,2025-01-01,Rodent,Rats in alley,BROOKLYN,BROOKLYN 01,Inspection completed\n"
        ),
        encoding="utf-8",
    )

    records = load_service_requests(csv_path)

    assert len(records) == 1
    assert records[0].latitude is None
    assert records[0].longitude is None
