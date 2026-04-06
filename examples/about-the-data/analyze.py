"""Catalogue + figure pipeline using cached CSVs (no Socrata unless you run download.py)."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import analysis_logic
from download_logic import parse_borough_list
from parsers import build_analyze_parser, build_common_parser
from paths import (
    ARTIFACTS_DIR,
    FIGURES_DIR,
    README_HERO_IMAGE,
    REPORTS_DIR,
    SCATTER_LIB_COVER,
    TABLES_DIR,
)
from tearsheet import write_tearsheet


def _publish_readme_hero_from_scatter_cover() -> None:
    """Copy the library scatter cover into ``docs/images`` for the root README + PyPI."""
    if not SCATTER_LIB_COVER.is_file() or SCATTER_LIB_COVER.stat().st_size < 1024:
        return
    README_HERO_IMAGE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SCATTER_LIB_COVER, README_HERO_IMAGE)


def run_analyze(args: argparse.Namespace) -> None:
    boroughs = parse_borough_list(args.boroughs)
    cache_root = Path(args.cache_dir).expanduser().resolve()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    if args.clear_figures:
        for png in FIGURES_DIR.glob("*.png"):
            png.unlink()
    if args.clear_report:
        report = REPORTS_DIR / "about-the-data-tearsheet.md"
        if report.is_file():
            report.unlink()
        if TABLES_DIR.is_dir():
            for p in TABLES_DIR.glob("*"):
                if p.is_file():
                    p.unlink()

    catalogue = analysis_logic.build_catalogue(cache_root, boroughs)
    analysis_logic.sample_eda_figures(
        cache_root,
        boroughs,
        figures_dir=FIGURES_DIR,
        artifacts_dir=ARTIFACTS_DIR,
    )
    if not args.skip_timeseries:
        analysis_logic.timeseries_figures(cache_root, boroughs, figures_dir=FIGURES_DIR)
    if not args.skip_choropleth:
        analysis_logic.choropleth_figures(cache_root, boroughs, figures_dir=FIGURES_DIR)
    if not args.skip_scatter:
        analysis_logic.scatter_map_figures(cache_root, boroughs, figures_dir=FIGURES_DIR)
        _publish_readme_hero_from_scatter_cover()
    if not args.skip_hero:
        analysis_logic.hero_image_figures(cache_root, boroughs, figures_dir=FIGURES_DIR)
    if not args.skip_analysis:
        analysis_logic.analysis_figures(cache_root, boroughs, figures_dir=FIGURES_DIR)

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    analysis_logic.write_eda_tables(cache_root, boroughs, tables_dir=TABLES_DIR)

    if not args.no_publish_report:
        write_tearsheet(
            boroughs=boroughs,
            catalogue=catalogue,
            figures_dir=FIGURES_DIR,
            tables_dir=TABLES_DIR,
            report_path=REPORTS_DIR / "about-the-data-tearsheet.md",
            reports_root=REPORTS_DIR,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        parents=[build_common_parser(), build_analyze_parser()],
    )
    args = parser.parse_args()
    run_analyze(args)


if __name__ == "__main__":
    main()
