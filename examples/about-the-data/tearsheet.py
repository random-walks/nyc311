"""Markdown tearsheet for the about-the-data example."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

import analysis_logic


def _csv_preview_markdown(path: Path, *, max_rows: int = 14) -> str:
    if not path.is_file():
        return f"*(missing {path.name})*"
    df = pd.read_csv(path, nrows=max_rows)
    if df.empty:
        return "*(empty)*"
    cols = "| " + " | ".join(str(c) for c in df.columns) + " |"
    sep = "|" + "|".join(["---"] * len(df.columns)) + "|"
    lines = [cols, sep]
    for _, row in df.iterrows():
        cells = []
        for x in row:
            s = str(x)
            if len(s) > 80:
                s = s[:77] + "..."
            cells.append(s)
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_tearsheet(
    *,
    boroughs: tuple[str, ...],
    catalogue: analysis_logic.CatalogueSummary,
    figures_dir: Path,
    tables_dir: Path,
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
    lines.extend(
        [
            "",
            "## EDA tables (CSV)",
            "",
            "Machine-readable slices written next to this report. Preview (truncated) below.",
            "",
        ]
    )
    table_order = (
        "sample_summary.csv",
        "rows_by_borough.csv",
        "top_complaint_types_citywide.csv",
        "daily_counts_last_45_days.csv",
    )
    for name in table_order:
        p = tables_dir / name
        if not p.is_file():
            continue
        rel = p.relative_to(reports_root)
        lines.append(f"### `{name}`")
        lines.append("")
        lines.append(f"[Download CSV]({rel.as_posix()})")
        lines.append("")
        lines.append(_csv_preview_markdown(p))
        lines.append("")
    for p in sorted(tables_dir.glob("*.csv")):
        if p.name in table_order:
            continue
        rel = p.relative_to(reports_root)
        lines.append(f"### `{p.name}`")
        lines.append("")
        lines.append(f"[Download CSV]({rel.as_posix()})")
        lines.append("")
        lines.append(_csv_preview_markdown(p))
        lines.append("")
    lines.extend(["", "## Figures", ""])
    for png in sorted(figures_dir.glob("*.png")):
        rel = png.relative_to(reports_root)
        lines.append(f"![{png.stem}]({rel.as_posix()})")
        lines.append("")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
