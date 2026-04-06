"""CLI for the NYC 311 about-the-data catalogue and figure pipeline."""

from __future__ import annotations

import argparse
import os
from datetime import date, datetime, timezone
from pathlib import Path

import analysis_logic
from download_logic import (
    ALL_BOROUGHS,
    download_all_records,
    download_boundary_layers,
    download_per_type_records,
    parse_borough_list,
    parse_complaint_types,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_CACHE = ROOT / "cache"
REPORTS_DIR = ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"


def _today() -> date:
    return datetime.now(timezone.utc).date()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--boroughs",
        default=",".join(ALL_BOROUGHS),
        help="Comma-separated boroughs (default: all five).",
    )
    p.add_argument("--start-date", default="2010-01-01")
    p.add_argument("--end-date", default=None)
    p.add_argument(
        "--complaint-types",
        default=None,
        help="Comma subset of supported topic complaint types (default: all 9).",
    )
    p.add_argument("--skip-download", action="store_true")
    p.add_argument("--skip-timeseries", action="store_true")
    p.add_argument("--skip-choropleth", action="store_true")
    p.add_argument("--skip-scatter", action="store_true")
    p.add_argument("--skip-hero", action="store_true")
    p.add_argument("--skip-analysis", action="store_true")
    p.add_argument("--refresh", action="store_true")
    p.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    p.add_argument("--no-publish-report", action="store_true")
    p.add_argument("--app-token", default=os.environ.get("NYC_OPEN_DATA_APP_TOKEN"))
    p.add_argument("--page-size", type=int, default=50_000)
    p.add_argument("--max-records-per-borough", type=int, default=None)
    p.add_argument(
        "--download-by-type",
        action="store_true",
        help="Also fetch per-(borough, complaint type) CSVs (large overlap with per-borough).",
    )
    return p


def _parse_date(raw: str | None) -> date:
    if raw is None:
        return _today()
    return date.fromisoformat(raw)


def write_tearsheet(
    *,
    boroughs: tuple[str, ...],
    catalogue: analysis_logic.CatalogueSummary,
    figures_dir: Path,
    report_path: Path,
) -> Path:
    lines: list[str] = [
        "# About the data — NYC 311",
        "",
        "## Boroughs in this run",
        "",
        *[f"- {b}" for b in boroughs],
        "",
        "## Catalogue",
        "",
        "| Borough | Records | Types seen | Supported-type rows | Date start | Date end | With coords | With resolution | CDs seen | Cache bytes |",
        "|---|---:|---:|---:|---|---|---:|---:|---:|---:|",
    ]
    for row in catalogue.rows:
        lines.append(
            f"| {row.borough} | {row.total_records} | {row.complaint_types_seen} | "
            f"{row.supported_types_records} | {row.date_range_start} | {row.date_range_end} | "
            f"{row.records_with_coords} | {row.records_with_resolution} | "
            f"{row.community_districts_seen} | {row.cache_bytes} |"
        )
    lines.extend(
        [
            "",
            "## Source layers",
            "",
            "| Name | URL / file | Rows / features |",
            "|---|---|---:|",
        ]
    )
    for name, url, n in catalogue.sources:
        lines.append(f"| {name} | {url} | {n} |")
    lines.extend(["", "## Figures", ""])
    for png in sorted(figures_dir.glob("*.png")):
        rel = png.relative_to(REPORTS_DIR)
        lines.append(f"![{png.stem}]({rel.as_posix()})")
        lines.append("")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> None:
    args = build_parser().parse_args()
    boroughs = parse_borough_list(args.boroughs)
    start = _parse_date(args.start_date)
    end = _parse_date(args.end_date)
    types = parse_complaint_types(args.complaint_types)
    cache_root = Path(args.cache_dir)
    app_token: str | None = args.app_token

    if not args.skip_download:
        download_boundary_layers(cache_root, refresh=args.refresh)
        download_all_records(
            cache_root,
            boroughs,
            refresh=args.refresh,
            app_token=app_token,
            start_date=start,
            end_date=end,
            page_size=args.page_size,
            max_records_per_borough=args.max_records_per_borough,
        )
        if args.download_by_type:
            download_per_type_records(
                cache_root,
                boroughs,
                types,
                refresh=args.refresh,
                app_token=app_token,
                start_date=start,
                end_date=end,
                page_size=args.page_size,
                max_records_per_borough=args.max_records_per_borough,
            )

    catalogue = analysis_logic.build_catalogue(cache_root, boroughs)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    analysis_logic.sample_eda_figures(
        cache_root,
        boroughs,
        figures_dir=FIGURES_DIR,
        artifacts_dir=ROOT / "artifacts",
    )
    if not args.skip_timeseries:
        analysis_logic.timeseries_figures(cache_root, boroughs, figures_dir=FIGURES_DIR)
    if not args.skip_choropleth:
        analysis_logic.choropleth_figures(cache_root, boroughs, figures_dir=FIGURES_DIR)
    if not args.skip_scatter:
        analysis_logic.scatter_map_figures(cache_root, boroughs, figures_dir=FIGURES_DIR)
    if not args.skip_hero:
        analysis_logic.hero_image_figures(cache_root, boroughs, figures_dir=FIGURES_DIR)
    if not args.skip_analysis:
        analysis_logic.analysis_figures(cache_root, boroughs, figures_dir=FIGURES_DIR)

    if not args.no_publish_report:
        write_tearsheet(
            boroughs=boroughs,
            catalogue=catalogue,
            figures_dir=FIGURES_DIR,
            report_path=REPORTS_DIR / "about-the-data-tearsheet.md",
        )


if __name__ == "__main__":
    main()
