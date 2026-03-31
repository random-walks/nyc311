"""Reusable helpers shared across example scripts and notebooks."""

from __future__ import annotations

from .display import print_counter, print_lines, print_section
from .filters import (
    brooklyn_borough_filter,
    brooklyn_socrata_config,
    build_filter,
    manhattan_borough_filter,
)
from .geo import load_boundary_frame, merge_summary_map, save_choropleth
from .geo import save_boundary_preview
from .paths import (
    DATA_DIR,
    EXAMPLES_ROOT,
    OUTPUT_DIR,
    REPO_ROOT,
    data_path,
    ensure_output_dir,
    output_path,
)
from .plotting import configure_matplotlib_style, require_matplotlib, save_current_figure

__all__ = [
    "DATA_DIR",
    "EXAMPLES_ROOT",
    "OUTPUT_DIR",
    "REPO_ROOT",
    "brooklyn_borough_filter",
    "brooklyn_socrata_config",
    "build_filter",
    "configure_matplotlib_style",
    "data_path",
    "ensure_output_dir",
    "load_boundary_frame",
    "manhattan_borough_filter",
    "merge_summary_map",
    "output_path",
    "print_counter",
    "print_lines",
    "print_section",
    "require_matplotlib",
    "save_boundary_preview",
    "save_choropleth",
    "save_current_figure",
]
