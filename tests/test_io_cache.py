"""Tests for Socrata CSV caching."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch

from nyc311.io._cache import cache_path_for_request, cached_fetch
from nyc311.models import GeographyFilter, ServiceRequestFilter, SocrataConfig
from nyc311.models._records import ServiceRequestRecord


def _sample_records() -> list[ServiceRequestRecord]:
    return [
        ServiceRequestRecord(
            service_request_id="1",
            created_date=date(2024, 1, 1),
            complaint_type="Noise - Residential",
            descriptor="loud music",
            borough="BROOKLYN",
            community_district="03 BROOKLYN",
        ),
        ServiceRequestRecord(
            service_request_id="2",
            created_date=date(2024, 1, 2),
            complaint_type="Rodent",
            descriptor="rats",
            borough="BROOKLYN",
            community_district="03 BROOKLYN",
        ),
    ]


def test_cache_path_unfiltered() -> None:
    cfg = SocrataConfig(page_size=1000)
    flt = ServiceRequestFilter(
        start_date=date(2024, 1, 1), end_date=date(2024, 1, 31)
    )
    p = cache_path_for_request(cfg, flt, Path("/tmp/cache"))
    assert p.name == "all_2024-01-01_2024-01-31_1000.csv"


def test_cache_path_borough_and_types() -> None:
    cfg = SocrataConfig(page_size=50_000)
    flt = ServiceRequestFilter(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        geography=GeographyFilter("borough", "BROOKLYN"),
        complaint_types=("Noise - Residential",),
    )
    p = cache_path_for_request(cfg, flt, Path("/tmp/cache"))
    assert "brooklyn" in p.name
    assert "noise_residential" in p.name


def test_cache_path_desc_suffix() -> None:
    cfg = SocrataConfig(page_size=5_000, created_date_sort="desc")
    flt = ServiceRequestFilter(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        geography=GeographyFilter("borough", "BROOKLYN"),
    )
    p = cache_path_for_request(cfg, flt, Path("/tmp/cache"))
    assert p.name.endswith("_desc.csv")


def test_cached_fetch_skips_when_exists(tmp_path: Path) -> None:
    cfg = SocrataConfig(page_size=10, max_pages=1)
    flt = ServiceRequestFilter()
    target = cache_path_for_request(cfg, flt, tmp_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("x", encoding="utf-8")

    with patch("nyc311.io._cache.iter_service_requests_from_socrata") as mock_iter:
        out = cached_fetch(cfg, flt, cache_dir=tmp_path, refresh=False)
        mock_iter.assert_not_called()
    assert out == target


def test_cached_fetch_drops_stale_partial_without_final(tmp_path: Path) -> None:
    cfg = SocrataConfig(page_size=10, max_pages=1)
    flt = ServiceRequestFilter()
    target = cache_path_for_request(cfg, flt, tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    partial.write_text("stale", encoding="utf-8")

    recs = _sample_records()

    def fake_iter(*_args, **_kwargs):
        yield from recs

    with patch(
        "nyc311.io._cache.iter_service_requests_from_socrata", side_effect=fake_iter
    ):
        out = cached_fetch(cfg, flt, cache_dir=tmp_path, refresh=False)

    assert not partial.exists()
    text = out.read_text(encoding="utf-8")
    assert "unique_key" in text
    assert "1" in text


def test_cached_fetch_writes_rows(tmp_path: Path) -> None:
    cfg = SocrataConfig(page_size=10, max_pages=1)
    flt = ServiceRequestFilter()
    recs = _sample_records()

    def fake_iter(*_args, **_kwargs):
        yield from recs

    with patch(
        "nyc311.io._cache.iter_service_requests_from_socrata", side_effect=fake_iter
    ):
        out = cached_fetch(cfg, flt, cache_dir=tmp_path, refresh=True)

    text = out.read_text(encoding="utf-8")
    assert "unique_key" in text
    assert "1" in text
    assert "2" in text
