"""Closed-date coverage — issue #20.

The `closed_date` field shipped in v1.0.1 so resolution-time analyses
don't have to bypass the SDK. These tests cover the four pipelines
the bulk_fetch → analysis round-trip touches:

1. `ServiceRequestRecord` constructor accepts closed_date and defaults
   to ``None`` for unresolved complaints.
2. Socrata `$select` string includes `closed_date` and the normalizer
   tolerates its absence from a row.
3. CSV ingest / export preserves `closed_date` (both the ISO date
   string and the empty-string-for-None convention).
4. DataFrame round-trip preserves the column, datetime dtype, and NaT
   ↔ None bridging.
"""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from nyc311.export._csv import export_service_requests_csv
from nyc311.io._cache import cached_fetch
from nyc311.io._csv import (
    _parse_optional_date,
    _parse_optional_datetime,
    _record_from_mapping,
    load_service_requests_from_csv,
)
from nyc311.io._socrata import _normalize_socrata_row, _socrata_select_fields
from nyc311.models import (
    ExportTarget,
    ServiceRequestFilter,
    ServiceRequestRecord,
    SocrataConfig,
)

# ---------------------------------------------------------------------------
# 1. Record model
# ---------------------------------------------------------------------------


def test_record_defaults_closed_date_to_none() -> None:
    record = ServiceRequestRecord(
        service_request_id="SR-NULL",
        created_date=date(2025, 1, 1),
        complaint_type="Rodent",
        descriptor="Rat sighting",
        borough="BRONX",
        community_district="BRONX 01",
    )
    assert record.closed_date is None


def test_record_resolution_latency_in_days() -> None:
    record = ServiceRequestRecord(
        service_request_id="SR-CLOSED",
        created_date=date(2025, 1, 1),
        complaint_type="Rodent",
        descriptor="Rat sighting",
        borough="BRONX",
        community_district="BRONX 01",
        resolution_description="Inspected",
        closed_date=date(2025, 1, 9),
    )
    assert record.closed_date is not None
    assert (record.closed_date - record.created_date).days == 8


# ---------------------------------------------------------------------------
# 2. Socrata select + normalizer
# ---------------------------------------------------------------------------


def test_socrata_select_includes_closed_date() -> None:
    assert "closed_date" in _socrata_select_fields()


def test_socrata_normalizer_tolerates_missing_closed_date() -> None:
    row: dict[str, object] = {
        "unique_key": "SR-MISSING",
        "created_date": "2025-01-01T00:00:00.000",
        # closed_date omitted — Socrata returns null for unresolved
        "complaint_type": "Rodent",
        "descriptor": "Rat sighting",
        "borough": "BRONX",
        "community_board": "BRONX 01",
    }
    normalized = _normalize_socrata_row(row)
    assert "closed_date" not in normalized


def test_socrata_normalizer_passes_through_closed_date() -> None:
    row: dict[str, object] = {
        "unique_key": "SR-CLOSED",
        "created_date": "2025-01-01T00:00:00.000",
        "closed_date": "2025-01-09T08:15:00.000",
        "complaint_type": "Rodent",
        "descriptor": "Rat sighting",
        "borough": "BRONX",
        "community_board": "BRONX 01",
    }
    normalized = _normalize_socrata_row(row)
    assert normalized["closed_date"] == "2025-01-09T08:15:00.000"


# ---------------------------------------------------------------------------
# 3. CSV ingest / export
# ---------------------------------------------------------------------------


def test_parse_optional_date_roundtrip() -> None:
    assert _parse_optional_date(None) is None
    assert _parse_optional_date("") is None
    assert _parse_optional_date("   ") is None
    assert _parse_optional_date("2025-01-09") == date(2025, 1, 9)
    assert _parse_optional_date("2025-01-09T08:15:00.000Z") == date(2025, 1, 9)


def test_record_from_mapping_handles_closed_date_column() -> None:
    row = {
        "unique_key": "SR-CLOSED",
        "created_date": "2025-01-01",
        "closed_date": "2025-01-09",
        "complaint_type": "Rodent",
        "descriptor": "Rat sighting",
        "borough": "BRONX",
        "community_board": "BRONX 01",
    }
    record = _record_from_mapping(row, community_district_column="community_board")
    assert record.closed_date == date(2025, 1, 9)


def test_record_from_mapping_without_closed_date_column() -> None:
    row = {
        "unique_key": "SR-OPEN",
        "created_date": "2025-01-01",
        "complaint_type": "Rodent",
        "descriptor": "Rat sighting",
        "borough": "BRONX",
        "community_board": "BRONX 01",
    }
    record = _record_from_mapping(row, community_district_column="community_board")
    assert record.closed_date is None


def test_csv_export_emits_closed_date_column(tmp_path: Path) -> None:
    records = [
        ServiceRequestRecord(
            service_request_id="SR-1",
            created_date=date(2025, 1, 1),
            complaint_type="Rodent",
            descriptor="Rat",
            borough="BRONX",
            community_district="BRONX 01",
            closed_date=date(2025, 1, 9),
        ),
        ServiceRequestRecord(
            service_request_id="SR-2",
            created_date=date(2025, 1, 2),
            complaint_type="Rodent",
            descriptor="Rat",
            borough="BRONX",
            community_district="BRONX 01",
            # closed_date intentionally omitted — unresolved
        ),
    ]
    output_path = tmp_path / "export.csv"
    export_service_requests_csv(records, ExportTarget("csv", output_path))

    with output_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert "closed_date" in rows[0]
    assert rows[0]["closed_date"] == "2025-01-09"
    assert rows[1]["closed_date"] == ""


def test_csv_round_trip_preserves_closed_date(tmp_path: Path) -> None:
    original = [
        ServiceRequestRecord(
            service_request_id="SR-1",
            created_date=date(2025, 1, 1),
            complaint_type="Rodent",
            descriptor="Rat",
            borough="BRONX",
            community_district="BRONX 01",
            closed_date=date(2025, 1, 9),
        ),
        ServiceRequestRecord(
            service_request_id="SR-2",
            created_date=date(2025, 1, 2),
            complaint_type="Rodent",
            descriptor="Rat",
            borough="BRONX",
            community_district="BRONX 01",
        ),
    ]
    csv_path = tmp_path / "round_trip.csv"
    export_service_requests_csv(original, ExportTarget("csv", csv_path))

    loaded = load_service_requests_from_csv(csv_path, filters=ServiceRequestFilter())

    assert loaded == original
    assert loaded[0].closed_date == date(2025, 1, 9)
    assert loaded[1].closed_date is None


# ---------------------------------------------------------------------------
# 3b. Full-precision timestamps (v1.0.4) — regression for the cold-run
#     bug where bulk CSVs shipped an empty closed_date column and
#     truncated created/closed to whole days (resolution-time -> NaT / days).
# ---------------------------------------------------------------------------


def test_parse_optional_datetime_only_when_time_component() -> None:
    assert _parse_optional_datetime(None) is None
    assert _parse_optional_datetime("") is None
    assert _parse_optional_datetime("   ") is None
    # bare date -> None so the day-grain *_date fields stay authoritative
    assert _parse_optional_datetime("2025-01-09") is None
    # ISO T separator
    assert _parse_optional_datetime("2025-01-09T08:15:00.000") == datetime(
        2025, 1, 9, 8, 15
    )
    # trailing Z tolerated
    assert _parse_optional_datetime("2025-01-09T08:15:00.000Z") == datetime(
        2025, 1, 9, 8, 15
    )
    # space separator
    assert _parse_optional_datetime("2025-01-09 08:15:00") == datetime(
        2025, 1, 9, 8, 15
    )


def test_record_from_mapping_captures_hour_precision() -> None:
    row = {
        "unique_key": "SR-TS",
        "created_date": "2025-01-01T09:00:00.000",
        "closed_date": "2025-01-01T14:30:00.000",
        "complaint_type": "Noise - Residential",
        "descriptor": "Loud Music/Party",
        "borough": "BRONX",
        "community_board": "BRONX 01",
    }
    record = _record_from_mapping(row, community_district_column="community_board")
    # day-grain fields stay authoritative and backward-compatible
    assert record.created_date == date(2025, 1, 1)
    assert record.closed_date == date(2025, 1, 1)
    # full-precision timestamps carry the time component
    assert record.created_at == datetime(2025, 1, 1, 9, 0)
    assert record.closed_at == datetime(2025, 1, 1, 14, 30)
    # resolution time is 5.5 hours, not 0 days
    assert (record.closed_at - record.created_at).total_seconds() / 3600 == 5.5


def test_record_from_mapping_date_only_leaves_timestamps_none() -> None:
    row = {
        "unique_key": "SR-DAY",
        "created_date": "2025-01-01",
        "closed_date": "2025-01-09",
        "complaint_type": "Rodent",
        "descriptor": "Rat sighting",
        "borough": "BRONX",
        "community_board": "BRONX 01",
    }
    record = _record_from_mapping(row, community_district_column="community_board")
    assert record.created_at is None
    assert record.closed_at is None
    assert record.created_date == date(2025, 1, 1)
    assert record.closed_date == date(2025, 1, 9)


def _timestamped_records() -> list[ServiceRequestRecord]:
    """Records as the Socrata loader builds them — full timestamps."""
    return [
        _record_from_mapping(
            {
                "unique_key": "SR-1",
                "created_date": "2024-01-01T09:00:00.000",
                "closed_date": "2024-01-01T15:00:00.000",
                "complaint_type": "Noise - Residential",
                "descriptor": "Loud Music/Party",
                "borough": "BROOKLYN",
                "community_board": "BROOKLYN 03",
            },
            community_district_column="community_board",
        ),
        _record_from_mapping(
            {
                "unique_key": "SR-2",
                "created_date": "2024-01-02T10:00:00.000",
                # unresolved — no closed_date
                "complaint_type": "Noise - Street/Sidewalk",
                "descriptor": "Loud Talking",
                "borough": "BROOKLYN",
                "community_board": "BROOKLYN 03",
            },
            community_district_column="community_board",
        ),
    ]


def test_cached_fetch_writes_populated_closed_date_with_timestamps(
    tmp_path: Path,
) -> None:
    """Regression: bulk cache CSVs must carry closed_date at hour grain."""
    cfg = SocrataConfig(page_size=10, max_pages=1)
    flt = ServiceRequestFilter()
    recs = _timestamped_records()

    def fake_iter(*_args, **_kwargs):
        yield from recs

    with patch(
        "nyc311.io._cache.iter_service_requests_from_socrata", side_effect=fake_iter
    ):
        out = cached_fetch(cfg, flt, cache_dir=tmp_path, refresh=True)

    with out.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # closed_date column is present AND populated at full precision
    assert rows[0]["closed_date"] == "2024-01-01T15:00:00"
    assert rows[0]["created_date"] == "2024-01-01T09:00:00"
    # unresolved complaint keeps the empty-string convention
    assert rows[1]["closed_date"] == ""

    # and the CSV round-trips back into records with real resolution time
    reloaded = load_service_requests_from_csv(out, filters=ServiceRequestFilter())
    assert reloaded[0].closed_at is not None
    assert reloaded[0].created_at is not None
    delta_hours = (
        reloaded[0].closed_at - reloaded[0].created_at
    ).total_seconds() / 3600
    assert delta_hours == 6.0
    assert reloaded[1].closed_at is None


def test_csv_export_preserves_hour_precision(tmp_path: Path) -> None:
    records = _timestamped_records()
    output_path = tmp_path / "export.csv"
    export_service_requests_csv(records, ExportTarget("csv", output_path))

    with output_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert rows[0]["created_date"] == "2024-01-01T09:00:00"
    assert rows[0]["closed_date"] == "2024-01-01T15:00:00"
    assert rows[1]["closed_date"] == ""


# ---------------------------------------------------------------------------
# 4. DataFrame round-trip
# ---------------------------------------------------------------------------


@pytest.mark.optional
def test_dataframe_round_trip_preserves_closed_date() -> None:
    pd = pytest.importorskip("pandas")
    from nyc311.dataframes import dataframe_to_records, records_to_dataframe

    original = [
        ServiceRequestRecord(
            service_request_id="SR-1",
            created_date=date(2025, 1, 1),
            complaint_type="Rodent",
            descriptor="Rat",
            borough="BRONX",
            community_district="BRONX 01",
            closed_date=date(2025, 1, 9),
        ),
        ServiceRequestRecord(
            service_request_id="SR-2",
            created_date=date(2025, 1, 2),
            complaint_type="Rodent",
            descriptor="Rat",
            borough="BRONX",
            community_district="BRONX 01",
        ),
    ]

    df = records_to_dataframe(original)
    assert "closed_date" in df.columns
    assert str(df["closed_date"].dtype).startswith("datetime64")
    # NaT bridges back to Python None on the round-trip.
    assert pd.isna(df["closed_date"].iloc[1])

    round_tripped = dataframe_to_records(df)
    assert round_tripped == original
