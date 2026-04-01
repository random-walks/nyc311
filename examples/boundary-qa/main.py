from __future__ import annotations

from importlib import import_module
from pathlib import Path

from nyc311 import geographies, plotting, samples, spatial

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


def format_match_label(value: bool) -> str:
    return "Yes" if value else "No"


def write_report(
    *,
    total_records: int,
    matched_count: int,
    unmatched_count: int,
    agreement_count: int,
    agreement_total: int,
    unmatched_points_path: Path,
    text_vs_spatial_path: Path,
    boundary_summary: object,
    map_image_path: Path,
    coverage_image_path: Path,
) -> Path:
    report_file = report_path("boundary-qa-tearsheet.md")
    coverage_rate = matched_count / total_records
    agreement_rate = 0.0 if agreement_total == 0 else agreement_count / agreement_total
    unmatched_boundary_names = [
        str(row.geography_value)
        for row in boundary_summary.itertuples(index=False)
        if int(row.matched_point_count) == 0
    ]
    lines = [
        "# Boundary QA Tearsheet",
        "",
        "This tearsheet audits the packaged sample points against the packaged",
        "`community_district` boundary layer. Treat the metrics here as a geometry",
        "sanity check for the sample assets, not a citywide production coverage test.",
        "",
        "## Executive Summary",
        "",
        (
            f"- The packaged sample contains `{total_records}` point-capable service "
            f"requests and `{len(boundary_summary)}` packaged sample-aligned polygons."
        ),
        (
            f"- Spatial join coverage is `{coverage_rate:.1%}` with `{matched_count}` "
            f"matched points and `{unmatched_count}` unmatched points."
        ),
        (
            f"- Raw district text agrees with the spatial join for "
            f"`{agreement_rate:.1%}` of matched rows "
            f"(`{agreement_count}` of `{agreement_total}`)."
            if agreement_total
            else "- No rows landed inside a polygon, so text-vs-spatial agreement is unavailable."
        ),
        (
            "- Every packaged sample polygon receives at least one matched point."
            if not unmatched_boundary_names
            else (
                "- The following packaged polygons receive no matched sample points: "
                f"`{', '.join(unmatched_boundary_names)}`."
            )
        ),
        (
            f"- Scratch QA tables are available at `{unmatched_points_path.name}` and "
            f"`{text_vs_spatial_path.name}` under `artifacts/`."
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
        "## Boundary Geometry Inventory",
        "",
        "| Boundary | Geometry type | Matched point count |",
        "| --- | --- | --- |",
    ]
    for row in boundary_summary.itertuples(index=False):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.geography_value),
                    str(row.geometry_type),
                    str(int(row.matched_point_count)),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Text vs Spatial Agreement",
            "",
            "The detailed agreement table lives in `artifacts/`, but the summary rule is",
            "simple: compare the raw `community_district` text on each record with the",
            "joined `boundary_geography_value` after the spatial overlay.",
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
    axes.set_title("How many packaged sample points join successfully?")
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


def main() -> None:
    records = samples.load_sample_service_requests()
    sample_boundaries = samples.load_sample_boundaries("community_district")
    boundaries_gdf = spatial.load_boundaries_geodataframe(sample_boundaries)
    context_gdf = spatial.load_boundaries_geodataframe(layer="community_district")
    borough_outlines = spatial.load_boundaries_geodataframe(layer="borough")
    joined = geographies.spatially_enrich_records(records, boundaries=sample_boundaries)
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

    summary_path = artifact_path("boundary-summary.csv")
    unmatched_path = artifact_path("boundary-unmatched-points.csv")
    comparison_path = artifact_path("boundary-text-vs-spatial.csv")
    boundary_summary.to_csv(summary_path, index=False)
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
    ].rename(
        columns={"boundary_geography_value": "spatial_community_district"}
    ).to_csv(comparison_path, index=False)

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
        report_figure_path("boundary-match-status-map.png"),
    )
    coverage_path = save_figure(
        build_coverage_figure(
            matched_count=matched_count,
            unmatched_count=unmatched_count,
        ),
        report_figure_path("boundary-coverage-breakdown.png"),
    )
    report_file = write_report(
        total_records=len(joined),
        matched_count=matched_count,
        unmatched_count=unmatched_count,
        agreement_count=agreement_count,
        agreement_total=len(matched),
        unmatched_points_path=unmatched_path,
        text_vs_spatial_path=comparison_path,
        boundary_summary=boundary_summary,
        map_image_path=match_status_path,
        coverage_image_path=coverage_path,
    )

    print("Boundary QA")
    print("-----------")
    print(f"Wrote boundary summary: {summary_path}")
    print(f"Wrote unmatched-point table: {unmatched_path}")
    print(f"Wrote text-vs-spatial table: {comparison_path}")
    print(f"Wrote tracked map: {match_status_path}")
    print(f"Wrote tracked coverage chart: {coverage_path}")
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
