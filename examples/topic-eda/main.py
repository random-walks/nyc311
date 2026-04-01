from __future__ import annotations

import argparse
import csv
import os
from collections import Counter
from datetime import date
from importlib import import_module
from pathlib import Path

from nyc311 import analysis, dataframes, export, io, models, pipeline, presets

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
        description="Run a topic coverage and anomaly audit with local cache reuse.",
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
    snapshot_path = cache_path("topic-eda-snapshot.csv")
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
            max_pages=15,
        ),
        output=snapshot_path,
    )
    return records, "live fetch", snapshot_path


def build_coverage_rows(
    records: list[models.ServiceRequestRecord],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    descriptor_counts = Counter()
    coverage_rows: list[dict[str, object]] = []
    for complaint_type in models.supported_topic_queries():
        coverage = analysis.analyze_topic_coverage(
            records,
            models.TopicQuery(complaint_type=complaint_type, top_n=10),
        )
        if coverage.total_records == 0:
            continue
        for descriptor, count in coverage.top_unmatched_descriptors:
            descriptor_counts[descriptor] += count
        top_unmatched_descriptor, top_unmatched_count = (
            ("No unmatched descriptors", 0)
            if not coverage.top_unmatched_descriptors
            else coverage.top_unmatched_descriptors[0]
        )
        coverage_rows.append(
            {
                "complaint_type": coverage.complaint_type,
                "total_records": coverage.total_records,
                "matched_records": coverage.matched_records,
                "other_records": coverage.other_records,
                "coverage_rate": coverage.coverage_rate,
                "top_unmatched_descriptor": top_unmatched_descriptor,
                "top_unmatched_count": top_unmatched_count,
            }
        )
    coverage_rows = sorted(
        coverage_rows,
        key=lambda row: (
            float(row["coverage_rate"]),
            -int(row["total_records"]),
            str(row["complaint_type"]),
        ),
    )
    descriptor_rows = [
        {"descriptor": descriptor, "count": count}
        for descriptor, count in descriptor_counts.most_common(10)
    ]
    return coverage_rows, descriptor_rows


def build_custom_rule_demo() -> tuple[
    models.TopicCoverageReport, models.TopicCoverageReport
]:
    custom_rules = (
        ("hydrant_issue", ("hydrant", "low water pressure")),
        ("leak", ("leak", "leaking")),
    )
    synthetic_records = [
        models.ServiceRequestRecord(
            service_request_id="demo-1",
            created_date=date(2025, 1, 1),
            complaint_type="Water System",
            descriptor="Low water pressure near hydrant",
            borough=models.BOROUGH_BROOKLYN,
            community_district="01 BROOKLYN",
        ),
        models.ServiceRequestRecord(
            service_request_id="demo-2",
            created_date=date(2025, 1, 2),
            complaint_type="Water System",
            descriptor="Leaking hydrant on corner",
            borough=models.BOROUGH_BROOKLYN,
            community_district="01 BROOKLYN",
        ),
        models.ServiceRequestRecord(
            service_request_id="demo-3",
            created_date=date(2025, 1, 3),
            complaint_type="Water System",
            descriptor="Pressure issue in building basement",
            borough=models.BOROUGH_BROOKLYN,
            community_district="01 BROOKLYN",
        ),
    ]
    before_coverage = analysis.analyze_topic_coverage(
        synthetic_records,
        models.TopicQuery("Water System", top_n=10),
    )
    after_coverage = analysis.analyze_topic_coverage(
        synthetic_records,
        models.TopicQuery("Water System", top_n=10),
        custom_rules=custom_rules,
    )
    return before_coverage, after_coverage


def build_coverage_figure(coverage_rows: list[dict[str, object]]) -> object:
    plt = require_matplotlib()
    percent_formatter = import_module("matplotlib.ticker").PercentFormatter
    plot_rows = coverage_rows[:10]
    figure, axes = plt.subplots(figsize=(10, 6))
    bars = axes.barh(
        [str(row["complaint_type"]) for row in plot_rows],
        [float(row["coverage_rate"]) for row in plot_rows],
        color="#2563eb",
    )
    axes.invert_yaxis()
    axes.set_xlim(0, 1)
    axes.set_xlabel("Coverage rate")
    axes.set_title("Which complaint types have the weakest built-in topic coverage?")
    axes.xaxis.set_major_formatter(percent_formatter(xmax=1))
    axes.grid(axis="x", alpha=0.25)
    for bar, row in zip(bars, plot_rows, strict=True):
        axes.text(
            bar.get_width() + 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"{int(row['matched_records'])}/{int(row['total_records'])}",
            ha="left",
            va="center",
            fontsize=8,
        )
    return figure


def build_unmatched_descriptor_figure(
    descriptor_rows: list[dict[str, object]],
) -> object:
    plt = require_matplotlib()
    plot_rows = descriptor_rows[:10]
    figure, axes = plt.subplots(figsize=(10, 5.5))
    bars = axes.barh(
        [str(row["descriptor"]) for row in plot_rows],
        [int(row["count"]) for row in plot_rows],
        color="#f59e0b",
    )
    axes.invert_yaxis()
    axes.set_xlabel("Unmatched descriptor count")
    axes.set_title("Which unmatched descriptors drive the biggest coverage gaps?")
    axes.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    axes.grid(axis="x", alpha=0.25)
    max_count = max(int(row["count"]) for row in plot_rows)
    axes.set_xlim(0, max_count * 1.18)
    for bar, row in zip(bars, plot_rows, strict=True):
        axes.text(
            bar.get_width() + max_count * 0.02,
            bar.get_y() + bar.get_height() / 2,
            str(int(row["count"])),
            ha="left",
            va="center",
            fontsize=8,
        )
    return figure


def build_anomaly_figure(anomalies: list[models.AnomalyResult]) -> object:
    plt = require_matplotlib()
    plot_rows = anomalies[:10]
    figure, axes = plt.subplots(figsize=(10, 5.5))
    bars = axes.barh(
        [
            f"{row.geography_value} / {format_topic_name(row.topic)}"
            for row in plot_rows
        ],
        [row.z_score for row in plot_rows],
        color=["#7c3aed" if row.z_score >= 0 else "#dc2626" for row in plot_rows],
    )
    axes.invert_yaxis()
    axes.axvline(0, color="#334155", linewidth=1)
    axes.set_xlabel("Z-score")
    axes.set_title("Which geography/topic summaries look most anomalous?")
    axes.grid(axis="x", alpha=0.25)
    for bar, row in zip(bars, plot_rows, strict=True):
        axes.text(
            bar.get_width() + (0.06 if row.z_score >= 0 else -0.06),
            bar.get_y() + bar.get_height() / 2,
            f"{row.z_score:+.2f}",
            ha="left" if row.z_score >= 0 else "right",
            va="center",
            fontsize=8,
        )
    return figure


def build_resolution_gap_figure(
    resolution_rows: list[models.ResolutionGapSummary],
) -> object:
    plt = require_matplotlib()
    percent_formatter = import_module("matplotlib.ticker").PercentFormatter
    plot_rows = resolution_rows[:10]
    figure, axes = plt.subplots(figsize=(10, 5.5))
    bars = axes.barh(
        [row.complaint_type for row in plot_rows],
        [row.unresolved_share for row in plot_rows],
        color="#dc2626",
    )
    axes.invert_yaxis()
    axes.set_xlim(0, 1)
    axes.set_xlabel("Unresolved share")
    axes.set_title("Which complaint groups have the highest unresolved share?")
    axes.xaxis.set_major_formatter(percent_formatter(xmax=1))
    axes.grid(axis="x", alpha=0.25)
    for bar, row in zip(bars, plot_rows, strict=True):
        axes.text(
            bar.get_width() + 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"{row.unresolved_request_count}/{row.total_request_count}",
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
    coverage_rows: list[dict[str, object]],
    descriptor_rows: list[dict[str, object]],
    anomalies: list[models.AnomalyResult],
    resolution_rows: list[models.ResolutionGapSummary],
    before_coverage: models.TopicCoverageReport,
    after_coverage: models.TopicCoverageReport,
    coverage_chart_path: Path,
    descriptor_chart_path: Path,
    anomaly_chart_path: Path,
    resolution_chart_path: Path,
) -> Path:
    report_file = report_path("topic-eda-tearsheet.md")
    weakest_coverage = coverage_rows[0]
    strongest_coverage = max(
        coverage_rows,
        key=lambda row: (
            float(row["coverage_rate"]),
            int(row["matched_records"]),
            str(row["complaint_type"]),
        ),
    )
    top_descriptor = descriptor_rows[0]
    top_anomaly = anomalies[0]
    top_resolution_gap = resolution_rows[0]
    lines = [
        "# Topic EDA Tearsheet",
        "",
        "This tearsheet summarizes a cached Brooklyn slice and highlights topic-rule",
        "coverage, unmatched descriptors, anomaly outliers, and resolution gaps.",
        "Refresh and republish only when you intentionally want to update the",
        "tracked report assets.",
        "",
        "## Executive Summary",
        "",
        (
            f"- The cached slice contains `{total_records}` complaint records sourced from "
            f"`cache/{snapshot_path.name}` (`{source}`)."
        ),
        (
            f"- The weakest built-in topic coverage in this slice is "
            f"`{weakest_coverage['complaint_type']}` at "
            f"`{float(weakest_coverage['coverage_rate']):.1%}` matched."
        ),
        (
            f"- The strongest built-in topic coverage is `{strongest_coverage['complaint_type']}` "
            f"at `{float(strongest_coverage['coverage_rate']):.1%}` matched."
        ),
        (
            f"- The biggest unmatched descriptor driver is `{top_descriptor['descriptor']}` "
            f"with `{int(top_descriptor['count'])}` unmatched rows in the coverage audit."
        ),
        (
            f"- The largest anomaly by absolute z-score is "
            f"`{top_anomaly.geography_value} / {format_topic_name(top_anomaly.topic)}` "
            f"at `{top_anomaly.z_score:+.2f}`."
        ),
        (
            f"- The highest unresolved share in the cached slice appears in "
            f"`{top_resolution_gap.complaint_type}` at "
            f"`{top_resolution_gap.unresolved_share:.1%}` unresolved."
        ),
        (
            f"- In the synthetic Water System demo, custom rules change coverage from "
            f"`{before_coverage.coverage_rate:.1%}` to `{after_coverage.coverage_rate:.1%}`."
        ),
        "",
        "## Coverage Rates",
        "",
        f"![Coverage rate by complaint type](./figures/{coverage_chart_path.name})",
        "",
        "## Top Unmatched Descriptors",
        "",
        f"![Top unmatched descriptors](./figures/{descriptor_chart_path.name})",
        "",
        "## Anomaly Scores",
        "",
        f"![Top anomaly z-scores](./figures/{anomaly_chart_path.name})",
        "",
        "## Resolution Gaps",
        "",
        f"![Resolution gaps by complaint type](./figures/{resolution_chart_path.name})",
        "",
        "## Coverage Metrics",
        "",
        "| Complaint type | Matched | Total | Coverage rate | Top unmatched descriptor |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        "| "
        + " | ".join(
            [
                str(row["complaint_type"]),
                str(int(row["matched_records"])),
                str(int(row["total_records"])),
                f"{float(row['coverage_rate']):.1%}",
                str(row["top_unmatched_descriptor"]),
            ]
        )
        + " |"
        for row in coverage_rows[:10]
    )
    lines.extend(
        [
            "",
            "## Resolution Hotspots",
            "",
            "| Complaint type | Unresolved count | Total requests | Unresolved share |",
            "| --- | --- | --- | --- |",
        ]
    )
    lines.extend(
        "| "
        + " | ".join(
            [
                row.complaint_type,
                str(row.unresolved_request_count),
                str(row.total_request_count),
                f"{row.unresolved_share:.1%}",
            ]
        )
        + " |"
        for row in resolution_rows[:10]
    )
    lines.extend(
        [
            "",
            "## Custom Rule Demo",
            "",
            "| Scenario | Coverage rate | Matched records | Total records |",
            "| --- | --- | --- | --- |",
            (
                f"| Before custom rules | {before_coverage.coverage_rate:.1%} | "
                f"{before_coverage.matched_records} | {before_coverage.total_records} |"
            ),
            (
                f"| After custom rules | {after_coverage.coverage_rate:.1%} | "
                f"{after_coverage.matched_records} | {after_coverage.total_records} |"
            ),
        ]
    )
    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_file


def main() -> None:
    args = build_parser().parse_args()
    records, source, snapshot_path = load_records(args.refresh, args.app_token)
    if not records:
        raise RuntimeError("The topic EDA slice did not return any records.")

    records_df = dataframes.records_to_dataframe(records)
    complaint_distribution = (
        records_df["complaint_type"]
        .value_counts()
        .rename_axis("complaint_type")
        .reset_index(name="count")
    )
    coverage_rows, descriptor_rows = build_coverage_rows(records)
    if not coverage_rows:
        raise RuntimeError(
            "The topic EDA slice did not include supported topic query rows."
        )
    if not descriptor_rows:
        descriptor_rows = [{"descriptor": "No unmatched descriptors", "count": 0}]
    before_coverage, after_coverage = build_custom_rule_demo()

    noise_records = [
        record for record in records if record.complaint_type == "Noise - Residential"
    ]
    if not noise_records:
        raise RuntimeError(
            "The topic EDA slice did not contain Noise - Residential rows."
        )

    noise_assignments = analysis.extract_topics(
        noise_records,
        models.TopicQuery("Noise - Residential", top_n=10),
    )
    noise_summaries = analysis.aggregate_by_geography(
        noise_assignments,
        geography="community_district",
    )
    anomalies = analysis.detect_anomalies(
        noise_summaries,
        models.AnalysisWindow(days=30),
        z_threshold=1.5,
    )
    resolution_records = [
        record for record in records if record.resolution_description is not None
    ]
    resolution_rows = analysis.analyze_resolution_gaps(records, resolution_records)
    if not resolution_rows:
        raise RuntimeError(
            "The topic EDA slice did not produce any resolution-gap summaries."
        )

    report_card_path = artifact_path("topic-eda-report.md")
    coverage_summary_path = artifact_path("topic-coverage-summary.csv")
    unmatched_descriptor_path = artifact_path("topic-unmatched-descriptors.csv")
    anomaly_path = artifact_path("topic-anomalies.csv")
    resolution_path = artifact_path("topic-resolution-gaps.csv")
    export.export_report_card(
        {
            "topic_summaries": noise_summaries,
            "resolution_gaps": resolution_rows,
            "anomalies": anomalies,
        },
        models.ExportTarget("md", report_card_path),
    )
    write_csv_rows(
        coverage_summary_path,
        fieldnames=[
            "complaint_type",
            "total_records",
            "matched_records",
            "other_records",
            "coverage_rate",
            "top_unmatched_descriptor",
            "top_unmatched_count",
        ],
        rows=coverage_rows,
    )
    write_csv_rows(
        unmatched_descriptor_path,
        fieldnames=["descriptor", "count"],
        rows=descriptor_rows,
    )
    export.export_anomalies(
        anomalies,
        models.ExportTarget("csv", anomaly_path),
    )
    write_csv_rows(
        resolution_path,
        fieldnames=[
            "geography",
            "geography_value",
            "complaint_type",
            "total_request_count",
            "resolved_request_count",
            "unresolved_request_count",
            "unresolved_share",
            "resolution_rate",
        ],
        rows=[
            {
                "geography": row.geography,
                "geography_value": row.geography_value,
                "complaint_type": row.complaint_type,
                "total_request_count": row.total_request_count,
                "resolved_request_count": row.resolved_request_count,
                "unresolved_request_count": row.unresolved_request_count,
                "unresolved_share": row.unresolved_share,
                "resolution_rate": row.resolution_rate,
            }
            for row in resolution_rows
        ],
    )

    report_file: Path | None = None
    coverage_chart_path: Path | None = None
    descriptor_chart_path: Path | None = None
    anomaly_chart_path: Path | None = None
    resolution_chart_path: Path | None = None
    if args.publish_report:
        coverage_chart_path = save_figure(
            build_coverage_figure(coverage_rows),
            report_figure_path("topic-coverage-by-complaint-type.png"),
        )
        descriptor_chart_path = save_figure(
            build_unmatched_descriptor_figure(descriptor_rows),
            report_figure_path("top-unmatched-descriptors.png"),
        )
        anomaly_chart_path = save_figure(
            build_anomaly_figure(anomalies),
            report_figure_path("topic-anomaly-zscores.png"),
        )
        resolution_chart_path = save_figure(
            build_resolution_gap_figure(resolution_rows),
            report_figure_path("topic-resolution-gap.png"),
        )
        report_file = write_report(
            source=source,
            snapshot_path=snapshot_path,
            total_records=len(records),
            coverage_rows=coverage_rows,
            descriptor_rows=descriptor_rows,
            anomalies=anomalies,
            resolution_rows=resolution_rows,
            before_coverage=before_coverage,
            after_coverage=after_coverage,
            coverage_chart_path=coverage_chart_path,
            descriptor_chart_path=descriptor_chart_path,
            anomaly_chart_path=anomaly_chart_path,
            resolution_chart_path=resolution_chart_path,
        )

    print("Topic EDA")
    print("---------")
    print(f"Record source: {source}")
    print(f"Cache path: {snapshot_path}")
    print("Complaint type distribution")
    print(complaint_distribution.head(10).to_string(index=False))
    print("\nCoverage audit for built-in topic rules")
    for row in coverage_rows[:10]:
        print(
            f"- {row['complaint_type']}: {int(row['matched_records'])}/"
            f"{int(row['total_records'])} matched "
            f"({float(row['coverage_rate']):.1%})"
        )
        if int(row["top_unmatched_count"]) > 0:
            print(
                f"  top unmatched -> {row['top_unmatched_descriptor']}: "
                f"{int(row['top_unmatched_count'])}"
            )
    print("\nCustom rule demo for Water System")
    print(f"- before custom rules: {before_coverage.coverage_rate:.1%} matched")
    print(f"- after custom rules:  {after_coverage.coverage_rate:.1%} matched")
    print(f"\nWrote baseline report card: {report_card_path}")
    print(f"Wrote coverage summary: {coverage_summary_path}")
    print(f"Wrote unmatched descriptor summary: {unmatched_descriptor_path}")
    print(f"Wrote anomaly summary: {anomaly_path}")
    print(f"Wrote resolution summary: {resolution_path}")
    if report_file is None:
        print(
            "Skipped tracked report generation. Re-run with --publish-report to update reports/."
        )
    else:
        print(f"Wrote tracked coverage chart: {coverage_chart_path}")
        print(f"Wrote tracked unmatched-descriptor chart: {descriptor_chart_path}")
        print(f"Wrote tracked anomaly chart: {anomaly_chart_path}")
        print(f"Wrote tracked resolution chart: {resolution_chart_path}")
        print(f"Wrote tracked report: {report_file}")


if __name__ == "__main__":
    main()
