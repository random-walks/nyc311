from __future__ import annotations

from typing import cast

import nyc311


def test_list_boundary_layers_reports_packaged_layers() -> None:
    assert nyc311.list_boundary_layers() == (
        "borough",
        "community_district",
        "council_district",
        "neighborhood_tabulation_area",
        "zcta",
        "census_tract",
    )


def test_load_nyc_boundaries_loads_full_packaged_community_district_layer() -> None:
    boundaries = nyc311.load_nyc_boundaries("community_district")

    assert boundaries.geography == "community_district"
    assert len(boundaries.features) == 59
    assert "BRONX 05" in {feature.geography_value for feature in boundaries.features}


def test_load_nyc_boundaries_filters_values_and_supports_zcta_aliases() -> None:
    boundaries = nyc311.load_nyc_boundaries("zip", values="MODZCTA 10001")

    assert boundaries.geography == "zcta"
    assert [feature.geography_value for feature in boundaries.features] == ["10001"]
    assert boundaries.features[0].properties["modzcta"] == "10001"


def test_specific_packaged_layer_loaders_work_for_remaining_layers() -> None:
    census_tracts = nyc311.load_nyc_census_tracts(values="1000100")
    ntas = nyc311.load_nyc_neighborhood_tabulation_areas(values="bk0101")
    council_districts = nyc311.load_nyc_council_districts(values="district 33")

    assert [feature.geography_value for feature in census_tracts.features] == [
        "36061000100"
    ]
    assert [feature.geography_value for feature in ntas.features] == ["BK0101"]
    assert [feature.geography_value for feature in council_districts.features] == ["33"]


def test_load_boundaries_accepts_packaged_layer_names() -> None:
    borough_boundaries = nyc311.load_boundaries("borough")

    assert borough_boundaries.geography == "borough"
    assert len(borough_boundaries.features) == 5


def test_sample_loaders_use_packaged_library_resources() -> None:
    records = nyc311.load_sample_service_requests()
    community_boundaries = nyc311.load_sample_boundaries("community_district")
    council_boundaries = nyc311.load_sample_boundaries("council_district")
    nta_boundaries = nyc311.load_sample_boundaries("neighborhood_tabulation_area")
    zcta_boundaries = nyc311.load_sample_boundaries("zcta")
    census_tract_boundaries = nyc311.load_sample_boundaries("census_tract")

    assert len(records) == 18
    assert {record.community_district for record in records} == {
        "BROOKLYN 01",
        "BROOKLYN 03",
        "MANHATTAN 10",
        "QUEENS 02",
        "BRONX 05",
    }
    assert {feature.geography_value for feature in community_boundaries.features} == {
        "BROOKLYN 01",
        "BROOKLYN 03",
        "MANHATTAN 10",
        "QUEENS 02",
        "BRONX 05",
    }
    assert {feature.geography_value for feature in zcta_boundaries.features} == {
        "10037",
        "10457",
        "11101",
        "11221",
        "11222",
    }
    assert {feature.geography_value for feature in council_boundaries.features} == {
        "09",
        "15",
        "22",
        "33",
        "36",
    }
    assert {feature.geography_value for feature in nta_boundaries.features} == {
        "BK0101",
        "BK0302",
        "BX0403",
        "MN1002",
        "QN0104",
    }
    assert {
        feature.geography_value for feature in census_tract_boundaries.features
    } == {
        "36005022703",
        "36047029500",
        "36047056500",
        "36061021200",
        "36081015900",
    }


def test_boundaries_to_geojson_preserves_feature_collection_shape() -> None:
    boundaries = nyc311.load_nyc_boundaries("borough", values="Queens")

    payload = nyc311.boundaries_to_geojson(boundaries)
    features = cast(list[dict[str, object]], payload["features"])
    properties = cast(dict[str, object], features[0]["properties"])

    assert payload["type"] == "FeatureCollection"
    assert len(features) == 1
    assert properties["geography_value"] == "QUEENS"
