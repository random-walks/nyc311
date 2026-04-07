"""Time-series and panel aggregations for complaint records and topic assignments."""

from __future__ import annotations

from typing import Any, Literal

from ..models import ServiceRequestRecord, TopicAssignment
from ._pandas import require_pandas
from ._records import records_to_dataframe


def _normalize_pandas_freq(freq: str) -> str:
    """Map deprecated offset aliases for current pandas versions."""
    return {"M": "ME", "Q": "QE", "Y": "YE", "A": "YE"}.get(freq, freq)


def to_timeseries(
    records: list[ServiceRequestRecord],
    *,
    freq: str = "D",
) -> Any:
    """Return complaint counts per period with a :class:`~pandas.DatetimeIndex`.

    Columns are complaint types (wide format). Suitable for ``.plot()``, ``.rolling()``,
    and ``.resample()``.
    """
    pd = require_pandas()
    if not records:
        return pd.DataFrame()

    freq = _normalize_pandas_freq(freq)
    dataframe = records_to_dataframe(records)
    counts = (
        dataframe.groupby([pd.Grouper(key="created_date", freq=freq), "complaint_type"])
        .size()
        .unstack(fill_value=0)
    )
    counts = counts.sort_index()
    counts.index.name = "created_date"
    return counts


def to_panel(
    records: list[ServiceRequestRecord],
    *,
    freq: str = "D",
    geography: str = "borough",
) -> Any:
    """Return a panel of complaint counts indexed by ``(geography_value, period)``.

    Columns are complaint types. Use ``.xs("BROOKLYN", level=0)`` for one area.
    """
    pd = require_pandas()
    if not records:
        return pd.DataFrame()

    freq = _normalize_pandas_freq(freq)
    dataframe = records_to_dataframe(records)
    geo_series = [record.geography_value(geography) for record in records]
    dataframe = dataframe.assign(_geography=geo_series)

    counts = (
        dataframe.groupby(
            [
                "_geography",
                pd.Grouper(key="created_date", freq=freq),
                "complaint_type",
            ]
        )
        .size()
        .unstack(fill_value=0)
    )
    counts.index.names = ("geography_value", "created_date")
    return counts.sort_index()


def to_topic_timeseries(
    assignments: list[TopicAssignment],
    *,
    freq: str = "D",
) -> Any:
    """Like :func:`to_timeseries` but aggregates extracted topic labels."""
    pd = require_pandas()
    if not assignments:
        return pd.DataFrame()

    freq = _normalize_pandas_freq(freq)
    dataframe = pd.DataFrame(
        {
            "created_date": pd.to_datetime(
                [a.record.created_date for a in assignments]
            ),
            "topic": [a.topic for a in assignments],
        }
    )
    counts = (
        dataframe.groupby([pd.Grouper(key="created_date", freq=freq), "topic"])
        .size()
        .unstack(fill_value=0)
    )
    counts = counts.sort_index()
    counts.index.name = "created_date"
    return counts


def resample_and_fill(
    dataframe: Any,
    freq: str,
    *,
    method: Literal["zero", "ffill", "bfill"] = "zero",
) -> Any:
    """Resample a DatetimeIndex-indexed frame and fill missing bins.

    ``method='zero'`` fills missing values with ``0`` (typical for counts).
    """
    pd = require_pandas()
    if dataframe is None or getattr(dataframe, "empty", True):
        return dataframe

    if not isinstance(dataframe.index, pd.DatetimeIndex):
        raise TypeError("resample_and_fill() expects a DatetimeIndex on the DataFrame.")

    freq = _normalize_pandas_freq(freq)
    resampled = dataframe.resample(freq).sum()
    if method == "zero":
        return resampled.fillna(0)
    if method == "ffill":
        return resampled.ffill()
    if method == "bfill":
        return resampled.bfill()
    raise ValueError(f"Unsupported method: {method!r}.")
