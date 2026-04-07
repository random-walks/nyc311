"""Tests for dataframes time-series helpers."""

from __future__ import annotations

import pandas as pd

from nyc311.analysis import extract_topics
from nyc311.dataframes import (
    resample_and_fill,
    to_panel,
    to_timeseries,
    to_topic_timeseries,
)
from nyc311.io import load_service_requests
from nyc311.models import TopicQuery

FIXTURE_PATH = __import__("pathlib").Path(__file__).parent / "fixtures" / "service_requests_fixture.csv"


def test_to_timeseries_shape() -> None:
    records = load_service_requests(FIXTURE_PATH)
    ts = to_timeseries(records, freq="M")
    assert not ts.empty
    assert ts.index.is_monotonic_increasing


def test_to_panel_multiindex() -> None:
    records = load_service_requests(FIXTURE_PATH)
    panel = to_panel(records, freq="M", geography="borough")
    assert panel.index.nlevels == 2


def test_resample_and_fill() -> None:
    idx = pd.date_range("2024-01-01", periods=3, freq="D")
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0]}, index=idx)
    out = resample_and_fill(df, "2D", method="zero")
    assert len(out) >= 2


def test_topic_timeseries() -> None:
    records = load_service_requests(FIXTURE_PATH)
    assignments = extract_topics(records, TopicQuery(complaint_type="Illegal Parking"))
    ts = to_topic_timeseries(assignments, freq="M")
    assert not ts.empty
