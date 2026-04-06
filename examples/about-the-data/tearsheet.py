"""Markdown tearsheet for the about-the-data example."""

from __future__ import annotations

from pathlib import Path

import analysis_logic


def write_tearsheet(
    *,
    boroughs: tuple[str, ...],
    catalogue: analysis_logic.CatalogueSummary,
    figures_dir: Path,
    report_path: Path,
    reports_root: Path,
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
        rel = png.relative_to(reports_root)
        lines.append(f"![{png.stem}]({rel.as_posix()})")
        lines.append("")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
