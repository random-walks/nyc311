"""Point GeoDataFrame helpers for nyc311 service-request records."""

from __future__ import annotations

from typing import Any

from ..dataframes import records_to_dataframe
from ..export._tabular import SERVICE_REQUEST_DATAFRAME_COLUMNS
from ..models import ServiceRequestRecord
from ._deps import require_geospatial_stack


def records_to_geodataframe(records: list[ServiceRequestRecord]) -> Any:
    """Convert point-capable service-request records into a GeoDataFrame."""
    geopandas, _ = require_geospatial_stack()
    records_with_coordinates = [
        record
        for record in records
        if record.latitude is not None and record.longitude is not None
    ]
    if not records_with_coordinates:
        return geopandas.GeoDataFrame(
            columns=(*SERVICE_REQUEST_DATAFRAME_COLUMNS, "geometry"),
            geometry="geometry",
            crs="EPSG:4326",
        )

    dataframe = records_to_dataframe(records_with_coordinates).copy()
    return geopandas.GeoDataFrame(
        dataframe,
        geometry=geopandas.points_from_xy(
            dataframe["longitude"],
            dataframe["latitude"],
        ),
        crs="EPSG:4326",
    )
