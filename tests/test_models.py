from __future__ import annotations

from datetime import date

import pytest

from nyc311.models import BoundaryCollection, BoundaryFeature, ServiceRequestRecord


def _build_record(
    *,
    service_request_id: str = "1001",
    created_date: date = date(2025, 1, 1),
    complaint_type: str = "Rodent",
    descriptor: str = "Rats behind building",
    borough: str = "BROOKLYN",
    community_district: str = "BROOKLYN 01",
    resolution_description: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> ServiceRequestRecord:
    return ServiceRequestRecord(
        service_request_id=service_request_id,
        created_date=created_date,
        complaint_type=complaint_type,
        descriptor=descriptor,
        borough=borough,
        community_district=community_district,
        resolution_description=resolution_description,
        latitude=latitude,
        longitude=longitude,
    )


def test_service_request_record_accepts_valid_coordinate_pair() -> None:
    record = _build_record(latitude=40.73, longitude=-73.96)

    assert record.latitude == pytest.approx(40.73)
    assert record.longitude == pytest.approx(-73.96)


def test_service_request_record_allows_missing_coordinate_pair() -> None:
    record = _build_record()

    assert record.latitude is None
    assert record.longitude is None


def test_service_request_record_coerces_zero_coordinate_pair_to_none() -> None:
    record = _build_record(latitude=0.0, longitude=0.0)

    assert record.latitude is None
    assert record.longitude is None


def test_service_request_record_rejects_partial_coordinate_pair() -> None:
    with pytest.raises(ValueError, match="provided together"):
        _build_record(latitude=40.73)


def test_service_request_record_rejects_coordinates_outside_nyc_bounds() -> None:
    with pytest.raises(ValueError, match="NYC bounds"):
        _build_record(latitude=39.9, longitude=-73.96)


def test_service_request_record_normalizes_number_first_community_district() -> None:
    record = _build_record(community_district="01 BROOKLYN")

    assert record.community_district == "BROOKLYN 01"


def test_service_request_record_preserves_nonstandard_community_district_label() -> (
    None
):
    record = _build_record(community_district="Unspecified BROOKLYN")

    assert record.community_district == "Unspecified BROOKLYN"


def test_boundary_models_accept_packaged_zcta_geography() -> None:
    feature = BoundaryFeature(
        geography="zcta",
        geography_value="10001",
        geometry={"type": "Polygon", "coordinates": []},
        properties={"name": "MODZCTA 10001"},
    )

    collection = BoundaryCollection(geography="zcta", features=(feature,))

    assert collection.geography == "zcta"
    assert collection.features[0].geography_value == "10001"
