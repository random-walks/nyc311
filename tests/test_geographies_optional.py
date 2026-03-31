from __future__ import annotations

import pytest

import nyc311

pytest.importorskip(
    "geopandas",
    reason="Install nyc311[spatial] to run packaged geography geospatial tests.",
)
pytest.importorskip(
    "pandas",
    reason="Install nyc311[dataframes] or nyc311[science] to run boundary dataframe tests.",
)
pytest.importorskip(
    "shapely",
    reason="Install nyc311[spatial] to run packaged geography geospatial tests.",
)
pytestmark = pytest.mark.optional


def test_load_nyc_boundaries_geodataframe_reads_packaged_zcta_layer() -> None:
    boundaries_gdf = nyc311.load_nyc_boundaries_geodataframe(
        "zcta",
        values=("10001", "10002"),
    )

    assert len(boundaries_gdf) == 2
    assert set(boundaries_gdf["geography_value"]) == {"10001", "10002"}
    assert str(boundaries_gdf.crs) == "EPSG:4326"


def test_load_nyc_boundaries_geodataframe_supports_new_packaged_layers() -> None:
    nta_gdf = nyc311.load_nyc_boundaries_geodataframe(
        "neighborhood_tabulation_area",
        values=("BK0101",),
    )
    council_gdf = nyc311.load_nyc_boundaries_geodataframe(
        "council_district",
        values=("33",),
    )
    census_gdf = nyc311.load_nyc_boundaries_geodataframe(
        "census_tract",
        values=("36061000100",),
    )

    assert list(nta_gdf["geography_value"]) == ["BK0101"]
    assert list(council_gdf["geography_value"]) == ["33"]
    assert list(census_gdf["geography_value"]) == ["36061000100"]


def test_load_boundaries_geodataframe_accepts_boundary_collections() -> None:
    boundaries = nyc311.load_sample_boundaries("community_district")

    boundaries_gdf = nyc311.load_boundaries_geodataframe(boundaries)

    assert len(boundaries_gdf) == 5
    assert set(boundaries_gdf["geography_value"]) == {
        "BRONX 05",
        "BROOKLYN 01",
        "BROOKLYN 03",
        "MANHATTAN 10",
        "QUEENS 02",
    }


def test_boundaries_to_dataframe_returns_notebook_friendly_rows() -> None:
    dataframe = nyc311.boundaries_to_dataframe(
        nyc311.load_nyc_boundaries("borough", values=("Queens", "Brooklyn"))
    )

    assert list(dataframe["geography_value"]) == ["BROOKLYN", "QUEENS"]
    assert "geometry" in dataframe.columns


def test_clip_boundaries_to_bbox_returns_only_intersecting_boundaries() -> None:
    clipped = nyc311.clip_boundaries_to_bbox(
        nyc311.load_sample_boundaries("community_district"),
        min_longitude=-73.95,
        min_latitude=40.74,
        max_longitude=-73.89,
        max_latitude=40.78,
    )

    assert {feature.geography_value for feature in clipped.features} == {"QUEENS 02"}


def test_spatially_enrich_records_can_join_sample_records_to_zcta() -> None:
    records = nyc311.load_sample_service_requests()

    joined = nyc311.spatially_enrich_records(records, layer="zcta")

    assert joined["boundary_geography_value"].notna().all()
    assert set(joined["boundary_geography_value"]) == {
        "10037",
        "10457",
        "11101",
        "11221",
        "11222",
    }


def test_spatially_enrich_records_can_join_sample_records_to_new_layers() -> None:
    records = nyc311.load_sample_service_requests()

    nta_joined = nyc311.spatially_enrich_records(
        records,
        layer="neighborhood_tabulation_area",
    )
    council_joined = nyc311.spatially_enrich_records(records, layer="council_district")

    assert set(nta_joined["boundary_geography_value"]) == {
        "BK0101",
        "BK0302",
        "BX0403",
        "MN1002",
        "QN0104",
    }
    assert set(council_joined["boundary_geography_value"]) == {
        "09",
        "15",
        "22",
        "33",
        "36",
    }
