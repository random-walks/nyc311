from __future__ import annotations

from collections import Counter
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


def format_borough_name(value: str) -> str:
    return value.title()


def format_topic_name(value: str | None) -> str:
    if not isinstance(value, str) or not value:
        return "No sample data"
    return value.replace("_", " ").title()


def format_borough_list(values: list[str]) -> str:
    if not values:
        return "none"
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return f"{', '.join(values[:-1])}, and {values[-1]}"


def sampled_snapshot_rows(snapshot_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        row
        for row in snapshot_rows
        if int(row["geography_total_count"]) > 0
    ]


def build_report_rows() -> tuple[
    list[models.ServiceRequestRecord],
    list[models.GeographyTopicSummary],
    list[models.GeographyTopicSummary],
    object,
    list[dict[str, object]],
    list[str],
]:
    records = samples.load_sample_service_requests(
        filters=models.ServiceRequestFilter(
            complaint_types=("Noise - Residential",),
        )
    )
    if not records:
        raise RuntimeError("The packaged sample slice did not return any records.")

    assignments = analysis.extract_topics(
        records,
        models.TopicQuery("Noise - Residential"),
    )
    borough_summaries = analysis.aggregate_by_geography(
        assignments,
        geography="borough",
    )
    dominant_summaries = [
        summary for summary in borough_summaries if summary.is_dominant_topic
    ]
    if not dominant_summaries:
        raise RuntimeError(
            "The packaged sample slice did not produce any dominant borough summaries."
        )

    all_boroughs = spatial.load_boundaries_geodataframe(layer="borough")
    dominant_map = spatial.summaries_to_geodataframe(
        dominant_summaries,
        boundaries_gdf=all_boroughs,
    )
    dominant_map["complaint_count"] = dominant_map["complaint_count"].fillna(0).astype(int)
    dominant_map["geography_total_count"] = dominant_map["geography_total_count"].fillna(0).astype(int)
    dominant_map["share_of_geography"] = dominant_map["share_of_geography"].fillna(0.0)

    topic_totals = Counter(summary.topic for summary in borough_summaries)
    topic_order = sorted(
        topic_totals,
        key=lambda topic: (topic != "party_music", -topic_totals[topic], topic),
    )
    summaries_by_borough: dict[str, list[models.GeographyTopicSummary]] = {}
    for summary in borough_summaries:
        summaries_by_borough.setdefault(summary.geography_value, []).append(summary)

    snapshot_rows: list[dict[str, object]] = []
    for row in all_boroughs[["geography_value"]].itertuples(index=False):
        borough = str(row.geography_value)
        borough_rows = sorted(
            summaries_by_borough.get(borough, []),
            key=lambda summary: (summary.topic_rank, summary.topic),
        )
        total_count = borough_rows[0].geography_total_count if borough_rows else 0
        dominant_row = next(
            (summary for summary in borough_rows if summary.is_dominant_topic),
            None,
        )
        party_music_row = next(
            (summary for summary in borough_rows if summary.topic == "party_music"),
            None,
        )
        topic_shares = {summary.topic: summary.share_of_geography for summary in borough_rows}
        topic_counts = {summary.topic: summary.complaint_count for summary in borough_rows}
        snapshot_rows.append(
            {
                "geography_value": borough,
                "geography_total_count": total_count,
                "dominant_topic": dominant_row.topic if dominant_row is not None else None,
                "dominant_count": dominant_row.complaint_count if dominant_row is not None else 0,
                "dominant_share": dominant_row.share_of_geography if dominant_row is not None else 0.0,
                "party_music_count": party_music_row.complaint_count if party_music_row is not None else 0,
                "party_music_share": party_music_row.share_of_geography if party_music_row is not None else 0.0,
                "topic_shares": topic_shares,
                "topic_counts": topic_counts,
            }
        )

    return (
        records,
        borough_summaries,
        dominant_summaries,
        dominant_map,
        snapshot_rows,
        topic_order,
    )


def write_csv_artifacts(
    borough_summaries: list[models.GeographyTopicSummary],
    dominant_summaries: list[models.GeographyTopicSummary],
) -> tuple[Path, Path]:
    all_summary_path = artifact_path("borough-topic-summaries.csv")
    dominant_summary_path = artifact_path("borough-dominant-topic-summaries.csv")
    export.export_topic_table(
        borough_summaries,
        models.ExportTarget("csv", all_summary_path),
    )
    export.export_topic_table(
        dominant_summaries,
        models.ExportTarget("csv", dominant_summary_path),
    )
    return all_summary_path, dominant_summary_path


def build_map_figure(dominant_map: object) -> object:
    figure = plotting.plot_boundary_choropleth(
        dominant_map,
        column="topic",
        title="Dominant noise topic by borough",
        cmap="Set2",
        categorical=True,
        figsize=(9, 8),
    )
    axes = figure.axes[0]
    legend = axes.get_legend()
    if legend is not None:
        legend.set_title("Dominant topic")

    sampled_rows = dominant_map[dominant_map["complaint_count"] > 0]
    for row in sampled_rows.itertuples(index=False):
        point = row.geometry.representative_point()
        axes.text(
            point.x,
            point.y,
            (
                f"{format_borough_name(row.geography_value)}\n"
                f"{format_topic_name(row.topic)}\n"
                f"{row.complaint_count}/{row.geography_total_count} ({row.share_of_geography:.0%})"
            ),
            ha="center",
            va="center",
            fontsize=8,
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": "white",
                "edgecolor": "#374151",
                "alpha": 0.9,
            },
        )
    return figure


def build_party_music_intensity_figure(snapshot_rows: list[dict[str, object]]) -> object:
    plt = require_matplotlib()
    percent_formatter = import_module("matplotlib.ticker").PercentFormatter
    plot_rows = sorted(
        sampled_snapshot_rows(snapshot_rows),
        key=lambda row: (
            -float(row["party_music_share"]),
            -int(row["geography_total_count"]),
            str(row["geography_value"]),
        ),
    )
    figure, axes = plt.subplots(figsize=(8, 4.8))
    bars = axes.barh(
        [format_borough_name(str(row["geography_value"])) for row in plot_rows],
        [float(row["party_music_share"]) for row in plot_rows],
        color=[
            "#7c3aed" if float(row["party_music_share"]) > 0 else "#cbd5e1"
            for row in plot_rows
        ],
    )
    axes.invert_yaxis()
    axes.set_xlim(0, 1)
    axes.set_xlabel("Party music share of sampled borough complaints")
    axes.set_title("Who parties the hardest in the packaged sample?")
    axes.xaxis.set_major_formatter(percent_formatter(xmax=1))
    axes.grid(axis="x", alpha=0.25)

    for bar, row in zip(bars, plot_rows, strict=True):
        count = int(row["party_music_count"])
        total = int(row["geography_total_count"])
        axes.text(
            bar.get_width() + 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"{bar.get_width():.1%} ({count}/{total})",
            ha="left",
            va="center",
            fontsize=8,
        )
    return figure


def build_topic_mix_facets_figure(
    snapshot_rows: list[dict[str, object]],
    topic_order: list[str],
) -> object:
    plt = require_matplotlib()
    percent_formatter = import_module("matplotlib.ticker").PercentFormatter
    sampled_rows = sorted(
        sampled_snapshot_rows(snapshot_rows),
        key=lambda row: (
            -float(row["party_music_share"]),
            -int(row["geography_total_count"]),
            str(row["geography_value"]),
        ),
    )
    figure, axes = plt.subplots(
        1,
        len(sampled_rows),
        figsize=(4.4 * len(sampled_rows), 4.8),
        sharey=True,
    )
    axes_list = [axes] if len(sampled_rows) == 1 else list(axes)
    colormap = require_matplotlib().get_cmap("Set2", len(topic_order))
    topic_colors = {
        topic: (
            "#7c3aed"
            if topic == "party_music"
            else colormap(index)
        )
        for index, topic in enumerate(topic_order)
    }

    for axis, row in zip(axes_list, sampled_rows, strict=True):
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
            f"{format_borough_name(str(row['geography_value']))}\n"
            f"n={int(row['geography_total_count'])}"
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
    axes_list[0].set_ylabel("Share of borough complaints")
    figure.suptitle("Normalized topic mix by borough", y=1.02)
    return figure


def write_report(
    *,
    records: list[models.ServiceRequestRecord],
    snapshot_rows: list[dict[str, object]],
    map_image_path: Path,
    party_music_image_path: Path,
    topic_mix_image_path: Path,
) -> Path:
    report_file = report_path("borough-choropleth-tearsheet.md")
    report_rows = sorted(
        snapshot_rows,
        key=lambda row: (
            -float(row["party_music_share"]),
            -int(row["geography_total_count"]),
            str(row["geography_value"]),
        ),
    )
    sampled_rows = sampled_snapshot_rows(report_rows)
    missing_boroughs = [
        format_borough_name(str(row["geography_value"]))
        for row in report_rows
        if int(row["geography_total_count"]) == 0
    ]
    top_party_share = max(float(row["party_music_share"]) for row in sampled_rows)
    top_party_rows = [
        row for row in sampled_rows if float(row["party_music_share"]) == top_party_share
    ]
    bottom_party_share = min(float(row["party_music_share"]) for row in sampled_rows)
    bottom_party_rows = [
        row for row in sampled_rows if float(row["party_music_share"]) == bottom_party_share
    ]
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
        "# Borough Choropleth Tearsheet",
        "",
        "This tearsheet summarizes the packaged `Noise - Residential` sample at the",
        "borough level. All shares are normalized within borough and should be read",
        "as sample intensity, not citywide prevalence.",
        "",
        "## Executive Summary",
        "",
        (
            f"- The packaged sample contains `{len(records)}` noise complaints across "
            f"`{len(sampled_rows)}` boroughs."
        ),
        (
            f"- {format_borough_list([format_borough_name(str(row['geography_value'])) for row in top_party_rows])} "
            f"shows the strongest party-music intensity at `{top_party_share:.1%}` "
            f"({int(top_party_rows[0]['party_music_count'])} of "
            f"{int(top_party_rows[0]['geography_total_count'])} complaints)."
        ),
        (
            f"- {format_borough_list([format_borough_name(str(row['geography_value'])) for row in bottom_party_rows])} "
            f"shows the weakest party-music intensity at `{bottom_party_share:.1%}` "
            f"({int(bottom_party_rows[0]['party_music_count'])} of "
            f"{int(bottom_party_rows[0]['geography_total_count'])} complaints)."
        ),
        (
            f"- The sharpest single-topic signal appears in "
            f"`{format_borough_name(str(strongest_dominance['geography_value']))}`, "
            f"where `{format_topic_name(strongest_dominance['dominant_topic'])}` accounts for "
            f"`{float(strongest_dominance['dominant_share']):.1%}` "
            f"({int(strongest_dominance['dominant_count'])} of "
            f"{int(strongest_dominance['geography_total_count'])})."
        ),
        (
            f"- The flattest topic mix appears in "
            f"`{format_borough_name(str(weakest_dominance['geography_value']))}`, "
            f"where the leading topic accounts for only "
            f"`{float(weakest_dominance['dominant_share']):.1%}` "
            f"({int(weakest_dominance['dominant_count'])} of "
            f"{int(weakest_dominance['geography_total_count'])})."
        ),
        (
            f"- No sample records are available for `{format_borough_list(missing_boroughs)}`."
            if missing_boroughs
            else "- All boroughs appear in the packaged sample."
        ),
        "",
        "## Borough Dominant Topic Map",
        "",
        f"![Dominant noise topics by borough](./figures/{map_image_path.name})",
        "",
        "## Party Music Intensity",
        "",
        f"![Party music intensity by borough](./figures/{party_music_image_path.name})",
        "",
        "## Topic Mix By Borough",
        "",
        f"![Normalized topic mix by borough](./figures/{topic_mix_image_path.name})",
        "",
        "## Borough Metrics",
        "",
        "| Borough | Total complaints | Party music count | Party music share | Dominant topic | Dominant share |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report_rows:
        party_share_text = (
            "n/a"
            if int(row["geography_total_count"]) == 0
            else f"{float(row['party_music_share']):.1%}"
        )
        dominant_share_text = (
            "n/a"
            if int(row["geography_total_count"]) == 0
            else f"{float(row['dominant_share']):.1%}"
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    format_borough_name(str(row["geography_value"])),
                    str(int(row["geography_total_count"])),
                    str(int(row["party_music_count"])),
                    party_share_text,
                    format_topic_name(row["dominant_topic"]),
                    dominant_share_text,
                ]
            )
            + " |"
        )
    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_file


def main() -> None:
    (
        records,
        borough_summaries,
        dominant_summaries,
        dominant_map,
        snapshot_rows,
        topic_order,
    ) = build_report_rows()
    all_summary_path, dominant_summary_path = write_csv_artifacts(
        borough_summaries,
        dominant_summaries,
    )
    map_path = save_figure(
        build_map_figure(dominant_map),
        report_figure_path("borough-dominant-noise-topics.png"),
    )
    party_music_chart_path = save_figure(
        build_party_music_intensity_figure(snapshot_rows),
        report_figure_path("borough-party-music-intensity.png"),
    )
    topic_mix_chart_path = save_figure(
        build_topic_mix_facets_figure(snapshot_rows, topic_order),
        report_figure_path("borough-topic-mix-facets.png"),
    )
    report_file = write_report(
        records=records,
        snapshot_rows=snapshot_rows,
        map_image_path=map_path,
        party_music_image_path=party_music_chart_path,
        topic_mix_image_path=topic_mix_chart_path,
    )

    print("Borough Choropleth")
    print("------------------")
    print(f"Wrote scratch summary: {all_summary_path}")
    print(f"Wrote dominant-only summary: {dominant_summary_path}")
    print(f"Wrote tracked map: {map_path}")
    print(f"Wrote tracked party-music chart: {party_music_chart_path}")
    print(f"Wrote tracked topic-mix chart: {topic_mix_chart_path}")
    print(f"Wrote tracked report: {report_file}")
    print("Dominant topics by borough")
    for row in snapshot_rows:
        borough_name = format_borough_name(str(row["geography_value"]))
        if int(row["geography_total_count"]) == 0:
            print(f"- {borough_name}: no sample data")
            continue
        print(
            f"- {borough_name}: "
            f"{format_topic_name(row['dominant_topic'])} "
            f"({int(row['dominant_count'])}/{int(row['geography_total_count'])}, "
            f"{float(row['dominant_share']):.1%})"
        )


if __name__ == "__main__":
    main()
