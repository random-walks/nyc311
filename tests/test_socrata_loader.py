from __future__ import annotations

import json
from collections import deque
from datetime import date
from urllib.parse import parse_qs, urlparse

import pytest
from typing_extensions import Self

from nyc311.io import load_service_requests
from nyc311.models import GeographyFilter, ServiceRequestFilter, SocrataConfig

pytestmark = [pytest.mark.unit, pytest.mark.fetch]


class FakeResponse:
    def __init__(self, payload: object, *, status_code: int = 200) -> None:
        self._payload = payload
        self.status = status_code

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        del exc_type, exc, tb

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_load_service_requests_supports_socrata_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested_urls: list[str] = []
    payload = [
        {
            "unique_key": "2001",
            "created_date": "2025-04-01T01:02:03",
            "complaint_type": "Noise - Residential",
            "descriptor": "Loud party music all night",
            "borough": "BROOKLYN",
            "community_board": "BROOKLYN 01",
            "resolution_description": "Warning issued",
            "latitude": "40.73",
            "longitude": "-73.96",
        },
        {
            "unique_key": "2002",
            "created_date": "2025-04-02T10:30:00",
            "complaint_type": "Rodent",
            "descriptor": "Rat seen near garbage bags",
            "borough": "BROOKLYN",
            "community_district": "BROOKLYN 01",
            "latitude": "40.731",
            "longitude": "-73.961",
        },
    ]

    def fake_urlopen(request: object, *, timeout: float | None = None) -> FakeResponse:
        del timeout
        request_url = request.full_url  # type: ignore[attr-defined]
        requested_urls.append(str(request_url))
        return FakeResponse(payload)

    monkeypatch.setattr("nyc311.io._service_requests.urlopen", fake_urlopen)

    records = load_service_requests(SocrataConfig(), filters=ServiceRequestFilter())

    assert [record.service_request_id for record in records] == ["2001", "2002"]
    assert requested_urls
    parsed = urlparse(requested_urls[0])
    assert parsed.scheme == "https"
    assert parsed.netloc == "data.cityofnewyork.us"
    assert parsed.path.endswith("/resource/erm2-nwe9.json")
    query_string = parse_qs(parsed.query)
    assert "latitude" in query_string["$select"][0]
    assert "longitude" in query_string["$select"][0]
    assert records[0].latitude == pytest.approx(40.73)
    assert records[0].longitude == pytest.approx(-73.96)


def test_load_service_requests_builds_filtered_socrata_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested_urls: list[str] = []

    def fake_urlopen(request: object, *, timeout: float | None = None) -> FakeResponse:
        del timeout
        request_url = request.full_url  # type: ignore[attr-defined]
        requested_urls.append(str(request_url))
        return FakeResponse([])

    monkeypatch.setattr("nyc311.io._service_requests.urlopen", fake_urlopen)

    load_service_requests(
        SocrataConfig(),
        filters=ServiceRequestFilter(
            start_date=date(2025, 4, 1),
            end_date=date(2025, 4, 30),
            geography=GeographyFilter("borough", "Brooklyn"),
            complaint_types=("Noise - Residential", "Rodent"),
        ),
    )

    assert len(requested_urls) == 1
    query_string = parse_qs(urlparse(requested_urls[0]).query)
    where_clause = query_string["$where"][0]
    assert "created_date >= '2025-04-01T00:00:00'" in where_clause
    assert "created_date <= '2025-04-30T23:59:59'" in where_clause
    assert "borough = 'BROOKLYN'" in where_clause
    assert "complaint_type IN ('Noise - Residential', 'Rodent')" in where_clause


def test_load_service_requests_uses_community_board_for_live_district_filter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested_urls: list[str] = []

    def fake_urlopen(request: object, *, timeout: float | None = None) -> FakeResponse:
        del timeout
        request_url = request.full_url  # type: ignore[attr-defined]
        requested_urls.append(str(request_url))
        return FakeResponse([])

    monkeypatch.setattr("nyc311.io._service_requests.urlopen", fake_urlopen)

    load_service_requests(
        SocrataConfig(),
        filters=ServiceRequestFilter(
            geography=GeographyFilter("community_district", "BROOKLYN 01"),
        ),
    )

    assert len(requested_urls) == 1
    query_string = parse_qs(urlparse(requested_urls[0]).query)
    where_clause = query_string["$where"][0]
    assert "community_board = 'BROOKLYN 01'" in where_clause


def test_load_service_requests_rejects_non_json_socrata_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request: object, *, timeout: float | None = None) -> FakeResponse:
        del request, timeout
        return FakeResponse({"not": "a list"})

    monkeypatch.setattr("nyc311.io._service_requests.urlopen", fake_urlopen)

    with pytest.raises(ValueError, match="expected a JSON list"):
        load_service_requests(SocrataConfig())


def test_load_service_requests_fetches_multiple_socrata_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads = deque(
        [
            [
                {
                    "unique_key": "3001",
                    "created_date": "2025-04-01T01:02:03",
                    "complaint_type": "Noise - Residential",
                    "descriptor": "Party music",
                    "borough": "BROOKLYN",
                    "community_district": "BROOKLYN 01",
                }
            ],
            [
                {
                    "unique_key": "3002",
                    "created_date": "2025-04-02T01:02:03",
                    "complaint_type": "Noise - Residential",
                    "descriptor": "Dog barking",
                    "borough": "BROOKLYN",
                    "community_district": "BROOKLYN 01",
                }
            ],
            [],
        ]
    )
    requested_urls: list[str] = []

    def fake_urlopen(request: object, *, timeout: float | None = None) -> FakeResponse:
        del timeout
        request_url = request.full_url  # type: ignore[attr-defined]
        requested_urls.append(str(request_url))
        return FakeResponse(payloads.popleft())

    monkeypatch.setattr("nyc311.io._service_requests.urlopen", fake_urlopen)

    records = load_service_requests(
        SocrataConfig(page_size=1),
        filters=ServiceRequestFilter(
            complaint_types=("Noise - Residential",),
        ),
    )

    assert [record.service_request_id for record in records] == ["3001", "3002"]
    assert parse_qs(urlparse(requested_urls[0]).query)["$offset"] == ["0"]
    assert parse_qs(urlparse(requested_urls[1]).query)["$offset"] == ["1"]


def test_load_service_requests_sends_socrata_app_token_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_headers: dict[str, str] = {}

    def fake_urlopen(request: object, *, timeout: float | None = None) -> FakeResponse:
        del timeout
        request_headers = request.headers  # type: ignore[attr-defined]
        for header_name, header_value in request_headers.items():
            captured_headers[str(header_name)] = str(header_value)
        return FakeResponse([])

    monkeypatch.setattr("nyc311.io._service_requests.urlopen", fake_urlopen)

    load_service_requests(
        SocrataConfig(app_token="test-token"),
        filters=ServiceRequestFilter(),
    )

    assert captured_headers["X-app-token"] == "test-token"


def test_load_service_requests_allows_missing_live_descriptor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request: object, *, timeout: float | None = None) -> FakeResponse:
        del request, timeout
        return FakeResponse(
            [
                {
                    "unique_key": "7001",
                    "created_date": "2025-04-01T01:02:03",
                    "complaint_type": "Noise - Residential",
                    "borough": "BROOKLYN",
                    "community_board": "BROOKLYN 01",
                }
            ]
        )

    monkeypatch.setattr("nyc311.io._service_requests.urlopen", fake_urlopen)

    records = load_service_requests(SocrataConfig(), filters=ServiceRequestFilter())

    assert len(records) == 1
    assert records[0].descriptor == ""
