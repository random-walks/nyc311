from __future__ import annotations

import argparse
import csv
import os
from collections import Counter, defaultdict
from importlib import import_module
from pathlib import Path

from nyc311 import analysis, export, io, models, pipeline, presets

ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / "cache"
ARTIFACTS_DIR = ROOT / "artifacts"
REPORTS_DIR = ROOT / "reports"
REPORT_FIGURES_DIR = REPORTS_DIR / "figures"


def cache_path(filename: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / filename


def artifact_path(filename: str) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    return ARTIFACTS_DIR / filename


def report_path(filename: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR / filename


def report_figure_path(filename: str) -> Path:
    REPORT_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    return REPORT_FIGURES_DIR / filename


def save_figure(figure: object, output_path: Path) -> Path:
    figure.tight_layout()
    figure.savefig(output_path, bbox_inches="tight", dpi=150)
    return output_path


def require_matplotlib() -> object:
    return import_module("matplotlib.pyplot")


def format_topic_name(value: str) -> str:
    return value.replace("_", " ").title()


def print_section(title: str) -> None:
    print(title)
    print("-" * len(title))


def print_pairs(title: str, rows: list[tuple[str, int]]) -> None:
    print(title)
    for label, count in rows:
        print(f"- {label}: {count}")


def write_csv_rows(
    output_path: Path,
    *,
    fieldnames: list[str],
    rows: list[dict[str, object]],
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a Brooklyn community-district case study with local cache reuse.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Ignore the existing cache file and fetch a fresh live slice.",
    )
    parser.add_argument(
        "--publish-report",
        action="store_true",
        help="Write tracked report markdown and tracked figures under reports/.",
    )
    parser.add_argument(
        "--app-token",
        default=os.getenv("NYC_OPEN_DATA_APP_TOKEN"),
        help="Optional Socrata app token. Falls back to NYC_OPEN_DATA_APP_TOKEN.",
    )
    return parser


def load_records(
    refresh: bool, app_token: str | None
) -> tuple[list[models.ServiceRequestRecord], str, Path]:
    snapshot_path = cache_path("brooklyn-case-study.csv")
    if snapshot_path.exists() and not refresh:
        return io.load_service_requests(snapshot_path), "cache", snapshot_path

    records = pipeline.fetch_service_requests(
        filters=presets.brooklyn_borough_filter(
            start_date="2025-01-01",
            end_date="2025-03-31",
        ),
        socrata_config=presets.small_socrata_config(
            app_token=app_token,
            page_size=1000,
            max_pages=5,
        ),
        output=snapshot_path,
    )
    return records, "live fetch", snapshot_path


def build_resolution_rows(
    records: list[models.ServiceRequestRecord],
    *,
    group_field: str,
    label_key: str,
) -> list[dict[str, object]]:
    grouped_totals: dict[str, int] = defaultdict(int)
    grouped_resolved: dict[str, int] = defaultdict(int)
    for record in records:
        label = str(getattr(record, group_field))
        grouped_totals[label] += 1
        if record.resolution_description is not None:
            grouped_resolved[label] += 1

    rows: list[dict[str, object]] = []
    for label, total_count in grouped_totals.items():
        resolved_count = grouped_resolved[label]
        unresolved_count = total_count - resolved_count
        rows.append(
            {
                label_key: label,
                "total_count": total_count,
                "resolved_count": resolved_count,
                "unresolved_count": unresolved_count,
                "resolution_rate": resolved_count / total_count,
                "unresolved_share": unresolved_count / total_count,
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            -float(row["unresolved_share"]),
            -int(row["total_count"]),
            str(row[label_key]),
        ),
    )


def build_noise_snapshot_rows(
    summaries: list[models.GeographyTopicSummary],
) -> list[dict[str, object]]:
    summaries_by_district: dict[str, list[models.GeographyTopicSummary]] = defaultdict(list)
    for summary in summaries:
        summaries_by_district[summary.geography_value].append(summary)

    snapshot_rows: list[dict[str, object]] = []
    for district, district_summaries in summaries_by_district.items():
        ordered_summaries = sorted(
            district_summaries,
            key=lambda summary: (summary.topic_rank, summary.topic),
        )
        dominant_summary = ordered_summaries[0]
        party_music_summary = next(
            (
                summary
                for summary in ordered_summaries
                if summary.topic == "party_music"
            ),
            None,
        )
        snapshot_rows.append(
            {
                "district": district,
                "geography_total_count": dominant_summary.geography_total_count,
                "dominant_topic": dominant_summary.topic,
                "dominant_count": dominant_summary.complaint_count,
                "dominant_share": dominant_summary.share_of_geography,
                "party_music_count": (
                    0 if party_music_summary is None else party_music_summary.complaint_count
                ),
                "party_music_share": (
                    0.0
                    if party_music_summary is None
                    else party_music_summary.share_of_geography
                ),
            }
        )
    return sorted(
        snapshot_rows,
        key=lambda row: (
            -float(row["party_music_share"]),
            -int(row["geography_total_count"]),
            str(row["district"]),
        ),
    )


def build_district_volume_figure(district_volume_rows: list[dict[str, object]]) -> object:
    plt = require_matplotlib()
    plot_rows = sorted(
        district_volume_rows[:10],
        key=lambda row: (-int(row["total_count"]), str(row["district"])),
    )
    figure, axes = plt.subplots(figsize=(9, 5.5))
    bars = axes.barh(
        [str(row["district"]) for row in plot_rows],
        [int(row["total_count"]) for row in plot_rows],
        color="#2563eb",
    )
    axes.invert_yaxis()
    axes.set_xlabel("Complaint count in cached Brooklyn slice")
    axes.set_title("Which districts carry the most Brooklyn complaint volume?")
    axes.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    axes.grid(axis="x", alpha=0.25)
    max_count = max(int(row["total_count"]) for row in plot_rows)
    axes.set_xlim(0, max_count * 1.18)
    for bar, row in zip(bars, plot_rows, strict=True):
        axes.text(
            bar.get_width() + max_count * 0.02,
            bar.get_y() + bar.get_height() / 2,
            str(int(row["total_count"])),
            ha="left",
            va="center",
            fontsize=8,
        )
    return figure


def build_party_music_intensity_figure(
    noise_snapshot_rows: list[dict[str, object]],
) -> object:
    plt = require_matplotlib()
    percent_formatter = import_module("matplotlib.ticker").PercentFormatter
    plot_rows = noise_snapshot_rows[:10]
    figure, axes = plt.subplots(figsize=(9, 5.5))
    bars = axes.barh(
        [str(row["district"]) for row in plot_rows],
        [float(row["party_music_share"]) for row in plot_rows],
        color=[
            "#7c3aed" if float(row["party_music_share"]) > 0 else "#cbd5e1"
            for row in plot_rows
        ],
    )
    axes.invert_yaxis()
    axes.set_xlim(0, 1)
    axes.set_xlabel("Party music share of district noise complaints")
    axes.set_title("Which districts show the strongest party-music intensity?")
    axes.xaxis.set_major_formatter(percent_formatter(xmax=1))
    axes.grid(axis="x", alpha=0.25)
    for bar, row in zip(bars, plot_rows, strict=True):
        axes.text(
            bar.get_width() + 0.02,
            bar.get_y() + bar.get_height() / 2,
            (
                f"{float(row['party_music_share']):.1%} "
                f"({int(row['party_music_count'])}/{int(row['geography_total_count'])})"
            ),
            ha="left",
            va="center",
            fontsize=8,
        )
    return figure


def build_resolution_gap_figure(
    district_resolution_rows: list[dict[str, object]],
) -> object:
    plt = require_matplotlib()
    percent_formatter = import_module("matplotlib.ticker").PercentFormatter
    plot_rows = district_resolution_rows[:10]
    figure, axes = plt.subplots(figsize=(9, 5.5))
    bars = axes.barh(
        [str(row["district"]) for row in plot_rows],
        [float(row["unresolved_share"]) for row in plot_rows],
        color="#dc2626",
    )
    axes.invert_yaxis()
    axes.set_xlim(0, 1)
    axes.set_xlabel("Unresolved share of district complaints")
    axes.set_title("Which districts have the weakest resolution rates?")
    axes.xaxis.set_major_formatter(percent_formatter(xmax=1))
    axes.grid(axis="x", alpha=0.25)
    for bar, row in zip(bars, plot_rows, strict=True):
        axes.text(
            bar.get_width() + 0.02,
            bar.get_y() + bar.get_height() / 2,
            (
                f"{float(row['unresolved_share']):.1%} "
                f"({int(row['unresolved_count'])}/{int(row['total_count'])})"
            ),
            ha="left",
            va="center",
            fontsize=8,
        )
    return figure


def write_report(
    *,
    source: str,
    snapshot_path: Path,
    total_records: int,
    complaint_type_rows: list[dict[str, object]],
    district_volume_rows: list[dict[str, object]],
    district_resolution_rows: list[dict[str, object]],
    complaint_resolution_rows: list[dict[str, object]],
    noise_snapshot_rows: list[dict[str, object]],
    volume_chart_path: Path,
    party_chart_path: Path,
    resolution_chart_path: Path,
) -> Path:
    report_file = report_path("community-district-case-study-tearsheet.md")
    top_complaint_row = complaint_type_rows[0]
    top_district_row = district_volume_rows[0]
    top_party_row = noise_snapshot_rows[0]
    weakest_resolution_row = district_resolution_rows[0]
    weakest_complaint_resolution = complaint_resolution_rows[0]
    lines = [
        "# Community District Case Study Tearsheet",
        "",
        "This tearsheet summarizes a cached Brooklyn slice and focuses on community",
        "district volume, normalized residential-noise topics, and resolution gaps.",
        "Refresh the cache and republish only when you intentionally want to update",
        "the tracked report assets.",
        "",
        "## Executive Summary",
        "",
        (
            f"- The cached slice contains `{total_records}` complaint records across "
            f"`{len(district_volume_rows)}` community districts."
        ),
        (
            f"- The largest complaint category is `{top_complaint_row['complaint_type']}` "
            f"with `{int(top_complaint_row['count'])}` records "
            f"({float(top_complaint_row['share']):.1%} of the slice)."
        ),
        (
            f"- The busiest district is `{top_district_row['district']}` with "
            f"`{int(top_district_row['total_count'])}` complaints."
        ),
        (
            f"- The strongest party-music intensity appears in "
            f"`{top_party_row['district']}`, where party music accounts for "
            f"`{float(top_party_row['party_music_share']):.1%}` of sampled "
            f"residential-noise complaints."
        ),
        (
            f"- The weakest district-level resolution rate appears in "
            f"`{weakest_resolution_row['district']}`, where "
            f"`{float(weakest_resolution_row['unresolved_share']):.1%}` of complaints "
            f"remain unresolved."
        ),
        (
            f"- The complaint group with the weakest overall resolution rate is "
            f"`{weakest_complaint_resolution['complaint_type']}` at "
            f"`{float(weakest_complaint_resolution['unresolved_share']):.1%}` unresolved."
        ),
        (
            f"- Report source: `{source}` using cache file "
            f"`cache/{snapshot_path.name}`."
        ),
        "",
        "## District Volume",
        "",
        f"![District complaint volume](./figures/{volume_chart_path.name})",
        "",
        "## Party Music Intensity",
        "",
        f"![Party music intensity by district](./figures/{party_chart_path.name})",
        "",
        "## Resolution Gap Comparison",
        "",
        f"![Resolution gap by district](./figures/{resolution_chart_path.name})",
        "",
        "## Top Complaint Types",
        "",
        "| Complaint type | Count | Share of slice |",
        "| --- | --- | --- |",
    ]
    for row in complaint_type_rows[:10]:
        lines.append(
            f"| {row['complaint_type']} | {int(row['count'])} | {float(row['share']):.1%} |"
        )
    lines.extend(
        [
            "",
            "## District Metrics",
            "",
            "| District | Total complaints | Dominant noise topic | Dominant share | Party music share | Resolution rate |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    resolution_by_district = {
        str(row["district"]): row for row in district_resolution_rows
    }
    for row in noise_snapshot_rows[:10]:
        resolution_row = resolution_by_district[str(row["district"])]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["district"]),
                    str(int(resolution_row["total_count"])),
                    format_topic_name(str(row["dominant_topic"])),
                    f"{float(row['dominant_share']):.1%}",
                    f"{float(row['party_music_share']):.1%}",
                    f"{float(resolution_row['resolution_rate']):.1%}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Resolution Hotspots",
            "",
            "| District | Unresolved count | Total complaints | Unresolved share |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in district_resolution_rows[:10]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["district"]),
                    str(int(row["unresolved_count"])),
                    str(int(row["total_count"])),
                    f"{float(row['unresolved_share']):.1%}",
                ]
            )
            + " |"
        )
    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_file


def main() -> None:
    args = build_parser().parse_args()
    records, source, snapshot_path = load_records(args.refresh, args.app_token)
    if not records:
        raise RuntimeError("The case-study slice did not return any records.")

    complaint_type_counts = Counter(record.complaint_type for record in records)
    district_counts = Counter(record.community_district for record in records)
    complaint_type_rows = [
        {
            "complaint_type": complaint_type,
            "count": count,
            "share": count / len(records),
        }
        for complaint_type, count in complaint_type_counts.most_common()
    ]
    district_volume_rows = [
        {"district": district, "total_count": count}
        for district, count in district_counts.most_common()
    ]
    district_resolution_rows = build_resolution_rows(
        records,
        group_field="community_district",
        label_key="district",
    )
    complaint_resolution_rows = build_resolution_rows(
        records,
        group_field="complaint_type",
        label_key="complaint_type",
    )

    noise_records = [
        record for record in records if record.complaint_type == "Noise - Residential"
    ]
    if not noise_records:
        raise RuntimeError("The case-study slice did not contain Noise - Residential rows.")

    assignments = analysis.extract_topics(
        noise_records,
        models.TopicQuery("Noise - Residential"),
    )
    summaries = analysis.aggregate_by_geography(
        assignments,
        geography="community_district",
    )
    dominant_topics = [summary for summary in summaries if summary.is_dominant_topic]
    noise_snapshot_rows = build_noise_snapshot_rows(summaries)

    topic_summary_path = artifact_path("brooklyn-noise-community-districts.csv")
    dominant_topic_path = artifact_path("brooklyn-noise-dominant-districts.csv")
    district_volume_path = artifact_path("brooklyn-district-volume.csv")
    district_resolution_path = artifact_path("brooklyn-district-resolution.csv")
    complaint_resolution_path = artifact_path("brooklyn-complaint-type-resolution.csv")
    export.export_topic_table(
        summaries,
        models.ExportTarget("csv", topic_summary_path),
    )
    export.export_topic_table(
        dominant_topics,
        models.ExportTarget("csv", dominant_topic_path),
    )
    write_csv_rows(
        district_volume_path,
        fieldnames=["district", "total_count"],
        rows=district_volume_rows,
    )
    write_csv_rows(
        district_resolution_path,
        fieldnames=[
            "district",
            "total_count",
            "resolved_count",
            "unresolved_count",
            "resolution_rate",
            "unresolved_share",
        ],
        rows=district_resolution_rows,
    )
    write_csv_rows(
        complaint_resolution_path,
        fieldnames=[
            "complaint_type",
            "total_count",
            "resolved_count",
            "unresolved_count",
            "resolution_rate",
            "unresolved_share",
        ],
        rows=complaint_resolution_rows,
    )

    report_file: Path | None = None
    volume_chart_path: Path | None = None
    party_chart_path: Path | None = None
    resolution_chart_path: Path | None = None
    if args.publish_report:
        volume_chart_path = save_figure(
            build_district_volume_figure(district_volume_rows),
            report_figure_path("brooklyn-district-volume.png"),
        )
        party_chart_path = save_figure(
            build_party_music_intensity_figure(noise_snapshot_rows),
            report_figure_path("brooklyn-party-music-intensity.png"),
        )
        resolution_chart_path = save_figure(
            build_resolution_gap_figure(district_resolution_rows),
            report_figure_path("brooklyn-resolution-gap.png"),
        )
        report_file = write_report(
            source=source,
            snapshot_path=snapshot_path,
            total_records=len(records),
            complaint_type_rows=complaint_type_rows,
            district_volume_rows=district_volume_rows,
            district_resolution_rows=district_resolution_rows,
            complaint_resolution_rows=complaint_resolution_rows,
            noise_snapshot_rows=noise_snapshot_rows,
            volume_chart_path=volume_chart_path,
            party_chart_path=party_chart_path,
            resolution_chart_path=resolution_chart_path,
        )

    print_section("Community District Case Study")
    print(f"Record source: {source}")
    print(f"Cache path: {snapshot_path}")
    print(f"Loaded records: {len(records)}")
    print_pairs("Top complaint types", complaint_type_counts.most_common(5))
    print_pairs("Top districts by volume", district_counts.most_common(5))
    print("Weakest district-level resolution rates")
    for row in district_resolution_rows[:5]:
        print(
            f"- {row['district']}: {float(row['unresolved_share']):.1%} unresolved "
            f"({int(row['unresolved_count'])}/{int(row['total_count'])})"
        )
    print(f"Wrote topic summary: {topic_summary_path}")
    print(f"Wrote dominant-topic summary: {dominant_topic_path}")
    print(f"Wrote district volume summary: {district_volume_path}")
    print(f"Wrote district resolution summary: {district_resolution_path}")
    print(f"Wrote complaint resolution summary: {complaint_resolution_path}")
    if report_file is None:
        print("Skipped tracked report generation. Re-run with --publish-report to update reports/.")
    else:
        print(f"Wrote tracked volume chart: {volume_chart_path}")
        print(f"Wrote tracked party-music chart: {party_chart_path}")
        print(f"Wrote tracked resolution chart: {resolution_chart_path}")
        print(f"Wrote tracked report: {report_file}")
    print("Dominant Brooklyn noise topics by district")
    for row in noise_snapshot_rows[:10]:
        print(
            f"- {row['district']}: {format_topic_name(str(row['dominant_topic']))} "
            f"({int(row['dominant_count'])}/{int(row['geography_total_count'])}, "
            f"{float(row['dominant_share']):.1%})"
        )


if __name__ == "__main__":
    main()
