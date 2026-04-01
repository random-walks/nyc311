"""Normalization helpers shared by public nyc311 models."""

from __future__ import annotations

import math

from ._constants import (
    _BOROUGH_ALIASES,
    _NYC_LATITUDE_RANGE,
    _NYC_LONGITUDE_RANGE,
    SUPPORTED_BOROUGHS,
)


def _normalize_value(value: str) -> str:
    """Normalize user- or file-provided string values."""
    return " ".join(value.strip().split())


def _normalize_borough_or_passthrough(value: str) -> str:
    """Normalize common borough aliases without rejecting unknown source values."""
    normalized = _normalize_value(value)
    if not normalized:
        return normalized

    return _BOROUGH_ALIASES.get(normalized.casefold(), normalized.upper())


def _coerce_optional_coordinate(value: object, *, name: str) -> float | None:
    """Normalize an optional coordinate value to a finite float."""
    if value is None:
        return None
    if isinstance(value, str):
        normalized_value = value.strip()
        if not normalized_value:
            return None
        value = normalized_value

    if not isinstance(value, (int, float, str)):
        raise ValueError(f"{name} must be numeric when provided.")

    try:
        coordinate = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric when provided.") from exc

    if not math.isfinite(coordinate):
        return None
    return coordinate


def _normalize_coordinate_pair(
    latitude: object, longitude: object
) -> tuple[float | None, float | None]:
    """Normalize an optional latitude/longitude pair for NYC point records."""
    normalized_latitude = _coerce_optional_coordinate(latitude, name="latitude")
    normalized_longitude = _coerce_optional_coordinate(longitude, name="longitude")

    if normalized_latitude is None and normalized_longitude is None:
        return None, None
    if normalized_latitude == 0 and normalized_longitude == 0:
        return None, None
    if normalized_latitude is None or normalized_longitude is None:
        raise ValueError("latitude and longitude must be provided together.")

    min_latitude, max_latitude = _NYC_LATITUDE_RANGE
    min_longitude, max_longitude = _NYC_LONGITUDE_RANGE
    if not min_latitude <= normalized_latitude <= max_latitude:
        raise ValueError(
            f"latitude must fall within the supported NYC bounds {_NYC_LATITUDE_RANGE}."
        )
    if not min_longitude <= normalized_longitude <= max_longitude:
        raise ValueError(
            "longitude must fall within the supported NYC bounds "
            f"{_NYC_LONGITUDE_RANGE}."
        )

    return normalized_latitude, normalized_longitude


def normalize_borough_name(value: str) -> str:
    """Normalize a borough name or borough alias to the canonical public constant."""
    normalized = _normalize_borough_or_passthrough(value)
    if normalized not in SUPPORTED_BOROUGHS:
        raise ValueError(
            "Unsupported borough name. "
            f"Expected one of {SUPPORTED_BOROUGHS}, got {value!r}."
        )
    return normalized
