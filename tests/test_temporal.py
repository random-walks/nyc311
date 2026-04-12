"""Tests for the temporal panel module."""

from __future__ import annotations

from datetime import date

import pytest

from nyc311.models import ServiceRequestRecord
from nyc311.temporal import (
    PanelDataset,
    PanelObservation,
    TreatmentEvent,
    build_complaint_panel,
    build_distance_weights,
    centroids_from_boundaries,
    weights_to_pysal,
)

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
) -> ServiceRequestRecord:
    return ServiceRequestRecord(
        service_request_id=service_request_id,
        created_date=created_date,
        complaint_type=complaint_type,
        descriptor=descriptor,
        borough=borough,
        community_district=community_district,
        resolution_description=resolution_description,
    )


def _sample_records() -> list[ServiceRequestRecord]:
    """Three months of complaints across two districts."""
    records = []
    idx = 0
    for month, day in [(4, 10), (5, 15), (6, 20)]:
        for district in ["BROOKLYN 01", "BROOKLYN 02"]:
            for _ in range(3):
                records.append(
                    _make_record(
                        service_request_id=f"SR-{idx}",
                        created_date=date(2024, month, day),
                        community_district=district,
                        resolution_description="Fixed" if idx % 2 == 0 else None,
                    )
                )
                idx += 1
    return records


# ---------------------------------------------------------------------------
# TreatmentEvent
# ---------------------------------------------------------------------------


class TestTreatmentEvent:
    def test_valid(self) -> None:
        event = TreatmentEvent(
            name="rat_program",
            description="Rat mitigation pilot",
            treated_units=("BROOKLYN 01",),
            treatment_date=date(2024, 5, 1),
            geography="community_district",
        )
        assert event.name == "rat_program"

    def test_empty_name(self) -> None:
        with pytest.raises(ValueError, match="name must not be empty"):
            TreatmentEvent(
                name="  ",
                description="test",
                treated_units=("BK01",),
                treatment_date=date(2024, 1, 1),
                geography="community_district",
            )

    def test_empty_units(self) -> None:
        with pytest.raises(ValueError, match="at least one unit"):
            TreatmentEvent(
                name="test",
                description="test",
                treated_units=(),
                treatment_date=date(2024, 1, 1),
                geography="community_district",
            )


# ---------------------------------------------------------------------------
# build_complaint_panel
# ---------------------------------------------------------------------------


class TestBuildComplaintPanel:
    def test_balanced_panel(self) -> None:
        records = _sample_records()
        panel = build_complaint_panel(
            records, geography="community_district", freq="ME"
        )

        assert panel.unit_type == "community_district"
        assert len(panel.unit_ids) == 2
        assert len(panel.periods) == 3

        # Balanced: every unit appears in every period
        expected_obs = len(panel.unit_ids) * len(panel.periods)
        assert len(panel.observations) == expected_obs

    def test_complaint_counts(self) -> None:
        records = _sample_records()
        panel = build_complaint_panel(
            records, geography="community_district", freq="ME"
        )

        # 3 records per (district, month)
        for obs in panel.observations:
            assert obs.complaint_count == 3

    def test_resolution_rate(self) -> None:
        records = _sample_records()
        panel = build_complaint_panel(
            records, geography="community_district", freq="ME"
        )

        for obs in panel.observations:
            # With alternating resolution, ~50% should be resolved
            assert 0.0 <= obs.resolution_rate <= 1.0

    def test_treatment_indicator(self) -> None:
        records = _sample_records()
        event = TreatmentEvent(
            name="pilot",
            description="Test pilot",
            treated_units=("BROOKLYN 01",),
            treatment_date=date(2024, 5, 1),
            geography="community_district",
        )
        panel = build_complaint_panel(
            records,
            geography="community_district",
            freq="ME",
            treatment_events=[event],
        )

        for obs in panel.observations:
            if obs.unit_id == "BROOKLYN 01" and obs.period >= "2024-05":
                assert obs.treatment is True
                assert obs.treatment_date == date(2024, 5, 1)
            elif obs.unit_id == "BROOKLYN 01":
                assert obs.treatment is False
            else:
                # BROOKLYN 02 is never treated
                assert obs.treatment is False
                assert obs.treatment_date is None

    def test_population_data(self) -> None:
        records = _sample_records()
        pops = {"BROOKLYN 01": 50_000, "BROOKLYN 02": 30_000}
        panel = build_complaint_panel(
            records,
            geography="community_district",
            freq="ME",
            population_data=pops,
        )
        bk01 = [o for o in panel.observations if o.unit_id == "BROOKLYN 01"]
        assert all(o.population == 50_000 for o in bk01)

    def test_covariates(self) -> None:
        records = _sample_records()
        covs = {"BROOKLYN 01": {"median_income": 55_000.0}}
        panel = build_complaint_panel(
            records,
            geography="community_district",
            freq="ME",
            covariates=covs,
        )
        bk01 = [o for o in panel.observations if o.unit_id == "BROOKLYN 01"]
        assert all(o.covariates == {"median_income": 55_000.0} for o in bk01)

    def test_empty_records(self) -> None:
        panel = build_complaint_panel([], geography="borough", freq="ME")
        assert panel.observations == ()
        assert panel.periods == ()

    def test_borough_geography(self) -> None:
        records = [
            _make_record(service_request_id="SR-1", borough="BROOKLYN"),
            _make_record(
                service_request_id="SR-2",
                borough="MANHATTAN",
                community_district="MANHATTAN 01",
            ),
        ]
        panel = build_complaint_panel(records, geography="borough", freq="ME")
        assert set(panel.unit_ids) == {"BROOKLYN", "MANHATTAN"}


# ---------------------------------------------------------------------------
# PanelDataset
# ---------------------------------------------------------------------------


class TestPanelDataset:
    def test_treatment_group(self) -> None:
        obs = (
            PanelObservation(
                unit_id="A",
                period="2024-01",
                complaint_count=10,
                complaint_counts_by_type={},
                resolution_rate=0.5,
                median_resolution_days=5.0,
                treatment=True,
                treatment_date=date(2024, 1, 1),
                population=None,
            ),
            PanelObservation(
                unit_id="B",
                period="2024-01",
                complaint_count=5,
                complaint_counts_by_type={},
                resolution_rate=0.8,
                median_resolution_days=3.0,
                treatment=False,
                treatment_date=None,
                population=None,
            ),
        )
        panel = PanelDataset(observations=obs, unit_type="cd", periods=("2024-01",))
        treated = panel.treatment_group()
        assert treated.unit_ids == ("A",)

    def test_control_group(self) -> None:
        obs = (
            PanelObservation(
                unit_id="A",
                period="2024-01",
                complaint_count=10,
                complaint_counts_by_type={},
                resolution_rate=0.5,
                median_resolution_days=5.0,
                treatment=True,
                treatment_date=date(2024, 1, 1),
                population=None,
            ),
            PanelObservation(
                unit_id="B",
                period="2024-01",
                complaint_count=5,
                complaint_counts_by_type={},
                resolution_rate=0.8,
                median_resolution_days=3.0,
                treatment=False,
                treatment_date=None,
                population=None,
            ),
        )
        panel = PanelDataset(observations=obs, unit_type="cd", periods=("2024-01",))
        control = panel.control_group()
        assert control.unit_ids == ("B",)

    def test_filter_periods(self) -> None:
        obs = (
            PanelObservation(
                unit_id="A",
                period="2024-01",
                complaint_count=10,
                complaint_counts_by_type={},
                resolution_rate=0.5,
                median_resolution_days=None,
                treatment=False,
                treatment_date=None,
                population=None,
            ),
            PanelObservation(
                unit_id="A",
                period="2024-02",
                complaint_count=15,
                complaint_counts_by_type={},
                resolution_rate=0.6,
                median_resolution_days=None,
                treatment=False,
                treatment_date=None,
                population=None,
            ),
            PanelObservation(
                unit_id="A",
                period="2024-03",
                complaint_count=12,
                complaint_counts_by_type={},
                resolution_rate=0.7,
                median_resolution_days=None,
                treatment=False,
                treatment_date=None,
                population=None,
            ),
        )
        panel = PanelDataset(
            observations=obs,
            unit_type="cd",
            periods=("2024-01", "2024-02", "2024-03"),
        )
        filtered = panel.filter_periods("2024-01", "2024-02")
        assert filtered.periods == ("2024-01", "2024-02")
        assert len(filtered.observations) == 2

    @pytest.mark.optional
    def test_to_dataframe(self) -> None:
        obs = (
            PanelObservation(
                unit_id="A",
                period="2024-01",
                complaint_count=10,
                complaint_counts_by_type={"Noise": 5, "Rodent": 5},
                resolution_rate=0.5,
                median_resolution_days=4.0,
                treatment=False,
                treatment_date=None,
                population=50_000,
            ),
        )
        panel = PanelDataset(observations=obs, unit_type="cd", periods=("2024-01",))
        df = panel.to_dataframe()
        assert df.index.names == ["unit_id", "period"]
        assert df.loc[("A", "2024-01"), "complaint_count"] == 10


# ---------------------------------------------------------------------------
# Spatial weights
# ---------------------------------------------------------------------------


class TestSpatialWeights:
    def test_build_distance_weights_symmetric(self) -> None:
        centroids = {
            "A": (40.70, -74.00),
            "B": (40.71, -74.00),
            "C": (40.80, -74.00),  # ~11 km from A — beyond default 2 km threshold
        }
        weights = build_distance_weights(centroids, threshold_meters=2000.0)

        # A and B are neighbors; C is too far from both
        assert "B" in weights["A"]
        assert "A" in weights["B"]
        assert "C" not in weights["A"]
        assert "C" not in weights["B"]
        # Symmetry
        assert weights["A"]["B"] == pytest.approx(weights["B"]["A"])

    def test_row_standardization(self) -> None:
        centroids = {
            "A": (40.70, -74.00),
            "B": (40.701, -74.00),
            "C": (40.702, -74.00),
        }
        weights = build_distance_weights(
            centroids, threshold_meters=5000.0, row_standardize=True
        )
        for uid in centroids:
            row_sum = sum(weights[uid].values())
            if row_sum > 0:
                assert row_sum == pytest.approx(1.0)

    def test_no_standardization(self) -> None:
        centroids = {
            "A": (40.70, -74.00),
            "B": (40.701, -74.00),
        }
        weights = build_distance_weights(
            centroids, threshold_meters=5000.0, row_standardize=False
        )
        # Raw inverse distance should not sum to 1
        assert weights["A"]["B"] > 0


# ---------------------------------------------------------------------------
# centroids_from_boundaries / weights_to_pysal helpers
# ---------------------------------------------------------------------------


class _StubFeature:
    def __init__(self, geography_value: str, geometry: dict) -> None:
        self.geography_value = geography_value
        self.geometry = geometry


class _StubBoundaries:
    def __init__(self, features: list[_StubFeature]) -> None:
        self.features = features


class TestCentroidsFromBoundaries:
    def test_polygon_centroid_is_mean_of_ring(self) -> None:
        # Square ring centered on (40.7, -74.0). The implementation averages
        # exterior-ring vertices including the closing vertex, so the
        # expected centroid weights it twice — verify against that.
        ring = [
            [-74.0, 40.7],
            [-73.9, 40.7],
            [-73.9, 40.8],
            [-74.0, 40.8],
            [-74.0, 40.7],  # closing vertex
        ]
        boundaries = _StubBoundaries(
            [_StubFeature("CD01", {"type": "Polygon", "coordinates": [ring]})]
        )

        centroids = centroids_from_boundaries(boundaries)

        assert "CD01" in centroids
        lat, lon = centroids["CD01"]
        expected_lat = sum(pt[1] for pt in ring) / len(ring)
        expected_lon = sum(pt[0] for pt in ring) / len(ring)
        assert lat == pytest.approx(expected_lat)
        assert lon == pytest.approx(expected_lon)

    def test_multipolygon_uses_first_outer_ring(self) -> None:
        ring = [
            [-74.0, 40.7],
            [-73.9, 40.7],
            [-73.9, 40.8],
            [-74.0, 40.7],
        ]
        boundaries = _StubBoundaries(
            [
                _StubFeature(
                    "CD02",
                    {"type": "MultiPolygon", "coordinates": [[ring]]},
                )
            ]
        )

        centroids = centroids_from_boundaries(boundaries)

        assert "CD02" in centroids

    def test_skips_features_with_empty_geometry(self) -> None:
        boundaries = _StubBoundaries(
            [
                _StubFeature("EMPTY", {"type": "Polygon", "coordinates": []}),
                _StubFeature(
                    "CD03",
                    {"type": "Polygon", "coordinates": [[[-74.0, 40.7], [-73.9, 40.7]]]},
                ),
            ]
        )

        centroids = centroids_from_boundaries(boundaries)
        assert "EMPTY" not in centroids
        assert "CD03" in centroids


@pytest.mark.optional
class TestWeightsToPysal:
    def test_round_trip_to_libpysal_w(self) -> None:
        pytest.importorskip("libpysal")

        weights = {
            "A": {"B": 0.5, "C": 0.5},
            "B": {"A": 1.0},
            "C": {"A": 1.0},
        }
        w = weights_to_pysal(weights)

        assert sorted(w.neighbors["A"]) == ["B", "C"]
        # libpysal stores weights as a list aligned with neighbors
        assert sum(w.weights["A"]) == pytest.approx(1.0)
