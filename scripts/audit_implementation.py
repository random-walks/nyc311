"""Audit the public nyc311 surface and classify implemented versus planned."""

from __future__ import annotations

import ast
import inspect
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PACKAGE_DIR = SRC / "nyc311"
FIXTURE_CSV = ROOT / "tests" / "fixtures" / "service_requests_fixture.csv"
FIXTURE_BOUNDARIES = (
    ROOT / "tests" / "fixtures" / "community_district_boundaries.geojson"
)

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import nyc311  # noqa: E402


def _planned_symbols_from_source() -> set[str]:
    planned_symbols: set[str] = set()
    for path in PACKAGE_DIR.glob("*.py"):
        if path.name == "_version.py":
            continue
        module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in module.body:
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            if any(
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and call.func.id == "planned_surface"
                for call in ast.walk(node)
            ):
                planned_symbols.add(node.name)
    return planned_symbols


def _symbol_module_name(symbol_name: str, symbol: object) -> str:
    explicit_modules = {
        "__version__": "_version",
        "REQUIRED_SERVICE_REQUEST_COLUMNS": "loaders",
    }
    if symbol_name in explicit_modules:
        return explicit_modules[symbol_name]

    module_name = getattr(symbol, "__module__", "nyc311")
    if module_name == "nyc311":
        return "nyc311"
    if module_name.startswith("nyc311."):
        return module_name.removeprefix("nyc311.")
    return module_name


def _build_probes(tmpdir: Path) -> dict[str, Callable[[], Any]]:
    def load_records() -> list[nyc311.ServiceRequestRecord]:
        return nyc311.load_service_requests(
            FIXTURE_CSV,
            filters=nyc311.ServiceRequestFilter(
                complaint_types=("Noise - Residential",),
            ),
        )

    def load_assignments() -> list[nyc311.TopicAssignment]:
        return nyc311.extract_topics(
            load_records(),
            nyc311.TopicQuery("Noise - Residential"),
        )

    def load_summaries() -> list[nyc311.GeographyTopicSummary]:
        return nyc311.aggregate_by_geography(
            load_assignments(),
            geography="community_district",
        )

    def load_boundary_export() -> nyc311.BoundaryGeoJSONExport:
        return nyc311.BoundaryGeoJSONExport(
            boundaries=nyc311.load_boundaries(FIXTURE_BOUNDARIES),
            summaries=tuple(load_summaries()),
        )

    return {
        "main": lambda: nyc311.main(
            [
                "topics",
                "--source",
                str(FIXTURE_CSV),
                "--output",
                str(tmpdir / "cli-output.csv"),
                "--complaint-type",
                "Noise - Residential",
                "--geography",
                "community_district",
            ]
        ),
        "normalize_borough_name": lambda: nyc311.normalize_borough_name("bk"),
        "run_topic_pipeline": lambda: nyc311.run_topic_pipeline(
            FIXTURE_CSV,
            "Noise - Residential",
            geography="community_district",
            output=tmpdir / "pipeline-output.csv",
            output_format="csv",
        ),
        "load_service_requests": load_records,
        "load_resolution_data": lambda: nyc311.load_resolution_data(FIXTURE_CSV),
        "load_boundaries": lambda: nyc311.load_boundaries(FIXTURE_BOUNDARIES),
        "extract_topics": load_assignments,
        "aggregate_by_geography": load_summaries,
        "analyze_resolution_gaps": lambda: nyc311.analyze_resolution_gaps(
            load_records(),
            nyc311.load_resolution_data(FIXTURE_CSV),
        ),
        "detect_anomalies": lambda: nyc311.detect_anomalies(
            load_summaries(),
            nyc311.AnalysisWindow(days=30),
        ),
        "export_topic_table": lambda: nyc311.export_topic_table(
            load_summaries(),
            nyc311.ExportTarget("csv", tmpdir / "topics.csv"),
        ),
        "export_geojson": lambda: nyc311.export_geojson(
            load_boundary_export(),
            nyc311.ExportTarget("geojson", tmpdir / "topics.geojson"),
        ),
        "export_service_requests_csv": lambda: nyc311.export_service_requests_csv(
            load_records(),
            nyc311.ExportTarget("csv", tmpdir / "service-requests.csv"),
        ),
        "export_anomalies": lambda: nyc311.export_anomalies(
            [],
            nyc311.ExportTarget("csv", tmpdir / "anomalies.csv"),
        ),
        "export_report_card": lambda: nyc311.export_report_card(
            {},
            nyc311.ExportTarget("csv", tmpdir / "report-card.csv"),
        ),
        "supported_topic_queries": nyc311.supported_topic_queries,
    }


def _status_for_symbol(
    symbol_name: str,
    symbol: object,
    planned_symbols: set[str],
    probes: dict[str, Callable[[], Any]],
) -> str:
    if symbol_name in planned_symbols:
        return "planned"
    if inspect.isclass(symbol) or not callable(symbol):
        return "implemented"

    probe = probes.get(symbol_name)
    if probe is not None:
        try:
            probe()
        except NotImplementedError:
            return "planned"
        except SystemExit as exc:
            return "implemented" if exc.code in (0, None) else "planned"
        except (LookupError, OSError, RuntimeError, TypeError, ValueError):
            return "implemented"
        return "implemented"

    try:
        source = inspect.getsource(symbol)
    except (OSError, TypeError):
        return "implemented"
    return "planned" if "planned_surface(" in source else "implemented"


def _iter_public_rows() -> list[tuple[str, str, str]]:
    planned_symbols = _planned_symbols_from_source()
    with tempfile.TemporaryDirectory() as tmp:
        probes = _build_probes(Path(tmp))
        rows = []
        for symbol_name in nyc311.__all__:
            symbol = getattr(nyc311, symbol_name)
            rows.append(
                (
                    symbol_name,
                    _symbol_module_name(symbol_name, symbol),
                    _status_for_symbol(symbol_name, symbol, planned_symbols, probes),
                )
            )
    return rows


def main() -> int:
    """Print a markdown table summarizing the current public implementation."""
    rows = _iter_public_rows()
    implemented_count = sum(status == "implemented" for *_rest, status in rows)
    planned_count = sum(status == "planned" for *_rest, status in rows)
    lines = [
        "# nyc311 implementation audit",
        "",
        f"- implemented: {implemented_count}",
        f"- planned: {planned_count}",
        "",
        "| Symbol | Module | Status |",
        "| --- | --- | --- |",
        *[
            f"| `{symbol_name}` | `{module_name}` | `{status}` |"
            for symbol_name, module_name, status in rows
        ],
    ]
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
