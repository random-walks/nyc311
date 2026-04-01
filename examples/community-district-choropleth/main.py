from __future__ import annotations

import argparse
import os
from collections import Counter
from datetime import date
from importlib import import_module
from pathlib import Path

from nyc311 import analysis, export, io, models, pipeline, plotting, spatial

ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / "cache"
ARTIFACTS_DIR = ROOT / "artifacts"
REPORTS_DIR = ROOT / "reports"
REPORT_FIGURES_DIR = REPORTS_DIR / "figures"
DEFAULT_START_DATE = "2025-01-01"
DEFAULT_END_DATE = "2025-03-31"
DEFAULT_PAGE_SIZE = 1_000
DEFAULT_MAX_PAGES = 15
MAP_LABEL_LIMIT = 12
PARTY_CHART_LIMIT = 12
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a district-level choropleth from a cached live noise slice.",
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
    snapshot_path = cache_path("community-district-noise-snapshot.csv")
    if snapshot_path.exists() and not refresh:
        return io.load_service_requests(snapshot_path), "cache", snapshot_path

    records = pipeline.fetch_service_requests(
        filters=models.ServiceRequestFilter(
            start_date=date.fromisoformat(DEFAULT_START_DATE),
            end_date=date.fromisoformat(DEFAULT_END_DATE),
            geography=models.GeographyFilter("borough", models.BOROUGH_BROOKLYN),
            complaint_types=("Noise - Residential",),
        ),
        socrata_config=models.SocrataConfig(
            app_token=app_token,
            page_size=DEFAULT_PAGE_SIZE,
            max_pages=DEFAULT_MAX_PAGES,
        ),
        output=snapshot_path,
    )
    return records, "live fetch", snapshot_path


def format_topic_name(value: str | None) -> str:
    if not isinstance(value, str) or not value:
        return "No sample data"
    return value.replace("_", " ").title()


def format_district_name(value: str) -> str:
    return value.title()


def sampled_snapshot_rows(
    snapshot_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    return [row for row in snapshot_rows if int(row["geography_total_count"]) > 0]


def select_label_rows(dominant_map: object) -> object:
    return (
        dominant_map[dominant_map["complaint_count"] > 0]
        .sort_values(
            ["geography_total_count", "share_of_geography", "geography_value"],
            ascending=[False, False, True],
        )
        .head(MAP_LABEL_LIMIT)
    )


def build_snapshot_rows(
    all_districts_gdf: object,
    summaries: list[models.GeographyTopicSummary],
) -> tuple[list[dict[str, object]], list[str]]:
    topic_totals = Counter(summary.topic for summary in summaries)
    topic_order = sorted(
        topic_totals,
        key=lambda topic: (topic != "party_music", -topic_totals[topic], topic),
    )
    summaries_by_district: dict[str, list[models.GeographyTopicSummary]] = {}
    for summary in summaries:
        summaries_by_district.setdefault(summary.geography_value, []).append(summary)

    snapshot_rows: list[dict[str, object]] = []
    for row in all_districts_gdf[["geography_value"]].itertuples(index=False):
        district = str(row.geography_value)
        district_summaries = sorted(
            summaries_by_district.get(district, []),
            key=lambda summary: (summary.topic_rank, summary.topic),
        )
        total_count = (
            district_summaries[0].geography_total_count if district_summaries else 0
        )
        dominant_summary = district_summaries[0] if district_summaries else None
        party_music_summary = next(
            (
                summary
                for summary in district_summaries
                if summary.topic == "party_music"
            ),
            None,
        )
        topic_shares = {
            summary.topic: summary.share_of_geography for summary in district_summaries
        }
        snapshot_rows.append(
            {
                "geography_value": district,
                "geography_total_count": total_count,
                "dominant_topic": (
                    None if dominant_summary is None else dominant_summary.topic
                ),
                "dominant_count": (
                    0 if dominant_summary is None else dominant_summary.complaint_count
                ),
                "dominant_share": (
                    0.0
                    if dominant_summary is None
                    else dominant_summary.share_of_geography
                ),
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
                "topic_shares": topic_shares,
            }
        )
    return snapshot_rows, topic_order


def build_map_figure(dominant_map: object, *, borough_outlines: object) -> object:
    figure = plotting.plot_boundary_choropleth(
        dominant_map,
        column="topic",
        title="Dominant noise topic by community district",
        cmap="Set2",
        categorical=True,
        figsize=(11, 10),
        outline_gdf=borough_outlines,
        legend_title="Dominant topic",
    )
    axes = figure.axes[0]
    for row in select_label_rows(dominant_map).itertuples(index=False):
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


def build_party_music_intensity_figure(
    snapshot_rows: list[dict[str, object]],
) -> object:
    plt = require_matplotlib()
    percent_formatter = import_module("matplotlib.ticker").PercentFormatter
    plot_rows = sorted(
        sampled_snapshot_rows(snapshot_rows),
        key=lambda row: (
            -float(row["party_music_share"]),
            -int(row["geography_total_count"]),
            str(row["geography_value"]),
        ),
    )[:PARTY_CHART_LIMIT]
    figure, axes = plt.subplots(figsize=(9, 6))
    bars = axes.barh(
        [str(row["geography_value"]) for row in plot_rows],
        [float(row["party_music_share"]) for row in plot_rows],
        color=[
            "#7c3aed" if float(row["party_music_share"]) > 0 else "#cbd5e1"
            for row in plot_rows
        ],
    )
    axes.invert_yaxis()
    axes.set_xlim(0, 1)
    axes.set_xlabel("Party music share of district noise complaints")
    axes.set_title(
        "Which districts in the cached slice skew hardest toward party music?"
    )
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


def build_topic_mix_figure(
    snapshot_rows: list[dict[str, object]],
    topic_order: list[str],
) -> object:
    plt = require_matplotlib()
    percent_formatter = import_module("matplotlib.ticker").PercentFormatter
    plot_rows = sorted(
        sampled_snapshot_rows(snapshot_rows),
        key=lambda row: (
            -float(row["dominant_share"]),
            -int(row["geography_total_count"]),
            str(row["geography_value"]),
        ),
    )[:6]
    figure, axes = plt.subplots(
        1,
        len(plot_rows),
        figsize=(4.2 * len(plot_rows), 4.8),
        sharey=True,
    )
    axes_list = [axes] if len(plot_rows) == 1 else list(axes)
    colormap = require_matplotlib().get_cmap("Set2", len(topic_order))
    topic_colors = {
        topic: "#7c3aed" if topic == "party_music" else colormap(index)
        for index, topic in enumerate(topic_order)
    }
    for axis, row in zip(axes_list, plot_rows, strict=True):
        shares = [float(row["topic_shares"].get(topic, 0.0)) for topic in topic_order]
        bars = axis.bar(
            range(len(topic_order)),
            shares,
            color=[
                topic_colors[topic] if share > 0 else "#e5e7eb"
                for topic, share in zip(topic_order, shares, strict=True)
            ],
        )
        axis.set_title(
            f"{row['geography_value']}\nn={int(row['geography_total_count'])}"
        )
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
    axes_list[0].set_ylabel("Share of district noise complaints")
    figure.suptitle(
        "Top districts in the cached slice by dominant-topic strength", y=1.02
    )
    return figure


def write_report(
    *,
    source: str,
    snapshot_path: Path,
    records: list[models.ServiceRequestRecord],
    snapshot_rows: list[dict[str, object]],
    map_image_path: Path,
    party_music_image_path: Path,
    topic_mix_image_path: Path,
) -> Path:
    report_file = report_path("community-district-choropleth-tearsheet.md")
    sampled_rows = sampled_snapshot_rows(snapshot_rows)
    report_rows = sorted(
        sampled_rows,
        key=lambda item: (
            -float(item["party_music_share"]),
            -int(item["geography_total_count"]),
            str(item["geography_value"]),
        ),
    )[:REPORT_DISTRICT_LIMIT]
    total_districts = len(snapshot_rows)
    missing_count = total_districts - len(sampled_rows)
    top_party_row = max(
        sampled_rows,
        key=lambda row: (
            float(row["party_music_share"]),
            int(row["party_music_count"]),
            -int(row["geography_total_count"]),
        ),
    )
    strongest_dominance = max(
        sampled_rows,
        key=lambda row: (
            float(row["dominant_share"]),
            int(row["dominant_count"]),
            -int(row["geography_total_count"]),
        ),
    )
    weakest_dominance = min(
        sampled_rows,
        key=lambda row: (
            float(row["dominant_share"]),
            -int(row["geography_total_count"]),
            str(row["geography_value"]),
        ),
    )
    lines = [
        "# Community District Choropleth Tearsheet",
        "",
        "This tearsheet summarizes a cached live `Noise - Residential` slice at the",
        "community-district level. The map uses the full NYC district layer so grey",
        "polygons show where the cached slice has no district-level coverage.",
        "",
        "## Executive Summary",
        "",
        (
            f"- The cached slice contains `{len(records)}` noise complaints from `{source}` "
            f"using `cache/{snapshot_path.name}` across `{len(sampled_rows)}` sampled districts."
        ),
        (
            f"- The strongest party-music intensity appears in "
            f"`{top_party_row['geography_value']}` at "
            f"`{float(top_party_row['party_music_share']):.1%}` "
            f"({int(top_party_row['party_music_count'])} of "
            f"{int(top_party_row['geography_total_count'])})."
        ),
        (
            f"- The sharpest dominant-topic signal appears in "
            f"`{strongest_dominance['geography_value']}`, where "
            f"`{format_topic_name(str(strongest_dominance['dominant_topic']))}` accounts for "
            f"`{float(strongest_dominance['dominant_share']):.1%}` of cached district noise."
        ),
        (
            f"- The flattest topic mix appears in "
            f"`{weakest_dominance['geography_value']}`, where the leading topic reaches only "
            f"`{float(weakest_dominance['dominant_share']):.1%}`."
        ),
        (
            f"- The full district layer contains `{missing_count}` no-data polygons that do not "
            "appear in the cached slice."
        ),
        "",
        "## Dominant Topic Map",
        "",
        f"![Dominant noise topic by community district](./figures/{map_image_path.name})",
        "",
        "## Party Music Intensity",
        "",
        f"![Party music intensity by district](./figures/{party_music_image_path.name})",
        "",
        "## Topic Mix Snapshot",
        "",
        f"![Topic mix for top sampled districts](./figures/{topic_mix_image_path.name})",
        "",
        "## District Metrics",
        "",
        "| District | Total complaints | Party music share | Dominant topic | Dominant share |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        "| "
        + " | ".join(
            [
                str(row["geography_value"]),
                str(int(row["geography_total_count"])),
                f"{float(row['party_music_share']):.1%}",
                format_topic_name(str(row["dominant_topic"])),
                f"{float(row['dominant_share']):.1%}",
            ]
        )
        + " |"
        for row in sorted(
            report_rows,
            key=lambda item: (
                -float(item["party_music_share"]),
                -int(item["geography_total_count"]),
                str(item["geography_value"]),
            ),
        )
    )
    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_file


def main() -> None:
    args = build_parser().parse_args()
    records, source, snapshot_path = load_records(args.refresh, args.app_token)
    if not records:
        raise RuntimeError(
            "The cached district choropleth slice did not return any records."
        )

    assignments = analysis.extract_topics(
        records,
        models.TopicQuery("Noise - Residential"),
    )
    summaries = analysis.aggregate_by_geography(
        assignments,
        geography="community_district",
    )
    dominant_summaries = [summary for summary in summaries if summary.is_dominant_topic]
    if not dominant_summaries:
        raise RuntimeError(
            "The cached district choropleth slice did not produce any community district summaries."
        )

    all_districts_gdf = spatial.load_boundaries_geodataframe(layer="community_district")
    borough_outlines = spatial.load_boundaries_geodataframe(layer="borough")
    dominant_map = spatial.summaries_to_geodataframe(
        dominant_summaries,
        boundaries_gdf=all_districts_gdf,
    )
    dominant_map["complaint_count"] = (
        dominant_map["complaint_count"].fillna(0).astype(int)
    )
    dominant_map["geography_total_count"] = (
        dominant_map["geography_total_count"].fillna(0).astype(int)
    )
    dominant_map["share_of_geography"] = dominant_map["share_of_geography"].fillna(0.0)

    snapshot_rows, topic_order = build_snapshot_rows(all_districts_gdf, summaries)
    all_summary_path = artifact_path("community-district-topic-summaries.csv")
    dominant_summary_path = artifact_path(
        "community-district-dominant-topic-summaries.csv"
    )
    export.export_topic_table(summaries, models.ExportTarget("csv", all_summary_path))
    export.export_topic_table(
        dominant_summaries,
        models.ExportTarget("csv", dominant_summary_path),
    )

    report_file: Path | None = None
    map_path: Path | None = None
    party_music_chart_path: Path | None = None
    topic_mix_chart_path: Path | None = None
    if args.publish_report:
        map_path = save_figure(
            build_map_figure(dominant_map, borough_outlines=borough_outlines),
            report_figure_path("community-district-dominant-noise-topics.png"),
        )
        party_music_chart_path = save_figure(
            build_party_music_intensity_figure(snapshot_rows),
            report_figure_path("community-district-party-music-intensity.png"),
        )
        topic_mix_chart_path = save_figure(
            build_topic_mix_figure(snapshot_rows, topic_order),
            report_figure_path("community-district-topic-mix-topn.png"),
        )
        report_file = write_report(
            source=source,
            snapshot_path=snapshot_path,
            records=records,
            snapshot_rows=snapshot_rows,
            map_image_path=map_path,
            party_music_image_path=party_music_chart_path,
            topic_mix_image_path=topic_mix_chart_path,
        )

    print("Community District Choropleth")
    print("-----------------------------")
    print(f"Record source: {source}")
    print(f"Cache path: {snapshot_path}")
    print(f"Loaded records: {len(records)}")
    print(f"Wrote scratch summary: {all_summary_path}")
    print(f"Wrote dominant-only summary: {dominant_summary_path}")
    if report_file is None:
        print(
            "Skipped tracked report generation. Re-run with --publish-report to update reports/."
        )
    else:
        print(f"Wrote tracked map: {map_path}")
        print(f"Wrote tracked party-music chart: {party_music_chart_path}")
        print(f"Wrote tracked topic-mix chart: {topic_mix_chart_path}")
        print(f"Wrote tracked report: {report_file}")
    print("Dominant topics by cached district slice")
    for row in sampled_snapshot_rows(snapshot_rows):
        print(
            f"- {row['geography_value']}: "
            f"{format_topic_name(str(row['dominant_topic']))} "
            f"({int(row['dominant_count'])}/{int(row['geography_total_count'])}, "
            f"{float(row['dominant_share']):.1%})"
        )


if __name__ == "__main__":
    main()
