from __future__ import annotations

import csv
from collections import Counter, defaultdict
from importlib import import_module
from pathlib import Path

from nyc311 import analysis, export, models, plotting, samples, spatial

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


def format_topic_name(value: str) -> str:
    return value.replace("_", " ").title()


def format_district_name(value: str) -> str:
    return value.title()


def aggregate_joined_topics(joined: object) -> list[models.GeographyTopicSummary]:
    grouped_counts: dict[tuple[str, str], int] = defaultdict(int)
    geography_totals: dict[str, int] = defaultdict(int)
    for row in joined.itertuples(index=False):
        district = str(row.boundary_geography_value)
        topic = str(row.topic)
        grouped_counts[(district, topic)] += 1
        geography_totals[district] += 1

    summaries: list[models.GeographyTopicSummary] = []
    district_topics: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for (district, topic), count in grouped_counts.items():
        district_topics[district].append((topic, count))
    for district, topic_counts in district_topics.items():
        ordered_topic_counts = sorted(
            topic_counts, key=lambda item: (-item[1], item[0])
        )
        total_count = geography_totals[district]
        for index, (topic, count) in enumerate(ordered_topic_counts, start=1):
            summaries.append(
                models.GeographyTopicSummary(
                    geography="community_district",
                    geography_value=district,
                    complaint_type="Noise - Residential",
                    topic=topic,
                    complaint_count=count,
                    geography_total_count=total_count,
                    share_of_geography=count / total_count,
                    topic_rank=index,
                    is_dominant_topic=index == 1,
                )
            )
    return sorted(
        summaries,
        key=lambda summary: (
            summary.geography_value,
            summary.topic_rank,
            summary.topic,
        ),
    )


def build_snapshot_rows(
    summaries: list[models.GeographyTopicSummary],
) -> tuple[list[dict[str, object]], list[str]]:
    topic_totals = Counter(summary.topic for summary in summaries)
    topic_order = sorted(
        topic_totals,
        key=lambda topic: (topic != "party_music", -topic_totals[topic], topic),
    )
    summaries_by_district: dict[str, list[models.GeographyTopicSummary]] = defaultdict(
        list
    )
    for summary in summaries:
        summaries_by_district[summary.geography_value].append(summary)

    snapshot_rows: list[dict[str, object]] = []
    for district, district_summaries in summaries_by_district.items():
        ordered = sorted(
            district_summaries,
            key=lambda summary: (summary.topic_rank, summary.topic),
        )
        dominant_summary = ordered[0]
        party_music_summary = next(
            (summary for summary in ordered if summary.topic == "party_music"),
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
                    0
                    if party_music_summary is None
                    else party_music_summary.complaint_count
                ),
                "party_music_share": (
                    0.0
                    if party_music_summary is None
                    else party_music_summary.share_of_geography
                ),
                "topic_shares": {
                    summary.topic: summary.share_of_geography for summary in ordered
                },
            }
        )
    return sorted(
        snapshot_rows,
        key=lambda row: (
            -float(row["party_music_share"]),
            -int(row["geography_total_count"]),
            str(row["district"]),
        ),
    ), topic_order


def build_comparison_rows(
    raw_summaries: list[models.GeographyTopicSummary],
    spatial_summaries: list[models.GeographyTopicSummary],
) -> list[dict[str, object]]:
    raw_rows, _ = build_snapshot_rows(raw_summaries)
    spatial_rows, _ = build_snapshot_rows(spatial_summaries)
    return [
        {
            "view": "Raw record label",
            "district": row["district"],
            "geography_total_count": row["geography_total_count"],
            "dominant_topic": row["dominant_topic"],
            "dominant_share": row["dominant_share"],
            "party_music_share": row["party_music_share"],
        }
        for row in raw_rows
    ] + [
        {
            "view": "Spatial join",
            "district": row["district"],
            "geography_total_count": row["geography_total_count"],
            "dominant_topic": row["dominant_topic"],
            "dominant_share": row["dominant_share"],
            "party_music_share": row["party_music_share"],
        }
        for row in spatial_rows
    ]


def build_preview_map(
    *,
    highlighted_districts_gdf: object,
    all_districts_gdf: object,
    borough_outlines: object,
    matched: object,
    unmatched: object,
) -> object:
    return plotting.plot_boundary_point_groups(
        highlighted_districts_gdf,
        title="Where do the sample noise points land in the full district layer?",
        matched_points_gdf=matched,
        unmatched_points_gdf=unmatched,
        context_gdf=all_districts_gdf,
        outline_gdf=borough_outlines,
        matched_label="Matched noise point",
        unmatched_label="Unmatched noise point",
        figsize=(10.5, 8.5),
    )


def build_dominant_map_figure(
    dominant_map: object, *, borough_outlines: object
) -> object:
    figure = plotting.plot_boundary_choropleth(
        dominant_map,
        column="topic",
        title="Dominant noise topic after spatial enrichment",
        cmap="Set2",
        categorical=True,
        figsize=(11, 10),
        outline_gdf=borough_outlines,
        legend_title="Spatially joined dominant topic",
    )
    axes = figure.axes[0]
    sampled_rows = dominant_map[dominant_map["complaint_count"] > 0]
    for row in sampled_rows.itertuples(index=False):
        point = row.geometry.representative_point()
        axes.text(
            point.x,
            point.y,
            (
                f"{format_district_name(row.geography_value)}\n"
                f"{format_topic_name(row.topic)}\n"
                f"{row.complaint_count}/{row.geography_total_count} ({row.share_of_geography:.0%})"
            ),
            ha="center",
            va="center",
            fontsize=7.5,
            bbox={
                "boxstyle": "round,pad=0.22",
                "facecolor": "white",
                "edgecolor": "#334155",
                "alpha": 0.92,
            },
        )
    return figure


def build_party_music_figure(snapshot_rows: list[dict[str, object]]) -> object:
    plt = require_matplotlib()
    percent_formatter = import_module("matplotlib.ticker").PercentFormatter
    figure, axes = plt.subplots(figsize=(8.5, 4.8))
    bars = axes.barh(
        [str(row["district"]) for row in snapshot_rows],
        [float(row["party_music_share"]) for row in snapshot_rows],
        color=[
            "#7c3aed" if float(row["party_music_share"]) > 0 else "#cbd5e1"
            for row in snapshot_rows
        ],
    )
    axes.invert_yaxis()
    axes.set_xlim(0, 1)
    axes.set_xlabel("Party music share of matched district noise complaints")
    axes.set_title("Which joined districts skew hardest toward party music?")
    axes.xaxis.set_major_formatter(percent_formatter(xmax=1))
    axes.grid(axis="x", alpha=0.25)
    for bar, row in zip(bars, snapshot_rows, strict=True):
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


def build_topic_mix_figure(
    snapshot_rows: list[dict[str, object]],
    topic_order: list[str],
) -> object:
    plt = require_matplotlib()
    percent_formatter = import_module("matplotlib.ticker").PercentFormatter
    figure, axes = plt.subplots(
        1,
        len(snapshot_rows),
        figsize=(4.2 * len(snapshot_rows), 4.8),
        sharey=True,
    )
    axes_list = [axes] if len(snapshot_rows) == 1 else list(axes)
    colormap = require_matplotlib().get_cmap("Set2", len(topic_order))
    topic_colors = {
        topic: "#7c3aed" if topic == "party_music" else colormap(index)
        for index, topic in enumerate(topic_order)
    }
    for axis, row in zip(axes_list, snapshot_rows, strict=True):
        shares = [float(row["topic_shares"].get(topic, 0.0)) for topic in topic_order]
        bars = axis.bar(
            range(len(topic_order)),
            shares,
            color=[
                topic_colors[topic] if share > 0 else "#e5e7eb"
                for topic, share in zip(topic_order, shares, strict=True)
            ],
        )
        axis.set_title(f"{row['district']}\nn={int(row['geography_total_count'])}")
        axis.set_xticks(range(len(topic_order)))
        axis.set_xticklabels(
            [format_topic_name(topic) for topic in topic_order],
            rotation=35,
            ha="right",
        )
        axis.set_ylim(0, 1)
        axis.yaxis.set_major_formatter(percent_formatter(xmax=1))
        axis.grid(axis="y", alpha=0.2)
        for bar, share in zip(bars, shares, strict=True):
            if share == 0:
                continue
            axis.text(
                bar.get_x() + bar.get_width() / 2,
                share + 0.03,
                f"{share:.0%}",
                ha="center",
                va="bottom",
                fontsize=8,
            )
    axes_list[0].set_ylabel("Share of matched district complaints")
    figure.suptitle("Normalized topic mix after spatial enrichment", y=1.02)
    return figure


def write_report(
    *,
    total_rows: int,
    matched_count: int,
    spatial_rows: list[dict[str, object]],
    comparison_rows: list[dict[str, object]],
    reassigned_rows: list[dict[str, object]],
    preview_map_path: Path,
    dominant_map_path: Path,
    party_chart_path: Path,
    topic_mix_chart_path: Path,
) -> Path:
    report_file = report_path("spatial-topic-comparison-tearsheet.md")
    top_party_row = spatial_rows[0]
    strongest_dominance = max(
        spatial_rows,
        key=lambda row: (
            float(row["dominant_share"]),
            int(row["dominant_count"]),
            -int(row["geography_total_count"]),
        ),
    )
    weakest_dominance = min(
        spatial_rows,
        key=lambda row: (
            float(row["dominant_share"]),
            -int(row["geography_total_count"]),
            str(row["district"]),
        ),
    )
    lines = [
        "# Spatial Topic Comparison Tearsheet",
        "",
        "This tearsheet compares residential-noise topics before and after spatially",
        "joining the packaged sample points to the full NYC community-district layer.",
        "",
        "## Executive Summary",
        "",
        (
            f"- The packaged sample contributes `{total_rows}` residential-noise points, "
            f"and `{matched_count}` of them land inside a district polygon when the full layer is used."
        ),
        (
            f"- The strongest party-music intensity after the spatial join appears in "
            f"`{top_party_row['district']}` at `{float(top_party_row['party_music_share']):.1%}`."
        ),
        (
            f"- The sharpest dominant-topic signal appears in `{strongest_dominance['district']}`, "
            f"where `{format_topic_name(str(strongest_dominance['dominant_topic']))}` reaches "
            f"`{float(strongest_dominance['dominant_share']):.1%}`."
        ),
        (
            f"- The most balanced joined district is `{weakest_dominance['district']}`, where the "
            f"leading topic reaches only `{float(weakest_dominance['dominant_share']):.1%}`."
        ),
        (
            f"- Spatial enrichment changes the raw district label for `{len(reassigned_rows)}` "
            "sample rows, which is why this example reports both raw and spatial district views."
        ),
        "",
        "## Spatial Join Preview",
        "",
        f"![Spatial join preview](./figures/{preview_map_path.name})",
        "",
        "## Dominant Topic Map",
        "",
        f"![Dominant topic after spatial enrichment](./figures/{dominant_map_path.name})",
        "",
        "## Party Music Intensity",
        "",
        f"![Party music intensity by joined district](./figures/{party_chart_path.name})",
        "",
        "## Topic Mix By Joined District",
        "",
        f"![Normalized topic mix after spatial enrichment](./figures/{topic_mix_chart_path.name})",
        "",
        "## Raw vs Spatial District Summary",
        "",
        "| View | District | Total complaints | Dominant topic | Dominant share | Party music share |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        "| "
        + " | ".join(
            [
                str(row["view"]),
                str(row["district"]),
                str(int(row["geography_total_count"])),
                format_topic_name(str(row["dominant_topic"])),
                f"{float(row['dominant_share']):.1%}",
                f"{float(row['party_music_share']):.1%}",
            ]
        )
        + " |"
        for row in comparison_rows
    )
    lines.extend(
        [
            "",
            "## Reassigned Rows",
            "",
            "| Request ID | Raw district | Spatial district | Topic | Descriptor |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    lines.extend(
        "| "
        + " | ".join(
            [
                str(row["service_request_id"]),
                str(row["raw_community_district"]),
                str(row["spatial_community_district"]),
                format_topic_name(str(row["topic"])),
                str(row["descriptor"]),
            ]
        )
        + " |"
        for row in reassigned_rows
    )
    lines.extend(
        [
            "",
            "## Joined District Metrics",
            "",
            "| Joined district | Total complaints | Dominant topic | Dominant share | Party music share |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    lines.extend(
        "| "
        + " | ".join(
            [
                str(row["district"]),
                str(int(row["geography_total_count"])),
                format_topic_name(str(row["dominant_topic"])),
                f"{float(row['dominant_share']):.1%}",
                f"{float(row['party_music_share']):.1%}",
            ]
        )
        + " |"
        for row in spatial_rows
    )
    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_file


def main() -> None:
    records = samples.load_sample_service_requests(
        filters=models.ServiceRequestFilter(
            complaint_types=("Noise - Residential",),
        )
    )
    if not records:
        raise RuntimeError(
            "The packaged sample slice did not return any noise records."
        )

    all_districts_gdf = spatial.load_boundaries_geodataframe(layer="community_district")
    borough_outlines = spatial.load_boundaries_geodataframe(layer="borough")
    records_gdf = spatial.records_to_geodataframe(records)
    joined = spatial.spatial_join_records_to_boundaries(records_gdf, all_districts_gdf)
    assignments = analysis.extract_topics(
        records,
        models.TopicQuery("Noise - Residential"),
    )
    raw_summaries = analysis.aggregate_by_geography(
        assignments,
        geography="community_district",
    )
    topic_lookup = {
        assignment.record.service_request_id: assignment.topic
        for assignment in assignments
    }
    joined["topic"] = joined["service_request_id"].map(topic_lookup)

    matched = joined[joined["boundary_geography_value"].notna()].copy()
    unmatched = joined[joined["boundary_geography_value"].isna()].copy()
    matched["raw_matches_spatial"] = (
        matched["community_district"] == matched["boundary_geography_value"]
    )
    spatial_summaries = aggregate_joined_topics(matched)
    if not spatial_summaries:
        raise RuntimeError(
            "The spatial join did not produce any matched topic summaries."
        )

    spatial_rows, topic_order = build_snapshot_rows(spatial_summaries)
    comparison_rows = build_comparison_rows(raw_summaries, spatial_summaries)
    reassigned_rows = [
        {
            "service_request_id": str(row.service_request_id),
            "raw_community_district": str(row.community_district),
            "spatial_community_district": str(row.boundary_geography_value),
            "topic": str(row.topic),
            "descriptor": str(row.descriptor),
        }
        for row in matched[~matched["raw_matches_spatial"]].itertuples(index=False)
    ]
    dominant_spatial_summaries = [
        summary for summary in spatial_summaries if summary.is_dominant_topic
    ]
    dominant_map = spatial.summaries_to_geodataframe(
        dominant_spatial_summaries,
        boundaries_gdf=all_districts_gdf,
    )
    dominant_map["complaint_count"] = (
        dominant_map["complaint_count"].fillna(0).astype(int)
    )
    dominant_map["geography_total_count"] = (
        dominant_map["geography_total_count"].fillna(0).astype(int)
    )
    dominant_map["share_of_geography"] = dominant_map["share_of_geography"].fillna(0.0)
    sampled_district_names = {str(row["district"]) for row in spatial_rows}
    sampled_districts_gdf = all_districts_gdf[
        all_districts_gdf["geography_value"].isin(sampled_district_names)
    ].copy()

    output_csv = artifact_path("spatial-topic-comparison.csv")
    joined_preview_path = artifact_path("spatial-topic-joined-preview.csv")
    unmatched_path = artifact_path("spatial-topic-unmatched.csv")
    comparison_path = artifact_path("spatial-topic-raw-vs-joined.csv")
    reassignment_path = artifact_path("spatial-topic-reassignments.csv")
    export.export_topic_table(
        spatial_summaries,
        models.ExportTarget("csv", output_csv),
    )
    matched[
        [
            "service_request_id",
            "community_district",
            "boundary_geography_value",
            "topic",
            "descriptor",
            "raw_matches_spatial",
        ]
    ].rename(
        columns={
            "community_district": "raw_community_district",
            "boundary_geography_value": "spatial_community_district",
        }
    ).to_csv(joined_preview_path, index=False)
    unmatched[
        [
            "service_request_id",
            "community_district",
            "descriptor",
            "latitude",
            "longitude",
        ]
    ].to_csv(unmatched_path, index=False)
    comparison_path.parent.mkdir(parents=True, exist_ok=True)
    with comparison_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "view",
                "district",
                "geography_total_count",
                "dominant_topic",
                "dominant_share",
                "party_music_share",
            ],
        )
        writer.writeheader()
        for row in comparison_rows:
            writer.writerow(row)
    with reassignment_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "service_request_id",
                "raw_community_district",
                "spatial_community_district",
                "topic",
                "descriptor",
            ],
        )
        writer.writeheader()
        for row in reassigned_rows:
            writer.writerow(row)

    preview_map_path = save_figure(
        build_preview_map(
            highlighted_districts_gdf=sampled_districts_gdf,
            all_districts_gdf=all_districts_gdf,
            borough_outlines=borough_outlines,
            matched=matched,
            unmatched=unmatched,
        ),
        report_figure_path("spatial-topic-comparison-preview.png"),
    )
    dominant_map_path = save_figure(
        build_dominant_map_figure(dominant_map, borough_outlines=borough_outlines),
        report_figure_path("spatial-dominant-noise-topics.png"),
    )
    party_chart_path = save_figure(
        build_party_music_figure(spatial_rows),
        report_figure_path("spatial-party-music-intensity.png"),
    )
    topic_mix_chart_path = save_figure(
        build_topic_mix_figure(spatial_rows, topic_order),
        report_figure_path("spatial-topic-mix-by-district.png"),
    )
    report_file = write_report(
        total_rows=len(joined),
        matched_count=len(matched),
        spatial_rows=spatial_rows,
        comparison_rows=comparison_rows,
        reassigned_rows=reassigned_rows,
        preview_map_path=preview_map_path,
        dominant_map_path=dominant_map_path,
        party_chart_path=party_chart_path,
        topic_mix_chart_path=topic_mix_chart_path,
    )

    print("Spatial Topic Comparison")
    print("------------------------")
    print(f"Wrote joined topic summary: {output_csv}")
    print(f"Wrote joined preview: {joined_preview_path}")
    print(f"Wrote unmatched rows: {unmatched_path}")
    print(f"Wrote raw-vs-joined summary: {comparison_path}")
    print(f"Wrote reassignment summary: {reassignment_path}")
    print(f"Wrote tracked preview map: {preview_map_path}")
    print(f"Wrote tracked dominant-topic map: {dominant_map_path}")
    print(f"Wrote tracked party-music chart: {party_chart_path}")
    print(f"Wrote tracked topic-mix chart: {topic_mix_chart_path}")
    print(f"Wrote tracked report: {report_file}")
    for row in spatial_rows:
        print(
            f"- {row['district']}: {format_topic_name(str(row['dominant_topic']))} "
            f"({int(row['dominant_count'])}/{int(row['geography_total_count'])}, "
            f"{float(row['dominant_share']):.1%})"
        )


if __name__ == "__main__":
    main()
