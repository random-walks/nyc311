from __future__ import annotations

from pathlib import Path

import pytest

from nyc311.cli import main
from nyc311.exporters import export_anomalies, export_geojson, export_report_card
from nyc311.loaders import load_boundaries, load_resolution_data
from nyc311.models import AnalysisWindow, ExportTarget
from nyc311.processors import analyze_resolution_gaps, detect_anomalies


def test_planned_loaders_still_raise_not_implemented() -> None:
    with pytest.raises(NotImplementedError, match="planned nyc311 surface"):
        load_resolution_data(Path("resolution.csv"))

    with pytest.raises(NotImplementedError, match="planned nyc311 surface"):
        load_boundaries(Path("boundaries.geojson"))


def test_planned_processors_still_raise_not_implemented() -> None:
    with pytest.raises(NotImplementedError, match="planned nyc311 surface"):
        detect_anomalies([], AnalysisWindow(days=30))

    with pytest.raises(NotImplementedError, match="planned nyc311 surface"):
        analyze_resolution_gaps([], object())


def test_planned_exporters_and_cli_still_raise_not_implemented(tmp_path: Path) -> None:
    target = ExportTarget(format="geojson", output_path=tmp_path / "out.geojson")

    with pytest.raises(NotImplementedError, match="planned nyc311 surface"):
        export_geojson([], target)

    with pytest.raises(NotImplementedError, match="planned nyc311 surface"):
        export_anomalies([], target)

    with pytest.raises(NotImplementedError, match="planned nyc311 surface"):
        export_report_card([], target)

    with pytest.raises(NotImplementedError, match="planned nyc311 surface"):
        main([])
