"""Normalization helpers for packaged NYC geography layers and values."""

from __future__ import annotations

import re
from collections.abc import Iterable

from ..models import normalize_borough_name

_COMMUNITY_DISTRICT_TOKEN_RE = re.compile(
    r"^(?:(?P<borough>[A-Z ]+?)\s+(?P<number>\d{1,2})|(?P<number_first>\d{1,2})\s+(?P<borough_last>[A-Z ]+))$"
)
_ZCTA_RE = re.compile(r"(\d{5})")
_COUNCIL_DISTRICT_RE = re.compile(r"(\d{1,2})")
_NTA_CODE_RE = re.compile(r"([A-Z]{2}\d{4})")
_COUNTY_FIPS_BY_BOROUGH_CODE = {
    "1": "061",
    "2": "005",
    "3": "047",
    "4": "081",
    "5": "085",
}
_LAYER_ALIASES = {
    "borough": "borough",
    "boroughs": "borough",
    "boro": "borough",
    "boros": "borough",
    "community_district": "community_district",
    "community_districts": "community_district",
    "community_board": "community_district",
    "community_boards": "community_district",
    "cd": "community_district",
    "council_district": "council_district",
    "council_districts": "council_district",
    "city_council_district": "council_district",
    "city_council_districts": "council_district",
    "council": "council_district",
    "councils": "council_district",
    "city_council": "council_district",
    "city_councils": "council_district",
    "zcta": "zcta",
    "zcta5": "zcta",
    "zip": "zcta",
    "zip_code": "zcta",
    "zip_codes": "zcta",
    "zipcode": "zcta",
    "zipcodes": "zcta",
    "modzcta": "zcta",
    "neighborhood_tabulation_area": "neighborhood_tabulation_area",
    "neighborhood_tabulation_areas": "neighborhood_tabulation_area",
    "nta": "neighborhood_tabulation_area",
    "nta2020": "neighborhood_tabulation_area",
    "neighborhood": "neighborhood_tabulation_area",
    "neighborhoods": "neighborhood_tabulation_area",
    "census_tract": "census_tract",
    "census_tracts": "census_tract",
    "tract": "census_tract",
    "tracts": "census_tract",
}


def _normalize_space(value: str) -> str:
    return " ".join(value.strip().replace("-", " ").replace("_", " ").split())


def normalize_boundary_layer(layer: str) -> str:
    """Normalize a user-facing boundary layer identifier to the canonical key."""
    normalized = _normalize_space(layer).casefold().replace(" ", "_")
    canonical = _LAYER_ALIASES.get(normalized)
    if canonical is None:
        supported = ", ".join(
            sorted(
                {
                    "borough",
                    "community_district",
                    "council_district",
                    "neighborhood_tabulation_area",
                    "zcta",
                    "census_tract",
                }
            )
        )
        raise ValueError(
            f"Unsupported boundary layer. Expected one of {supported}, got {layer!r}."
        )
    return canonical


def normalize_boundary_value(layer: str, value: str) -> str:
    """Normalize one boundary value for a packaged NYC boundary layer."""
    normalized_layer = normalize_boundary_layer(layer)
    normalized_value = _normalize_space(value)
    if not normalized_value:
        raise ValueError("Boundary values must not be empty.")

    if normalized_layer == "borough":
        return normalize_borough_name(normalized_value)

    if normalized_layer == "community_district":
        upper_value = (
            normalized_value.upper()
            .replace("COMMUNITY DISTRICT", " ")
            .replace("COMMUNITY BOARD", " ")
            .replace("DISTRICT", " ")
            .replace("BOARD", " ")
        )
        upper_value = _normalize_space(upper_value)
        match = _COMMUNITY_DISTRICT_TOKEN_RE.fullmatch(upper_value)
        if match is None:
            raise ValueError(
                "Community district values must look like 'BROOKLYN 01', "
                f"'01 BROOKLYN', or a borough alias plus a district number. Got {value!r}."
            )

        borough_token = match.group("borough") or match.group("borough_last")
        number_token = match.group("number") or match.group("number_first")
        if borough_token is None or number_token is None:
            raise ValueError(
                "Community district values must include both a borough and "
                f"a district number. Got {value!r}."
            )
        district_number = int(number_token)
        if not 1 <= district_number <= 18:
            raise ValueError(
                "Community district numbers must fall between 1 and 18. "
                f"Got {district_number!r} from {value!r}."
            )
        borough = normalize_borough_name(borough_token)
        return f"{borough} {district_number:02d}"

    matches = _ZCTA_RE.findall(normalized_value)
    if normalized_layer == "zcta":
        if len(matches) != 1:
            raise ValueError(
                f"ZCTA values must contain exactly one 5-digit ZIP code. Got {value!r}."
            )
        return matches[0]

    if normalized_layer == "council_district":
        council_matches = _COUNCIL_DISTRICT_RE.findall(normalized_value)
        if len(council_matches) != 1:
            raise ValueError(
                "Council district values must contain exactly one district number. "
                f"Got {value!r}."
            )
        district_number = int(council_matches[0])
        if not 1 <= district_number <= 51:
            raise ValueError(
                "Council district numbers must fall between 1 and 51. "
                f"Got {district_number!r} from {value!r}."
            )
        return f"{district_number:02d}"

    if normalized_layer == "neighborhood_tabulation_area":
        compact_value = re.sub(r"[^A-Z0-9]", "", normalized_value.upper())
        match = _NTA_CODE_RE.fullmatch(compact_value)
        if match is None:
            raise ValueError(
                "Neighborhood tabulation area values must look like 'BK0101'. "
                f"Got {value!r}."
            )
        return match.group(1)

    tract_code = re.sub(r"[^0-9]", "", normalized_value)
    if len(tract_code) not in {7, 11}:
        raise ValueError(
            "Census tract values must contain exactly one 7-digit borough tract code "
            f"or 11-digit GEOID. Got {value!r}."
        )
    if len(tract_code) == 11:
        return tract_code

    borough_code = tract_code[0]
    county_fips = _COUNTY_FIPS_BY_BOROUGH_CODE.get(borough_code)
    if county_fips is None:
        raise ValueError(
            "7-digit census tract values must start with a valid borough code 1-5. "
            f"Got {value!r}."
        )
    return f"36{county_fips}{tract_code[1:]}"


def normalize_boundary_values(
    layer: str, values: str | Iterable[str] | None
) -> tuple[str, ...] | None:
    """Normalize and de-duplicate one or more boundary values."""
    if values is None:
        return None

    raw_values = (values,) if isinstance(values, str) else tuple(values)
    if not raw_values:
        return None

    normalized_values = [
        normalize_boundary_value(layer, value)
        for value in raw_values
        if _normalize_space(value)
    ]
    if not normalized_values:
        return None
    return tuple(dict.fromkeys(normalized_values))
