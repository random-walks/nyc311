"""Tests for the composable factor pipeline."""

from __future__ import annotations

from datetime import date

import pytest

from nyc311.factors import (
    AnomalyScoreFactor,
    ComplaintVolumeFactor,
    EquityGapFactor,
    FactorContext,
    Pipeline,
    PipelineResult,
    RecurrenceFactor,
    ResolutionTimeFactor,
    ResponseRateFactor,
    SeasonalityFactor,
    SpatialLagFactor,
    TopicConcentrationFactor,
)
from nyc311.models import ServiceRequestRecord

# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------


def _make_record(
    *,
    service_request_id: str = "SR-001",
    created_date: date = date(2024, 6, 15),
    complaint_type: str = "Noise - Residential",
    descriptor: str = "Loud Music/Party",
    borough: str = "BROOKLYN",
    community_district: str = "BROOKLYN 01",
    resolution_description: str | None = None,
    latitude: float | None = 40.6782,
    longitude: float | None = -73.9442,
) -> ServiceRequestRecord:
    return ServiceRequestRecord(
        service_request_id=service_request_id,
        created_date=created_date,
        complaint_type=complaint_type,
        descriptor=descriptor,
        borough=borough,
        community_district=community_district,
        resolution_description=resolution_description,
        latitude=latitude,
        longitude=longitude,
    )


def _make_context(
    *,
    complaints: tuple[ServiceRequestRecord, ...] | None = None,
    geography: str = "community_district",
    geography_value: str = "BROOKLYN 01",
    time_window_start: date = date(2024, 6, 1),
    time_window_end: date = date(2024, 6, 30),
    total_population: int | None = 100_000,
    extras: dict | None = None,
) -> FactorContext:
    if complaints is None:
        complaints = (_make_record(),)
    return FactorContext(
        geography=geography,
        geography_value=geography_value,
        complaints=complaints,
        time_window_start=time_window_start,
        time_window_end=time_window_end,
        total_population=total_population,
        extras=extras,
    )


# ---------------------------------------------------------------------------
# FactorContext
# ---------------------------------------------------------------------------


class TestFactorContext:
    def test_frozen(self) -> None:
        ctx = _make_context()
        with pytest.raises(AttributeError):
            ctx.geography = "borough"  # type: ignore[misc]

    def test_fields(self) -> None:
        ctx = _make_context()
        assert ctx.geography == "community_district"
        assert ctx.geography_value == "BROOKLYN 01"
        assert len(ctx.complaints) == 1
        assert ctx.total_population == 100_000

    def test_empty_complaints(self) -> None:
        ctx = _make_context(complaints=())
        assert len(ctx.complaints) == 0


# ---------------------------------------------------------------------------
# ComplaintVolumeFactor
# ---------------------------------------------------------------------------


class TestComplaintVolumeFactor:
    def test_raw_count(self) -> None:
        records = tuple(_make_record(service_request_id=f"SR-{i}") for i in range(5))
        ctx = _make_context(complaints=records)
        result = ComplaintVolumeFactor().compute(ctx)
        assert result == 5

    def test_per_capita(self) -> None:
        records = tuple(_make_record(service_request_id=f"SR-{i}") for i in range(10))
        ctx = _make_context(complaints=records, total_population=50_000)
        result = ComplaintVolumeFactor(per_capita=True).compute(ctx)
        assert result == pytest.approx(2.0)  # 10 / 50000 * 10000

    def test_per_capita_no_population(self) -> None:
        records = tuple(_make_record(service_request_id=f"SR-{i}") for i in range(10))
        ctx = _make_context(complaints=records, total_population=None)
        result = ComplaintVolumeFactor(per_capita=True).compute(ctx)
        assert result == 10  # falls back to raw count

    def test_empty(self) -> None:
        ctx = _make_context(complaints=())
        assert ComplaintVolumeFactor().compute(ctx) == 0


# ---------------------------------------------------------------------------
# ResolutionTimeFactor
# ---------------------------------------------------------------------------


class TestResolutionTimeFactor:
    def test_median(self) -> None:
        records = (
            _make_record(
                service_request_id="SR-1",
                created_date=date(2024, 6, 10),
                resolution_description="Fixed",
            ),
            _make_record(
                service_request_id="SR-2",
                created_date=date(2024, 6, 20),
                resolution_description="Resolved",
            ),
        )
        ctx = _make_context(
            complaints=records,
            time_window_end=date(2024, 6, 30),
        )
        result = ResolutionTimeFactor().compute(ctx)
        # Days: (30-10)=20, (30-20)=10 -> median = 15
        assert result == pytest.approx(15.0)

    def test_mean(self) -> None:
        records = (
            _make_record(
                service_request_id="SR-1",
                created_date=date(2024, 6, 10),
                resolution_description="Fixed",
            ),
            _make_record(
                service_request_id="SR-2",
                created_date=date(2024, 6, 20),
                resolution_description="Resolved",
            ),
        )
        ctx = _make_context(
            complaints=records,
            time_window_end=date(2024, 6, 30),
        )
        result = ResolutionTimeFactor(method="mean").compute(ctx)
        assert result == pytest.approx(15.0)

    def test_no_resolved(self) -> None:
        ctx = _make_context(complaints=(_make_record(),))
        assert ResolutionTimeFactor().compute(ctx) == -1.0

    def test_invalid_method(self) -> None:
        with pytest.raises(ValueError, match="method must be"):
            ResolutionTimeFactor(method="mode")

    def test_empty(self) -> None:
        ctx = _make_context(complaints=())
        assert ResolutionTimeFactor().compute(ctx) == -1.0


# ---------------------------------------------------------------------------
# TopicConcentrationFactor
# ---------------------------------------------------------------------------


class TestTopicConcentrationFactor:
    def test_single_type(self) -> None:
        records = tuple(_make_record(service_request_id=f"SR-{i}") for i in range(3))
        ctx = _make_context(complaints=records)
        # All same type -> HHI = 1.0
        assert TopicConcentrationFactor().compute(ctx) == pytest.approx(1.0)

    def test_uniform_distribution(self) -> None:
        records = (
            _make_record(
                service_request_id="SR-1", complaint_type="Noise - Residential"
            ),
            _make_record(service_request_id="SR-2", complaint_type="Rodent"),
            _make_record(service_request_id="SR-3", complaint_type="HEAT/HOT WATER"),
            _make_record(service_request_id="SR-4", complaint_type="Illegal Parking"),
        )
        ctx = _make_context(complaints=records)
        # 4 types, each 25% -> HHI = 4 * 0.0625 = 0.25
        assert TopicConcentrationFactor().compute(ctx) == pytest.approx(0.25)

    def test_empty(self) -> None:
        ctx = _make_context(complaints=())
        assert TopicConcentrationFactor().compute(ctx) == 0.0


# ---------------------------------------------------------------------------
# SeasonalityFactor
# ---------------------------------------------------------------------------


class TestSeasonalityFactor:
    def test_above_baseline(self) -> None:
        baseline = {6: 50.0}
        records = tuple(_make_record(service_request_id=f"SR-{i}") for i in range(75))
        ctx = _make_context(complaints=records, time_window_start=date(2024, 6, 1))
        result = SeasonalityFactor(baseline).compute(ctx)
        assert result == pytest.approx(0.5)  # (75 - 50) / 50

    def test_below_baseline(self) -> None:
        baseline = {6: 100.0}
        records = tuple(_make_record(service_request_id=f"SR-{i}") for i in range(50))
        ctx = _make_context(complaints=records, time_window_start=date(2024, 6, 1))
        result = SeasonalityFactor(baseline).compute(ctx)
        assert result == pytest.approx(-0.5)

    def test_missing_month(self) -> None:
        baseline = {1: 100.0}  # only January
        ctx = _make_context(time_window_start=date(2024, 6, 1))
        assert SeasonalityFactor(baseline).compute(ctx) == 0.0


# ---------------------------------------------------------------------------
# AnomalyScoreFactor
# ---------------------------------------------------------------------------


class TestAnomalyScoreFactor:
    def test_z_score(self) -> None:
        records = tuple(_make_record(service_request_id=f"SR-{i}") for i in range(20))
        ctx = _make_context(complaints=records)
        result = AnomalyScoreFactor(population_mean=10.0, population_std=5.0).compute(
            ctx
        )
        assert result == pytest.approx(2.0)

    def test_zero_std(self) -> None:
        ctx = _make_context()
        result = AnomalyScoreFactor(population_mean=1.0, population_std=0.0).compute(
            ctx
        )
        assert result == 0.0


# ---------------------------------------------------------------------------
# ResponseRateFactor
# ---------------------------------------------------------------------------


class TestResponseRateFactor:
    def test_half_resolved(self) -> None:
        records = (
            _make_record(service_request_id="SR-1", resolution_description="Fixed"),
            _make_record(service_request_id="SR-2"),
        )
        ctx = _make_context(complaints=records)
        assert ResponseRateFactor().compute(ctx) == pytest.approx(0.5)

    def test_all_resolved(self) -> None:
        records = (
            _make_record(service_request_id="SR-1", resolution_description="Fixed"),
            _make_record(service_request_id="SR-2", resolution_description="Done"),
        )
        ctx = _make_context(complaints=records)
        assert ResponseRateFactor().compute(ctx) == pytest.approx(1.0)

    def test_empty(self) -> None:
        ctx = _make_context(complaints=())
        assert ResponseRateFactor().compute(ctx) == 0.0


# ---------------------------------------------------------------------------
# RecurrenceFactor
# ---------------------------------------------------------------------------


class TestRecurrenceFactor:
    def test_repeat_location(self) -> None:
        records = (
            _make_record(
                service_request_id="SR-1", latitude=40.6782, longitude=-73.9442
            ),
            _make_record(
                service_request_id="SR-2", latitude=40.6782, longitude=-73.9442
            ),
            _make_record(
                service_request_id="SR-3", latitude=40.7000, longitude=-73.9500
            ),
        )
        ctx = _make_context(complaints=records)
        result = RecurrenceFactor().compute(ctx)
        # 2 unique locations; 1 has count > 1 -> 1/2 = 0.5
        assert result == pytest.approx(0.5)

    def test_no_coordinates(self) -> None:
        records = (
            _make_record(service_request_id="SR-1", latitude=None, longitude=None),
        )
        ctx = _make_context(complaints=records)
        assert RecurrenceFactor().compute(ctx) == 0.0

    def test_all_unique(self) -> None:
        records = (
            _make_record(
                service_request_id="SR-1", latitude=40.6782, longitude=-73.9442
            ),
            _make_record(
                service_request_id="SR-2", latitude=40.7000, longitude=-73.9500
            ),
        )
        ctx = _make_context(complaints=records)
        assert RecurrenceFactor().compute(ctx) == 0.0


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class TestPipeline:
    def test_add_returns_new(self) -> None:
        p1 = Pipeline()
        p2 = p1.add(ComplaintVolumeFactor())
        assert len(p1.factors) == 0
        assert len(p2.factors) == 1

    def test_run_multiple_contexts(self) -> None:
        ctx_a = _make_context(
            geography_value="BROOKLYN 01",
            complaints=tuple(
                _make_record(service_request_id=f"SR-A{i}") for i in range(3)
            ),
        )
        ctx_b = _make_context(
            geography_value="MANHATTAN 01",
            complaints=tuple(
                _make_record(
                    service_request_id=f"SR-B{i}",
                    borough="MANHATTAN",
                    community_district="MANHATTAN 01",
                )
                for i in range(7)
            ),
        )

        pipeline = Pipeline().add(ComplaintVolumeFactor()).add(ResponseRateFactor())
        result = pipeline.run([ctx_a, ctx_b])

        assert result.geography_ids == ("BROOKLYN 01", "MANHATTAN 01")
        assert result.columns["complaint_volume"] == (3, 7)
        assert result.columns["response_rate"] == (0.0, 0.0)

    def test_run_empty(self) -> None:
        result = Pipeline().add(ComplaintVolumeFactor()).run([])
        assert result.geography_ids == ()
        assert result.columns["complaint_volume"] == ()


# ---------------------------------------------------------------------------
# PipelineResult
# ---------------------------------------------------------------------------


class TestPipelineResult:
    def test_to_records(self) -> None:
        result = PipelineResult(
            columns={"complaint_volume": (10, 20)},
            geography_ids=("BK01", "MN01"),
        )
        records = result.to_records()
        assert len(records) == 2
        assert records[0] == {"geography_id": "BK01", "complaint_volume": 10}
        assert records[1] == {"geography_id": "MN01", "complaint_volume": 20}

    @pytest.mark.optional
    def test_to_dataframe(self) -> None:
        result = PipelineResult(
            columns={"complaint_volume": (10, 20), "response_rate": (0.5, 0.8)},
            geography_ids=("BK01", "MN01"),
        )
        df = result.to_dataframe()
        assert df.index.name == "geography_id"
        assert list(df.columns) == ["complaint_volume", "response_rate"]
        assert df.loc["BK01", "complaint_volume"] == 10


# ---------------------------------------------------------------------------
# Advanced factors
# ---------------------------------------------------------------------------


class TestSpatialLagFactor:
    def test_computes_weighted_sum(self) -> None:
        weights = {"A": {"B": 0.6, "C": 0.4}, "B": {"A": 1.0}, "C": {"A": 1.0}}
        values = {"A": 10.0, "B": 20.0, "C": 30.0}
        factor = SpatialLagFactor(weights=weights, values=values)
        ctx = _make_context(geography_value="A")
        result = factor.compute(ctx)
        expected = 0.6 * 20.0 + 0.4 * 30.0
        assert result == pytest.approx(expected)

    def test_no_neighbors(self) -> None:
        factor = SpatialLagFactor(weights={}, values={"A": 10.0})
        ctx = _make_context(geography_value="A")
        assert factor.compute(ctx) == 0.0


class TestEquityGapFactor:
    def test_ratio_above_one(self) -> None:
        records = tuple(
            _make_record(
                service_request_id=f"SR-{i}",
                resolution_description="Resolved",
                created_date=date(2024, 5, 1),
            )
            for i in range(5)
        )
        ctx = FactorContext(
            geography="test",
            geography_value="SLOW_DISTRICT",
            complaints=records,
            time_window_start=date(2024, 5, 1),
            time_window_end=date(2024, 6, 15),
        )
        factor = EquityGapFactor(citywide_median_days=10.0)
        result = factor.compute(ctx)
        assert result > 0.0

    def test_no_resolved(self) -> None:
        records = (_make_record(resolution_description=None),)
        ctx = FactorContext(
            geography="test",
            geography_value="X",
            complaints=records,
            time_window_start=date(2024, 6, 1),
            time_window_end=date(2024, 6, 30),
        )
        factor = EquityGapFactor(citywide_median_days=10.0)
        assert factor.compute(ctx) == 0.0
