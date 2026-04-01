"""Reusable preset builders for common nyc311 example and workflow inputs."""

from __future__ import annotations

from datetime import date

from . import models


def _coerce_date(value: date | str) -> date:
    return value if isinstance(value, date) else date.fromisoformat(value)


def build_filter(
    *,
    start_date: date | str,
    end_date: date | str,
    geography: str = "borough",
    geography_value: str = models.BOROUGH_BROOKLYN,
    complaint_types: tuple[str, ...] = (),
) -> models.ServiceRequestFilter:
    """Build a typed service-request filter from string-friendly inputs."""
    return models.ServiceRequestFilter(
        start_date=_coerce_date(start_date),
        end_date=_coerce_date(end_date),
        geography=models.GeographyFilter(geography, geography_value),
        complaint_types=complaint_types,
    )


def brooklyn_borough_filter(
    *,
    start_date: date | str,
    end_date: date | str,
    complaint_types: tuple[str, ...] = (),
) -> models.ServiceRequestFilter:
    """Build a borough-level Brooklyn filter."""
    return build_filter(
        start_date=start_date,
        end_date=end_date,
        geography="borough",
        geography_value=models.BOROUGH_BROOKLYN,
        complaint_types=complaint_types,
    )


def manhattan_borough_filter(
    *,
    start_date: date | str,
    end_date: date | str,
    complaint_types: tuple[str, ...] = (),
) -> models.ServiceRequestFilter:
    """Build a borough-level Manhattan filter."""
    return build_filter(
        start_date=start_date,
        end_date=end_date,
        geography="borough",
        geography_value=models.BOROUGH_MANHATTAN,
        complaint_types=complaint_types,
    )


def small_socrata_config(
    *,
    page_size: int = 500,
    max_pages: int | None = 1,
    app_token: str | None = None,
) -> models.SocrataConfig:
    """Build a small Socrata config suited to examples and local iteration."""
    return models.SocrataConfig(
        app_token=app_token,
        page_size=page_size,
        max_pages=max_pages,
    )


__all__ = [
    "brooklyn_borough_filter",
    "build_filter",
    "manhattan_borough_filter",
    "small_socrata_config",
]
