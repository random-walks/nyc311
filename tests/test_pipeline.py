from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

from nyc311.models import ServiceRequestRecord
from nyc311.pipeline import bulk_fetch, run_topic_pipeline

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


# ---------------------------------------------------------------------------
# bulk_fetch
# ---------------------------------------------------------------------------


def _bulk_records(borough: str) -> list[ServiceRequestRecord]:
    return [
        ServiceRequestRecord(
            service_request_id=f"{borough}-1",
            created_date=date(2024, 1, 1),
            complaint_type="Noise - Residential",
            descriptor="loud music",
            borough=borough,
            community_district=f"03 {borough}",
        ),
    ]


def test_bulk_fetch_writes_one_csv_per_borough(tmp_path: Path) -> None:
    captured_filters: list[tuple[str, str | None]] = []

    def fake_iter(_config, filters, **_kwargs):
        borough = filters.geography.value if filters.geography else "ALL"
        captured_filters.append(
            (borough, filters.start_date.isoformat() if filters.start_date else None),
        )
        yield from _bulk_records(borough)

    with patch(
        "nyc311.io._cache.iter_service_requests_from_socrata", side_effect=fake_iter
    ):
        paths = bulk_fetch(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            cache_dir=tmp_path,
        )

    assert len(paths) == 5  # one CSV per borough
    boroughs = {b for b, _ in captured_filters}
    assert boroughs == {"BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND"}

    for csv_path in paths:
        assert csv_path.exists()
        text = csv_path.read_text(encoding="utf-8")
        assert "unique_key" in text
        meta_path = csv_path.with_suffix(".meta.json")
        assert meta_path.exists()
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert meta["record_count"] == 1
        assert meta["sha256"]
        assert meta["start_date"] == "2024-01-01"


def test_bulk_fetch_accepts_iso_string_dates(tmp_path: Path) -> None:
    def fake_iter(_config, filters, **_kwargs):
        yield from _bulk_records(
            filters.geography.value if filters.geography else "ALL"
        )

    with patch(
        "nyc311.io._cache.iter_service_requests_from_socrata", side_effect=fake_iter
    ):
        paths = bulk_fetch(
            start_date="2024-01-01",
            end_date="2024-01-31",
            cache_dir=tmp_path,
            boroughs=("BROOKLYN",),
        )

    assert len(paths) == 1
    meta = json.loads(paths[0].with_suffix(".meta.json").read_text(encoding="utf-8"))
    assert meta["start_date"] == "2024-01-01"
    assert meta["end_date"] == "2024-01-31"


def test_bulk_fetch_invokes_progress_callback(tmp_path: Path) -> None:
    def fake_iter(_config, filters, **kwargs):
        on_page = kwargs.get("on_page")
        if on_page is not None:
            on_page(0, 1)
        yield from _bulk_records(
            filters.geography.value if filters.geography else "ALL"
        )

    progress_events: list[tuple[str, int, int]] = []

    with patch(
        "nyc311.io._cache.iter_service_requests_from_socrata", side_effect=fake_iter
    ):
        bulk_fetch(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            cache_dir=tmp_path,
            boroughs=("BROOKLYN", "QUEENS"),
            on_progress=lambda boro, page, rows: progress_events.append(
                (boro, page, rows)
            ),
        )

    assert sorted(e[0] for e in progress_events) == ["BROOKLYN", "QUEENS"]
    assert all(e[1] == 0 and e[2] == 1 for e in progress_events)


def test_bulk_fetch_skips_existing_borough_files(tmp_path: Path) -> None:
    # Pre-stage a complete file for BROOKLYN; bulk_fetch should not call iter
    # for that borough.
    from nyc311.io._cache import cache_path_for_request
    from nyc311.models import GeographyFilter, ServiceRequestFilter
    from nyc311.presets import large_socrata_config

    config = large_socrata_config(page_size=5_000)
    pre_filter = ServiceRequestFilter(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        geography=GeographyFilter(geography="borough", value="BROOKLYN"),
    )
    pre_path = cache_path_for_request(config, pre_filter, tmp_path)
    pre_path.parent.mkdir(parents=True, exist_ok=True)
    pre_path.write_text("unique_key\nseed\n", encoding="utf-8")

    seen_boroughs: list[str] = []

    def fake_iter(_config, filters, **_kwargs):
        borough = filters.geography.value if filters.geography else "ALL"
        seen_boroughs.append(borough)
        yield from _bulk_records(borough)

    with patch(
        "nyc311.io._cache.iter_service_requests_from_socrata", side_effect=fake_iter
    ):
        paths = bulk_fetch(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            cache_dir=tmp_path,
            boroughs=("BROOKLYN", "QUEENS"),
        )

    # BROOKLYN was cached; only QUEENS should hit the iterator.
    assert seen_boroughs == ["QUEENS"]
    assert len(paths) == 2
