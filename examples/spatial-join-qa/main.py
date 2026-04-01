from __future__ import annotations

from importlib import import_module
from pathlib import Path

from nyc311 import plotting, samples, spatial

ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = ROOT / "artifacts"
REPORTS_DIR = ROOT / "reports"
REPORT_FIGURES_DIR = REPORTS_DIR / "figures"


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
        title="Where do packaged sample points land against the sampled district subset?",
        matched_points_gdf=matched,
        unmatched_points_gdf=unmatched,
        context_gdf=context_gdf,
        outline_gdf=borough_outlines,
        matched_label="Matched within sampled subset",
        unmatched_label="Outside sampled subset",
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
    axes.set_title("How often does the sampled spatial join succeed?")
    axes.set_ylabel("Point count")
    axes.set_ylim(0, max(counts) + 1)
    axes.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    secondary = axes.twinx()
    secondary.set_ylim(0, 1)
    secondary.yaxis.set_major_formatter(percent_formatter(xmax=1))
    secondary.set_ylabel("Share of packaged sample points")
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
    figure, axes = plt.subplots(figsize=(8.5, 5))
    bars = axes.barh(
        [str(row["boundary_geography_value"]) for row in joined_counts],
        [int(row["count"]) for row in joined_counts],
        color="#2563eb",
    )
    axes.invert_yaxis()
    axes.set_xlabel("Matched record count")
    axes.set_title("Which sampled districts receive the most matched sample points?")
    axes.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    axes.grid(axis="x", alpha=0.25)
    max_count = max(int(row["count"]) for row in joined_counts)
    axes.set_xlim(0, max_count * 1.18)
    for bar, row in zip(bars, joined_counts, strict=True):
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
    total_records: int,
    matched_count: int,
    unmatched_count: int,
    agreement_count: int,
    agreement_total: int,
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
    coverage_rate = matched_count / total_records
    agreement_rate = 0.0 if agreement_total == 0 else agreement_count / agreement_total
    unmatched_boundary_names = [
        str(row.geography_value)
        for row in boundary_summary.itertuples(index=False)
        if int(row.matched_point_count) == 0
    ]
    top_joined_row = joined_counts[0]
    lines = [
        "# Spatial Join QA Tearsheet",
        "",
        "This canonical example audits the packaged sample points against the packaged",
        "sample-aligned `community_district` subset, then turns the results into one",
        "report that covers join success, unmatched rows, boundary coverage, and raw-vs-spatial agreement.",
        "",
        "## Executive Summary",
        "",
        (
            f"- The packaged sample contains `{total_records}` point-capable service "
            f"requests and the sampled spatial join succeeds for `{matched_count}` of them "
            f"(`{coverage_rate:.1%}`)."
        ),
        (
            f"- `{unmatched_count}` rows remain outside every polygon in the sampled "
            "boundary subset."
        ),
        (
            f"- Raw district text agrees with the spatial join for "
            f"`{agreement_rate:.1%}` of matched rows (`{agreement_count}` of `{agreement_total}`)."
            if agreement_total
            else "- No rows land inside the sampled polygons, so text-vs-spatial agreement is unavailable."
        ),
        (
            "- Every packaged sample polygon receives at least one matched point."
            if not unmatched_boundary_names
            else (
                "- The following sampled polygons receive no matched sample points: "
                f"`{', '.join(unmatched_boundary_names)}`."
            )
        ),
        (
            f"- The busiest sampled polygon is `{top_joined_row['boundary_geography_value']}` "
            f"with `{int(top_joined_row['count'])}` matched records."
        ),
        "",
        "## Match Status Map",
        "",
        f"![Matched versus unmatched sample points](./figures/{map_image_path.name})",
        "",
        "## Coverage Breakdown",
        "",
        f"![Matched versus unmatched breakdown](./figures/{coverage_image_path.name})",
        "",
        "## Joined District Counts",
        "",
        f"![Matched records by sampled district](./figures/{district_chart_path.name})",
        "",
        "## Boundary Geometry Inventory",
        "",
        "| Boundary | Geometry type | Matched point count |",
        "| --- | --- | --- |",
    ]
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
            "## Joined District Metrics",
            "",
            "| Sampled district | Matched count |",
            "| --- | --- |",
        ]
    )
    lines.extend(
        f"| {row['boundary_geography_value']} | {int(row['count'])} |"
        for row in joined_counts
    )
    lines.extend(
        [
            "",
            "## Agreement Summary",
            "",
            "Scratch QA tables are available under `artifacts/`:",
            (
                f"`{unmatched_points_path.name}`, `{text_vs_spatial_path.name}`, and "
                f"`{joined_counts_path.name}`."
            ),
            "",
            "| Metric | Value |",
            "| --- | --- |",
            f"| Matched rows | {matched_count} |",
            f"| Unmatched rows | {unmatched_count} |",
            f"| Agreement rows | {agreement_count} |",
            f"| Agreement rate among matched rows | {agreement_rate:.1%} |",
        ]
    )
    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_file


def main() -> None:
    records = samples.load_sample_service_requests()
    records_gdf = spatial.records_to_geodataframe(records)
    sample_boundaries = samples.load_sample_boundaries("community_district")
    boundaries_gdf = spatial.load_boundaries_geodataframe(sample_boundaries)
    context_gdf = spatial.load_boundaries_geodataframe(layer="community_district")
    borough_outlines = spatial.load_boundaries_geodataframe(layer="borough")
    joined = spatial.spatial_join_records_to_boundaries(records_gdf, boundaries_gdf)
    matched = joined[joined["boundary_geography_value"].notna()].copy()
    unmatched = joined[joined["boundary_geography_value"].isna()].copy()
    matched["raw_matches_spatial"] = (
        matched["community_district"] == matched["boundary_geography_value"]
    )

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

    boundary_summary_path = artifact_path("spatial-join-qa-boundary-summary.csv")
    join_preview_path = artifact_path("spatial-join-qa-join-preview.csv")
    unmatched_path = artifact_path("spatial-join-qa-unmatched-points.csv")
    comparison_path = artifact_path("spatial-join-qa-text-vs-spatial.csv")
    joined_counts_path = artifact_path("spatial-join-qa-joined-district-counts.csv")
    boundary_summary.to_csv(boundary_summary_path, index=False)
    join_preview.to_csv(join_preview_path, index=False)
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
    joined_counts_frame.to_csv(joined_counts_path, index=False)

    matched_count = len(matched)
    unmatched_count = len(unmatched)
    agreement_count = int(matched["raw_matches_spatial"].sum())
    match_status_path = save_figure(
        build_match_status_map(
            boundaries_gdf,
            joined,
            context_gdf=context_gdf,
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
        total_records=len(joined),
        matched_count=matched_count,
        unmatched_count=unmatched_count,
        agreement_count=agreement_count,
        agreement_total=len(matched),
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
    print(f"Wrote boundary summary: {boundary_summary_path}")
    print(f"Wrote join preview: {join_preview_path}")
    print(f"Wrote unmatched-point table: {unmatched_path}")
    print(f"Wrote text-vs-spatial table: {comparison_path}")
    print(f"Wrote joined-district counts: {joined_counts_path}")
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
