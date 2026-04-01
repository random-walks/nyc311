from __future__ import annotations

import json
from pathlib import Path

import pytest

from nyc311.analysis import aggregate_by_geography, extract_topics
from nyc311.export import export_geojson
from nyc311.geographies import load_boundaries
from nyc311.io import load_service_requests
from nyc311.models import BoundaryGeoJSONExport, ExportTarget, TopicQuery

BOUNDARIES_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "community_district_boundaries.geojson"
)
SERVICE_REQUESTS_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "service_requests_fixture.csv"
)


def test_load_boundaries_reads_geojson_fixture() -> None:
    boundaries = load_boundaries(BOUNDARIES_FIXTURE_PATH)

    assert boundaries.geography == "community_district"
    assert len(boundaries.features) == 4
    assert boundaries.features[0].geography == "community_district"
    assert boundaries.features[0].geography_value == "BROOKLYN 01"
    assert boundaries.features[0].properties["name"] == "Brooklyn Community District 1"


def test_export_geojson_writes_feature_collection(tmp_path: Path) -> None:
    service_requests = load_service_requests(SERVICE_REQUESTS_FIXTURE_PATH)
    assignments = extract_topics(
        service_requests,
        TopicQuery(complaint_type="Noise - Residential"),
    )
    summaries = aggregate_by_geography(assignments, geography="community_district")
    boundaries = load_boundaries(BOUNDARIES_FIXTURE_PATH)

    output_path = tmp_path / "exports" / "noise_topics.geojson"
    written_path = export_geojson(
        BoundaryGeoJSONExport(boundaries=boundaries, summaries=tuple(summaries)),
        ExportTarget(format="geojson", output_path=output_path),
    )

    assert written_path == output_path

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["type"] == "FeatureCollection"
    assert len(payload["features"]) == 4

    brooklyn_feature = next(
        feature
        for feature in payload["features"]
        if feature["properties"]["geography_value"] == "BROOKLYN 01"
    )
    assert brooklyn_feature["properties"]["complaint_type"] == "Noise - Residential"
    assert brooklyn_feature["properties"]["dominant_topic"] == "banging"
    assert brooklyn_feature["properties"]["topic_count"] == 1


def test_export_geojson_requires_geojson_target(tmp_path: Path) -> None:
    boundaries = load_boundaries(BOUNDARIES_FIXTURE_PATH)
    output_path = tmp_path / "exports" / "invalid.json"

    with pytest.raises(ValueError, match="only GeoJSON output"):
        export_geojson(
            BoundaryGeoJSONExport(boundaries=boundaries, summaries=()),
            ExportTarget(format="json", output_path=output_path),
        )
