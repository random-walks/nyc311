from __future__ import annotations

import argparse
import csv
import os
from collections import Counter
from datetime import date
from importlib import import_module
from pathlib import Path

from nyc311 import io, models, pipeline, plotting, spatial

ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / "cache"
ARTIFACTS_DIR = ROOT / "artifacts"
REPORTS_DIR = ROOT / "reports"
REPORT_FIGURES_DIR = REPORTS_DIR / "figures"
DEFAULT_START_DATE = "2025-01-01"
DEFAULT_END_DATE = "2025-01-31"
DEFAULT_PAGE_SIZE = 1_000
DEFAULT_MAX_PAGES = 15
DEFAULT_COMPLAINT_TYPES = (
    "Illegal Parking",
    "Blocked Driveway",
    "Street Condition",
    "Abandoned Vehicle",
    "Traffic Signal Condition",
)
DISTRICT_CHART_LIMIT = 15
REPORT_COMPLAINT_LIMIT = 10
REPORT_DISTRICT_LIMIT = 15


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
        description="Audit a cached live 311 slice against the full community-district layer.",
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
    snapshot_path = cache_path("spatial-join-qa-snapshot.csv")
    if snapshot_path.exists() and not refresh:
        return io.load_service_requests(snapshot_path), "cache", snapshot_path

    records = pipeline.fetch_service_requests(
        filters=models.ServiceRequestFilter(
            start_date=date.fromisoformat(DEFAULT_START_DATE),
            end_date=date.fromisoformat(DEFAULT_END_DATE),
            complaint_types=DEFAULT_COMPLAINT_TYPES,
        ),
        socrata_config=models.SocrataConfig(
            app_token=app_token,
            page_size=DEFAULT_PAGE_SIZE,
            max_pages=DEFAULT_MAX_PAGES,
        ),
        output=snapshot_path,
    )
    return records, "live fetch", snapshot_path


def build_match_status_map(
    boundaries_gdf: object,
    joined: object,
    *,
    context_gdf: object,
    borough_outlines: object,
) -> object:
    matched = joined[joined["boundary_geography_value"].notna()]
    unmatched = joined[joined["boundary_geography_value"].isna()]
    return plotting.plot_boundary_point_groups(
        boundaries_gdf,
        title="Where do cached live requests land against the district layer?",
        matched_points_gdf=matched,
        unmatched_points_gdf=unmatched,
        context_gdf=context_gdf,
        outline_gdf=borough_outlines,
        matched_label="Matched to a district",
        unmatched_label="Outside every district polygon",
        figsize=(10.5, 8.5),
    )


def build_coverage_figure(*, matched_count: int, unmatched_count: int) -> object:
    plt = require_matplotlib()
    percent_formatter = import_module("matplotlib.ticker").PercentFormatter
    total_records = matched_count + unmatched_count
    figure, axes = plt.subplots(figsize=(7, 4.5))
    labels = ["Matched", "Unmatched"]
    counts = [matched_count, unmatched_count]
    colors = ["#16a34a", "#dc2626"]
    bars = axes.bar(labels, counts, color=colors)
    axes.set_title("How often does the spatial join succeed on the cached slice?")
    axes.set_ylabel("Point count")
    axes.set_ylim(0, max(counts) + 1)
    axes.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    secondary = axes.twinx()
    secondary.set_ylim(0, 1)
    secondary.yaxis.set_major_formatter(percent_formatter(xmax=1))
    secondary.set_ylabel("Share of point-capable cached requests")
    for bar, count in zip(bars, counts, strict=True):
        share = 0 if total_records == 0 else count / total_records
        axes.text(
            bar.get_x() + bar.get_width() / 2,
            count + 0.05,
            f"{count} ({share:.1%})",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    return figure


def build_joined_districts_figure(joined_counts: list[dict[str, object]]) -> object:
    plt = require_matplotlib()
    plot_rows = joined_counts[:DISTRICT_CHART_LIMIT]
    figure, axes = plt.subplots(figsize=(8.5, 5))
    bars = axes.barh(
        [str(row["boundary_geography_value"]) for row in plot_rows],
        [int(row["count"]) for row in plot_rows],
        color="#2563eb",
    )
    axes.invert_yaxis()
    axes.set_xlabel("Matched record count")
    axes.set_title("Which community districts receive the most joined requests?")
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


def write_report(
    *,
    source: str,
    snapshot_path: Path,
    total_records: int,
    point_capable_count: int,
    matched_count: int,
    unmatched_count: int,
    agreement_count: int,
    agreement_total: int,
    complaint_rows: list[dict[str, object]],
    complaint_mix_path: Path,
    unmatched_points_path: Path,
    text_vs_spatial_path: Path,
    joined_counts_path: Path,
    boundary_summary: object,
    joined_counts: list[dict[str, object]],
    map_image_path: Path,
    coverage_image_path: Path,
    district_chart_path: Path,
) -> Path:
    report_file = report_path("spatial-join-qa-tearsheet.md")
    coverage_rate = matched_count / point_capable_count
    agreement_rate = 0.0 if agreement_total == 0 else agreement_count / agreement_total
    unmatched_boundary_names = [
        str(row.geography_value)
        for row in boundary_summary.itertuples(index=False)
        if int(row.matched_point_count) == 0
    ]
    matched_boundary_count = sum(
        int(row.matched_point_count) > 0
        for row in boundary_summary.itertuples(index=False)
    )
    top_complaint_row = complaint_rows[0]
    top_joined_row = joined_counts[0]
    top_joined_rows = joined_counts[:REPORT_DISTRICT_LIMIT]
    lines = [
        "# Spatial Join QA Tearsheet",
        "",
        "This canonical example audits a cached live 311 slice against the full NYC",
        "community-district layer, then turns the result into one QA report covering",
        "join success, unmatched rows, district coverage, and raw-vs-spatial agreement.",
        "",
        "## Executive Summary",
        "",
        (
            f"- The cached slice contains `{total_records}` requests from `{source}` using "
            f"`cache/{snapshot_path.name}`. `{point_capable_count}` of those rows carry usable "
            "coordinates for point-in-polygon QA."
        ),
        (
            f"- The largest complaint group in the QA slice is "
            f"`{top_complaint_row['complaint_type']}` with `{int(top_complaint_row['count'])}` "
            f"rows ({float(top_complaint_row['share']):.1%} of the slice)."
        ),
        (
            f"- The spatial join succeeds for `{matched_count}` of the "
            f"`{point_capable_count}` point-capable rows "
            f"(`{coverage_rate:.1%}`)."
        ),
        (
            f"- `{unmatched_count}` rows remain outside every polygon in the "
            "district layer."
        ),
        (
            f"- Raw district text agrees with the spatial join for "
            f"`{agreement_rate:.1%}` of matched rows (`{agreement_count}` of `{agreement_total}`)."
            if agreement_total
            else "- No rows land inside district polygons, so text-vs-spatial agreement is unavailable."
        ),
        (
            f"- `{matched_boundary_count}` of `{len(boundary_summary)}` community districts "
            "receive at least one joined request."
        ),
        (
            "- Every district polygon receives at least one matched point."
            if not unmatched_boundary_names
            else (
                "- Districts with zero matched requests include "
                f"`{', '.join(unmatched_boundary_names[:10])}`"
                + (" and others." if len(unmatched_boundary_names) > 10 else ".")
            )
        ),
        (
            f"- The busiest joined district is `{top_joined_row['boundary_geography_value']}` "
            f"with `{int(top_joined_row['count'])}` matched records."
        ),
        "",
        "## Match Status Map",
        "",
        f"![Matched versus unmatched cached requests](./figures/{map_image_path.name})",
        "",
        "## Coverage Breakdown",
        "",
        f"![Matched versus unmatched breakdown](./figures/{coverage_image_path.name})",
        "",
        "## Joined District Counts",
        "",
        f"![Matched records by joined district](./figures/{district_chart_path.name})",
        "",
        "## Complaint Mix",
        "",
        "| Complaint type | Count | Share of cached slice |",
        "| --- | --- | --- |",
    ]
    lines.extend(
        "| "
        + " | ".join(
            [
                str(row["complaint_type"]),
                str(int(row["count"])),
                f"{float(row['share']):.1%}",
            ]
        )
        + " |"
        for row in complaint_rows[:REPORT_COMPLAINT_LIMIT]
    )
    lines.extend(
        [
            "",
            "## Joined District Metrics",
            "",
            "| District | Matched count |",
            "| --- | --- |",
        ]
    )
    lines.extend(
        f"| {row['boundary_geography_value']} | {int(row['count'])} |"
        for row in top_joined_rows
    )
    lines.extend(
        [
            "",
            "## Boundary Geometry Inventory",
            "",
            "| Boundary | Geometry type | Matched point count |",
            "| --- | --- | --- |",
        ]
    )
    lines.extend(
        "| "
        + " | ".join(
            [
                str(row.geography_value),
                str(row.geometry_type),
                str(int(row.matched_point_count)),
            ]
        )
        + " |"
        for row in boundary_summary.itertuples(index=False)
    )
    lines.extend(
        [
            "",
            "## Agreement Summary",
            "",
            "Scratch QA tables are available under `artifacts/`:",
            (
                f"`{complaint_mix_path.name}`, `{unmatched_points_path.name}`, "
                f"`{text_vs_spatial_path.name}`, and `{joined_counts_path.name}`."
            ),
            "",
            "| Metric | Value |",
            "| --- | --- |",
            f"| Cached rows | {total_records} |",
            f"| Point-capable rows | {point_capable_count} |",
            f"| Matched rows | {matched_count} |",
            f"| Unmatched rows | {unmatched_count} |",
            f"| Agreement rows | {agreement_count} |",
            f"| Agreement rate among matched rows | {agreement_rate:.1%} |",
        ]
    )
    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_file


def main() -> None:
    args = build_parser().parse_args()
    records, source, snapshot_path = load_records(args.refresh, args.app_token)
    if not records:
        raise RuntimeError(
            "The cached spatial-join QA slice did not return any records."
        )
    records_gdf = spatial.records_to_geodataframe(records)
    boundaries_gdf = spatial.load_boundaries_geodataframe(layer="community_district")
    borough_outlines = spatial.load_boundaries_geodataframe(layer="borough")
    joined = spatial.spatial_join_records_to_boundaries(records_gdf, boundaries_gdf)
    if joined.empty:
        raise RuntimeError(
            "The cached spatial-join QA slice did not include any point-capable records."
        )
    matched = joined[joined["boundary_geography_value"].notna()].copy()
    unmatched = joined[joined["boundary_geography_value"].isna()].copy()
    matched["raw_matches_spatial"] = (
        matched["community_district"] == matched["boundary_geography_value"]
    )
    complaint_counts = Counter(record.complaint_type for record in records)
    complaint_rows = [
        {
            "complaint_type": complaint_type,
            "count": count,
            "share": count / len(records),
        }
        for complaint_type, count in complaint_counts.most_common()
    ]

    boundary_counts = (
        matched.groupby("boundary_geography_value")
        .size()
        .rename("matched_point_count")
        .reset_index()
    )
    boundary_summary = (
        boundaries_gdf.assign(
            geometry_type=boundaries_gdf.geometry.geom_type,
        )[["geography", "geography_value", "geometry_type"]]
        .merge(
            boundary_counts,
            left_on="geography_value",
            right_on="boundary_geography_value",
            how="left",
        )
        .drop(columns="boundary_geography_value")
        .fillna({"matched_point_count": 0})
    )
    boundary_summary["matched_point_count"] = boundary_summary[
        "matched_point_count"
    ].astype(int)

    join_preview = joined[
        [
            "service_request_id",
            "complaint_type",
            "community_district",
            "boundary_geography_value",
            "descriptor",
        ]
    ]
    joined_counts_frame = (
        matched.groupby("boundary_geography_value")
        .size()
        .rename("count")
        .reset_index()
        .sort_values(["count", "boundary_geography_value"], ascending=[False, True])
    )
    joined_counts = joined_counts_frame.to_dict(orient="records")
    if not joined_counts:
        raise RuntimeError(
            "The spatial join did not produce any matched district counts."
        )

    boundary_summary_path = artifact_path("spatial-join-qa-boundary-summary.csv")
    join_preview_path = artifact_path("spatial-join-qa-join-preview.csv")
    unmatched_path = artifact_path("spatial-join-qa-unmatched-points.csv")
    comparison_path = artifact_path("spatial-join-qa-text-vs-spatial.csv")
    joined_counts_path = artifact_path("spatial-join-qa-joined-district-counts.csv")
    complaint_mix_path = artifact_path("spatial-join-qa-complaint-mix.csv")
    boundary_summary.to_csv(boundary_summary_path, index=False)
    join_preview.to_csv(join_preview_path, index=False)
    matched[
        [
            "service_request_id",
            "complaint_type",
            "borough",
            "community_district",
            "boundary_geography_value",
            "raw_matches_spatial",
        ]
    ].rename(columns={"boundary_geography_value": "spatial_community_district"}).to_csv(
        comparison_path, index=False
    )
    write_csv_rows(
        complaint_mix_path,
        fieldnames=["complaint_type", "count", "share"],
        rows=complaint_rows,
    )
    unmatched[
        [
            "service_request_id",
            "complaint_type",
            "borough",
            "community_district",
            "descriptor",
            "latitude",
            "longitude",
        ]
    ].to_csv(unmatched_path, index=False)
    joined_counts_frame.to_csv(joined_counts_path, index=False)

    matched_count = len(matched)
    unmatched_count = len(unmatched)
    agreement_count = int(matched["raw_matches_spatial"].sum())
    report_file: Path | None = None
    match_status_path: Path | None = None
    coverage_path: Path | None = None
    district_chart_path: Path | None = None
    if args.publish_report:
        match_status_path = save_figure(
            build_match_status_map(
                boundaries_gdf,
                joined,
                context_gdf=boundaries_gdf,
                borough_outlines=borough_outlines,
            ),
            report_figure_path("spatial-join-qa-match-status-map.png"),
        )
        coverage_path = save_figure(
            build_coverage_figure(
                matched_count=matched_count,
                unmatched_count=unmatched_count,
            ),
            report_figure_path("spatial-join-qa-coverage-breakdown.png"),
        )
        district_chart_path = save_figure(
            build_joined_districts_figure(joined_counts),
            report_figure_path("spatial-join-qa-joined-district-counts.png"),
        )
        report_file = write_report(
            source=source,
            snapshot_path=snapshot_path,
            total_records=len(records),
            point_capable_count=len(joined),
            matched_count=matched_count,
            unmatched_count=unmatched_count,
            agreement_count=agreement_count,
            agreement_total=len(matched),
            complaint_rows=complaint_rows,
            complaint_mix_path=complaint_mix_path,
            unmatched_points_path=unmatched_path,
            text_vs_spatial_path=comparison_path,
            joined_counts_path=joined_counts_path,
            boundary_summary=boundary_summary,
            joined_counts=joined_counts,
            map_image_path=match_status_path,
            coverage_image_path=coverage_path,
            district_chart_path=district_chart_path,
        )

    print("Spatial Join QA")
    print("---------------")
    print(f"Record source: {source}")
    print(f"Cache path: {snapshot_path}")
    print(f"Loaded records: {len(records)}")
    print(f"Point-capable rows: {len(joined)}")
    print(f"Wrote boundary summary: {boundary_summary_path}")
    print(f"Wrote join preview: {join_preview_path}")
    print(f"Wrote complaint mix: {complaint_mix_path}")
    print(f"Wrote unmatched-point table: {unmatched_path}")
    print(f"Wrote text-vs-spatial table: {comparison_path}")
    print(f"Wrote joined-district counts: {joined_counts_path}")
    if report_file is None:
        print(
            "Skipped tracked report generation. Re-run with --publish-report to update reports/."
        )
    else:
        print(f"Wrote tracked map: {match_status_path}")
        print(f"Wrote tracked coverage chart: {coverage_path}")
        print(f"Wrote tracked joined-district chart: {district_chart_path}")
        print(f"Wrote tracked report: {report_file}")
    print(
        "Join coverage: "
        f"{matched_count}/{len(joined)} ({matched_count / len(joined):.1%})"
    )
    print(
        "Text-vs-spatial agreement among matched rows: "
        f"{agreement_count}/{len(matched)} "
        f"({0 if not len(matched) else agreement_count / len(matched):.1%})"
    )
    for row in boundary_summary.itertuples(index=False):
        print(
            f"- {row.geography_value}: {row.geometry_type}, "
            f"{int(row.matched_point_count)} matched points"
        )


if __name__ == "__main__":
    main()
