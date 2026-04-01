"""GeoJSON exporter for nyc311 artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from ..models import BoundaryGeoJSONExport, ExportTarget


def export_geojson(data: BoundaryGeoJSONExport, target: ExportTarget) -> Path:
    """Export supported boundary-backed complaint outputs to GeoJSON."""
    if target.format != "geojson":
        raise ValueError(
            "export_geojson() currently supports only GeoJSON output. "
            f"Got format={target.format!r}."
        )

    output_path = target.output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary_by_geography = {
        summary.geography_value: summary
        for summary in data.summaries
        if summary.is_dominant_topic
    }
    features: list[dict[str, object]] = []
    for boundary in data.boundaries.features:
        summary = summary_by_geography.get(boundary.geography_value)
        properties: dict[str, object] = {
            "geography": boundary.geography,
            "geography_value": boundary.geography_value,
            **boundary.properties,
        }
        if summary is not None:
            properties.update(
                {
                    "complaint_type": summary.complaint_type,
                    "dominant_topic": summary.topic,
                    "topic_count": summary.complaint_count,
                    "geography_total_count": summary.geography_total_count,
                    "share_of_geography": round(summary.share_of_geography, 6),
                }
            )
        features.append(
            {
                "type": "Feature",
                "geometry": boundary.geometry,
                "properties": properties,
            }
        )

    feature_collection = {"type": "FeatureCollection", "features": features}
    output_path.write_text(
        json.dumps(feature_collection, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output_path
