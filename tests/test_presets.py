from __future__ import annotations

from datetime import date

import pytest

from nyc311.models import BOROUGH_BROOKLYN, BOROUGH_MANHATTAN
from nyc311.presets import (
    brooklyn_borough_filter,
    build_filter,
    large_socrata_config,
    manhattan_borough_filter,
    small_socrata_config,
    smoke_socrata_config,
)

pytestmark = pytest.mark.unit


def test_build_filter_coerces_dates_and_geography() -> None:
    filters = build_filter(
        start_date="2025-01-01",
        end_date=date(2025, 1, 31),
        geography="borough",
        geography_value="Brooklyn",
        complaint_types=("Rodent",),
    )

    assert filters.start_date == date(2025, 1, 1)
    assert filters.end_date == date(2025, 1, 31)
    assert filters.geography is not None
    assert filters.geography.geography == "borough"
    assert filters.geography.value == BOROUGH_BROOKLYN
    assert filters.complaint_types == ("Rodent",)


def test_borough_filter_presets_use_canonical_borough_values() -> None:
    brooklyn = brooklyn_borough_filter(
        start_date="2025-01-01",
        end_date="2025-01-31",
    )
    manhattan = manhattan_borough_filter(
        start_date="2025-01-01",
        end_date="2025-01-31",
    )

    assert brooklyn.geography is not None
    assert manhattan.geography is not None
    assert brooklyn.geography.value == BOROUGH_BROOKLYN
    assert manhattan.geography.value == BOROUGH_MANHATTAN


def test_small_socrata_config_uses_example_friendly_defaults() -> None:
    config = small_socrata_config(app_token="demo-token")

    assert config.app_token == "demo-token"
    assert config.page_size == 500
    assert config.max_pages == 1


def test_large_socrata_config_uses_bulk_defaults() -> None:
    config = large_socrata_config(app_token="demo-token")

    assert config.app_token == "demo-token"
    assert config.page_size == 5_000
    assert config.max_pages is None
    assert config.request_timeout_seconds == 300.0
    assert config.created_date_sort == "asc"


def test_smoke_socrata_config_is_recent_first() -> None:
    config = smoke_socrata_config(app_token="demo-token")

    assert config.created_date_sort == "desc"
    assert config.page_size == 5_000
    assert config.request_timeout_seconds == 120.0
