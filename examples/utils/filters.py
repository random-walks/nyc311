"""Reusable filter builders for example scripts and notebooks."""

from __future__ import annotations

from datetime import date

import nyc311


def _coerce_date(value: date | str) -> date:
    return value if isinstance(value, date) else date.fromisoformat(value)


def build_filter(
    *,
    start_date: date | str,
    end_date: date | str,
    geography: str = "borough",
    geography_value: str = nyc311.BOROUGH_BROOKLYN,
    complaint_types: tuple[str, ...] = (),
) -> nyc311.ServiceRequestFilter:
    """Build a standard service-request filter for examples."""
    return nyc311.ServiceRequestFilter(
        start_date=_coerce_date(start_date),
        end_date=_coerce_date(end_date),
        geography=nyc311.GeographyFilter(geography, geography_value),
        complaint_types=complaint_types,
    )


def brooklyn_borough_filter(
    *,
    start_date: date | str,
    end_date: date | str,
    complaint_types: tuple[str, ...] = (),
) -> nyc311.ServiceRequestFilter:
    """Build a borough-level Brooklyn filter."""
    return build_filter(
        start_date=start_date,
        end_date=end_date,
        geography="borough",
        geography_value=nyc311.BOROUGH_BROOKLYN,
        complaint_types=complaint_types,
    )


def manhattan_borough_filter(
    *,
    start_date: date | str,
    end_date: date | str,
    complaint_types: tuple[str, ...] = (),
) -> nyc311.ServiceRequestFilter:
    """Build a borough-level Manhattan filter."""
    return build_filter(
        start_date=start_date,
        end_date=end_date,
        geography="borough",
        geography_value=nyc311.BOROUGH_MANHATTAN,
        complaint_types=complaint_types,
    )


def brooklyn_socrata_config(
    *,
    page_size: int = 500,
    max_pages: int | None = 1,
    app_token: str | None = None,
) -> nyc311.SocrataConfig:
    """Build a small, example-friendly Socrata config."""
    return nyc311.SocrataConfig(
        app_token=app_token,
        page_size=page_size,
        max_pages=max_pages,
    )
