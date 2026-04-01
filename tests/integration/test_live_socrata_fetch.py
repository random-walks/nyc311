from __future__ import annotations

import os

import pytest

from nyc311.io import load_service_requests
from nyc311.models import ServiceRequestFilter, SocrataConfig

pytestmark = [
    pytest.mark.integration,
    pytest.mark.network,
    pytest.mark.fetch,
]


@pytest.mark.skipif(
    os.getenv("NYC311_RUN_LIVE_FETCH_TESTS") != "1",
    reason="set NYC311_RUN_LIVE_FETCH_TESTS=1 to run live Socrata checks",
)
def test_live_socrata_fetch_returns_real_records() -> None:
    records = load_service_requests(
        SocrataConfig(page_size=1, max_pages=1, request_timeout_seconds=30.0),
        filters=ServiceRequestFilter(
            complaint_types=("Noise - Residential",),
        ),
    )

    assert len(records) == 1
    record = records[0]
    assert record.service_request_id
    assert record.complaint_type == "Noise - Residential"
    assert record.borough
    assert record.community_district
