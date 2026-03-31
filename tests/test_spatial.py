from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

import nyc311

pytest.importorskip(
    "geopandas",
    reason="Install nyc311[spatial] to run geospatial helper tests.",
)
pytest.importorskip(
    "shapely",
    reason="Install nyc311[spatial] to run geospatial helper tests.",
)
pytestmark = pytest.mark.optional

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "service_requests_fixture.csv"
BOUNDARIES_PATH = (
    Path(__file__).parent / "fixtures" / "community_district_boundaries.geojson"
)


def test_records_to_geodataframe_keeps_only_records_with_coordinates() -> None:
    records = nyc311.load_service_requests(FIXTURE_PATH)
    records.append(
        nyc311.ServiceRequestRecord(
            service_request_id="missing-point",
            created_date=date(2025, 4, 1),
            complaint_type="Rodent",
            descriptor="Missing coordinates",
            borough=nyc311.BOROUGH_BROOKLYN,
            community_district="BROOKLYN 01",
        )
    )

    records_gdf = nyc311.records_to_geodataframe(records)

    assert len(records_gdf) == 18
    assert str(records_gdf.crs) == "EPSG:4326"
    assert "geometry" in records_gdf.columns


def test_load_boundaries_geodataframe_reads_geojson_fixture() -> None:
    boundaries_gdf = nyc311.load_boundaries_geodataframe(BOUNDARIES_PATH)

    assert len(boundaries_gdf) == 4
    assert set(boundaries_gdf["geography_value"]) == {
        "BROOKLYN 01",
        "BROOKLYN 03",
        "MANHATTAN 10",
        "QUEENS 02",
    }


def test_spatial_join_records_to_boundaries_assigns_boundary_columns() -> None:
    records_gdf = nyc311.records_to_geodataframe(nyc311.load_service_requests(FIXTURE_PATH))
    boundaries_gdf = nyc311.load_boundaries_geodataframe(BOUNDARIES_PATH)

    joined = nyc311.spatial_join_records_to_boundaries(records_gdf, boundaries_gdf)

    assert "boundary_geography_value" in joined.columns
    assert (
        joined.loc[joined["service_request_id"] == "1001", "boundary_geography_value"]
        .iat[0]
        == "BROOKLYN 01"
    )
    assert joined.loc[
        joined["service_request_id"] == "1016", "boundary_geography_value"
    ].isna().all()


def test_summaries_to_geodataframe_merges_summary_rows_onto_boundaries() -> None:
    records = nyc311.load_service_requests(FIXTURE_PATH)
    assignments = nyc311.extract_topics(
        records,
        nyc311.TopicQuery("Noise - Residential"),
    )
    summaries = nyc311.aggregate_by_geography(
        assignments,
        geography="community_district",
    )
    boundaries_gdf = nyc311.load_boundaries_geodataframe(BOUNDARIES_PATH)

    summary_gdf = nyc311.summaries_to_geodataframe(summaries, boundaries_gdf)

    assert "topic" in summary_gdf.columns
    assert summary_gdf["geometry"].notna().all()
    assert {
        *summary_gdf.loc[
            summary_gdf["geography_value"] == "BROOKLYN 01",
            "topic",
        ]
        .dropna()
        .tolist()
    } == {"banging", "party_music"}
