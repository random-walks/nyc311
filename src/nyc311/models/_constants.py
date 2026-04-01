"""Public constants and canonical value catalogs for nyc311 models."""

from __future__ import annotations

from typing import Final

BoroughName = str

SUPPORTED_RECORD_GEOGRAPHIES: Final[tuple[str, ...]] = ("borough", "community_district")
SUPPORTED_BOUNDARY_GEOGRAPHIES: Final[tuple[str, ...]] = (
    "borough",
    "community_district",
    "council_district",
    "neighborhood_tabulation_area",
    "census_tract",
    "zcta",
)
SUPPORTED_GEOGRAPHIES: Final[tuple[str, ...]] = SUPPORTED_RECORD_GEOGRAPHIES
SOCRATA_DATASET_IDENTIFIER: Final[str] = "erm2-nwe9"
BOROUGH_BRONX: Final[BoroughName] = "BRONX"
BOROUGH_BROOKLYN: Final[BoroughName] = "BROOKLYN"
BOROUGH_MANHATTAN: Final[BoroughName] = "MANHATTAN"
BOROUGH_QUEENS: Final[BoroughName] = "QUEENS"
BOROUGH_STATEN_ISLAND: Final[BoroughName] = "STATEN ISLAND"
SUPPORTED_BOROUGHS: Final[tuple[BoroughName, ...]] = (
    BOROUGH_BRONX,
    BOROUGH_BROOKLYN,
    BOROUGH_MANHATTAN,
    BOROUGH_QUEENS,
    BOROUGH_STATEN_ISLAND,
)
_BOROUGH_ALIASES: Final[dict[str, BoroughName]] = {
    "bronx": BOROUGH_BRONX,
    "bx": BOROUGH_BRONX,
    "brooklyn": BOROUGH_BROOKLYN,
    "bk": BOROUGH_BROOKLYN,
    "kings": BOROUGH_BROOKLYN,
    "manhattan": BOROUGH_MANHATTAN,
    "mn": BOROUGH_MANHATTAN,
    "new york": BOROUGH_MANHATTAN,
    "new york county": BOROUGH_MANHATTAN,
    "queens": BOROUGH_QUEENS,
    "qn": BOROUGH_QUEENS,
    "staten island": BOROUGH_STATEN_ISLAND,
    "si": BOROUGH_STATEN_ISLAND,
    "richmond": BOROUGH_STATEN_ISLAND,
}
_NYC_LATITUDE_RANGE: Final[tuple[float, float]] = (40.4, 41.0)
_NYC_LONGITUDE_RANGE: Final[tuple[float, float]] = (-74.3, -73.6)
_SUPPORTED_TOPIC_QUERIES: Final[tuple[str, ...]] = (
    "Abandoned Vehicle",
    "Blocked Driveway",
    "HEAT/HOT WATER",
    "Illegal Parking",
    "Noise - Residential",
    "Noise - Street/Sidewalk",
    "Rodent",
    "Street Condition",
    "UNSANITARY CONDITION",
)


def supported_topic_queries() -> tuple[str, ...]:
    """Return the complaint types with implemented topic extraction."""
    return _SUPPORTED_TOPIC_QUERIES
