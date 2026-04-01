from __future__ import annotations

import csv
import json
from pathlib import Path

from nyc311.pipeline import run_topic_pipeline

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "service_requests_fixture.csv"
BOUNDARIES_PATH = (
    Path(__file__).parent / "fixtures" / "community_district_boundaries.geojson"
)


def test_run_topic_pipeline_returns_summaries_without_export() -> None:
    summary = run_topic_pipeline(
        FIXTURE_PATH,
        "Noise - Residential",
        geography="community_district",
    )

    assert summary
    assert summary[0].geography == "community_district"
    assert summary[0].complaint_type == "Noise - Residential"


def test_run_topic_pipeline_exports_csv_when_output_is_provided(tmp_path: Path) -> None:
    output_path = tmp_path / "pipeline-output.csv"

    summary = run_topic_pipeline(
        FIXTURE_PATH,
        "Noise - Residential",
        geography="community_district",
        output=output_path,
    )

    assert summary
    assert output_path.exists()

    with output_path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows[0]["topic"] == "banging"


def test_run_topic_pipeline_exports_geojson(tmp_path: Path) -> None:
    output_path = tmp_path / "pipeline-output.geojson"

    summary = run_topic_pipeline(
        FIXTURE_PATH,
        "Noise - Residential",
        geography="community_district",
        output_format="geojson",
        boundaries=BOUNDARIES_PATH,
        output=output_path,
    )

    assert summary
    assert output_path.exists()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["type"] == "FeatureCollection"
