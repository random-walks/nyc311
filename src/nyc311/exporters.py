"""Planned exporters for map-ready and report-ready outputs."""

from __future__ import annotations

from typing import Any

from ._not_implemented import planned_surface
from .models import ExportTarget


def export_geojson(data: Any, target: ExportTarget) -> Any:
    """Export geography-aware complaint outputs to GeoJSON."""
    planned_surface("export_geojson()")


def export_topic_table(data: Any, target: ExportTarget) -> Any:
    """Export topic summaries to CSV or similar tabular formats."""
    planned_surface("export_topic_table()")


def export_anomalies(data: Any, target: ExportTarget) -> Any:
    """Export anomaly detections for downstream reporting."""
    planned_surface("export_anomalies()")


def export_report_card(data: Any, target: ExportTarget) -> Any:
    """Export a neighborhood report-card style artifact."""
    planned_surface("export_report_card()")
