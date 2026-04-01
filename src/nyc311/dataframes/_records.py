"""Record-shaped dataframe conversions for nyc311 models."""

from __future__ import annotations

from datetime import date
from typing import Any

from ..export._tabular import (
    SERVICE_REQUEST_DATAFRAME_COLUMNS,
    SERVICE_REQUEST_REQUIRED_DATAFRAME_COLUMNS,
    TOPIC_ASSIGNMENT_COLUMNS,
)
from ..models import ServiceRequestRecord, TopicAssignment
from ._pandas import require_pandas


def records_to_dataframe(records: list[ServiceRequestRecord]) -> Any:
    """Convert service-request records into a notebook-friendly DataFrame."""
    pd = require_pandas()
    dataframe = pd.DataFrame.from_records(
        [
            {
                "service_request_id": record.service_request_id,
                "created_date": record.created_date,
                "complaint_type": record.complaint_type,
                "descriptor": record.descriptor,
                "borough": record.borough,
                "community_district": record.community_district,
                "resolution_description": record.resolution_description,
                "latitude": record.latitude,
                "longitude": record.longitude,
            }
            for record in records
        ],
        columns=SERVICE_REQUEST_DATAFRAME_COLUMNS,
    )
    if "created_date" in dataframe:
        dataframe["created_date"] = pd.to_datetime(dataframe["created_date"])
    return dataframe


def dataframe_to_records(dataframe: Any) -> list[ServiceRequestRecord]:
    """Convert a DataFrame back into typed service-request records."""
    pd = require_pandas()
    required_columns = set(SERVICE_REQUEST_REQUIRED_DATAFRAME_COLUMNS)
    missing_columns = sorted(required_columns.difference(dataframe.columns))
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(
            f"DataFrame is missing required service-request columns: {missing}."
        )

    records: list[ServiceRequestRecord] = []
    for row in dataframe.to_dict(orient="records"):
        raw_created_date = row["created_date"]
        if hasattr(raw_created_date, "to_pydatetime"):
            created_date = raw_created_date.to_pydatetime().date()
        elif isinstance(raw_created_date, date):
            created_date = raw_created_date
        else:
            created_date = date.fromisoformat(str(raw_created_date))

        resolution_description = row.get("resolution_description")
        normalized_resolution = (
            None
            if resolution_description in (None, "") or pd.isna(resolution_description)
            else str(resolution_description)
        )
        latitude = row.get("latitude")
        longitude = row.get("longitude")
        records.append(
            ServiceRequestRecord(
                service_request_id=str(row["service_request_id"]),
                created_date=created_date,
                complaint_type=str(row["complaint_type"]),
                descriptor=str(row["descriptor"]),
                borough=str(row["borough"]),
                community_district=str(row["community_district"]),
                resolution_description=normalized_resolution,
                latitude=None if latitude is None or pd.isna(latitude) else latitude,
                longitude=None
                if longitude is None or pd.isna(longitude)
                else longitude,
            )
        )
    return records


def assignments_to_dataframe(assignments: list[TopicAssignment]) -> Any:
    """Convert topic assignments into a DataFrame."""
    pd = require_pandas()
    dataframe = pd.DataFrame.from_records(
        [
            {
                "service_request_id": assignment.record.service_request_id,
                "created_date": assignment.record.created_date,
                "complaint_type": assignment.record.complaint_type,
                "descriptor": assignment.record.descriptor,
                "borough": assignment.record.borough,
                "community_district": assignment.record.community_district,
                "resolution_description": assignment.record.resolution_description,
                "latitude": assignment.record.latitude,
                "longitude": assignment.record.longitude,
                "topic": assignment.topic,
                "normalized_text": assignment.normalized_text,
            }
            for assignment in assignments
        ],
        columns=TOPIC_ASSIGNMENT_COLUMNS,
    )
    if "created_date" in dataframe:
        dataframe["created_date"] = pd.to_datetime(dataframe["created_date"])
    return dataframe
