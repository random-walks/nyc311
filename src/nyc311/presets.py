"""Reusable preset builders for common nyc311 example and workflow inputs."""

from __future__ import annotations

from datetime import date
from typing import Literal

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


def large_socrata_config(
    *,
    page_size: int = 5_000,
    max_pages: int | None = None,
    app_token: str | None = None,
    request_timeout_seconds: float = 300.0,
    created_date_sort: Literal["asc", "desc"] = "asc",
) -> models.SocrataConfig:
    """Build a high-throughput Socrata config for bulk downloads (e.g. full history).

    Default ``page_size`` is 5,000 rows per request so each HTTP round-trip stays
    smaller than very large pages, with a five-minute read timeout per request.
    Use ``created_date_sort='desc'`` when you want the most recent rows first
    (e.g. capped smoke samples).
    """
    return models.SocrataConfig(
        app_token=app_token,
        page_size=page_size,
        max_pages=max_pages,
        request_timeout_seconds=request_timeout_seconds,
        created_date_sort=created_date_sort,
    )


def smoke_socrata_config(
    *,
    page_size: int = 5_000,
    app_token: str | None = None,
    request_timeout_seconds: float = 120.0,
) -> models.SocrataConfig:
    """Small, recent-first Socrata config for quick multi-borough smoke downloads."""
    return models.SocrataConfig(
        app_token=app_token,
        page_size=page_size,
        max_pages=None,
        request_timeout_seconds=request_timeout_seconds,
        created_date_sort="desc",
    )


__all__ = [
    "brooklyn_borough_filter",
    "build_filter",
    "large_socrata_config",
    "manhattan_borough_filter",
    "smoke_socrata_config",
    "small_socrata_config",
]
