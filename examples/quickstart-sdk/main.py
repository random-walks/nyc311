from __future__ import annotations

from pathlib import Path

from nyc311 import analysis, export, models, samples

ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = ROOT / "artifacts"
REPORTS_DIR = ROOT / "reports"


def artifact_path(filename: str) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    return ARTIFACTS_DIR / filename


def report_path(filename: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR / filename


def format_topic_name(value: str) -> str:
    return value.replace("_", " ").title()


def write_report(
    *,
    total_records: int,
    dominant_topics: list[models.GeographyTopicSummary],
) -> Path:
    report_file = report_path("quickstart-sdk-tearsheet.md")
    top_district = max(
        dominant_topics,
        key=lambda summary: (
            summary.geography_total_count,
            summary.complaint_count,
            summary.geography_value,
        ),
    )
    strongest_dominant = max(
        dominant_topics,
        key=lambda summary: (
            summary.share_of_geography,
            summary.complaint_count,
            summary.geography_value,
        ),
    )
    lines = [
        "# Quickstart SDK Tearsheet",
        "",
        "This tearsheet summarizes the smallest in-memory `nyc311` example over the",
        "packaged `Noise - Residential` sample.",
        "",
        "## Executive Summary",
        "",
        (
            f"- The quickstart loads `{total_records}` packaged sample records across "
            f"`{len(dominant_topics)}` community districts."
        ),
        (
            f"- The busiest sampled district is `{top_district.geography_value}` with "
            f"`{top_district.geography_total_count}` complaints."
        ),
        (
            f"- The strongest dominant topic signal appears in "
            f"`{strongest_dominant.geography_value}`, where "
            f"`{format_topic_name(strongest_dominant.topic)}` accounts for "
            f"`{strongest_dominant.share_of_geography:.1%}` of district complaints."
        ),
        "",
        "## Dominant Topics By District",
        "",
        "| District | Total complaints | Dominant topic | Dominant share |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(
        "| "
        + " | ".join(
            [
                summary.geography_value,
                str(summary.geography_total_count),
                format_topic_name(summary.topic),
                f"{summary.share_of_geography:.1%}",
            ]
        )
        + " |"
        for summary in sorted(
            dominant_topics,
            key=lambda item: (
                -item.geography_total_count,
                item.geography_value,
            ),
        )
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
        raise RuntimeError("The packaged sample slice did not return any records.")

    assignments = analysis.extract_topics(
        records,
        models.TopicQuery("Noise - Residential"),
    )
    summaries = analysis.aggregate_by_geography(
        assignments,
        geography="community_district",
    )

    output_path = artifact_path("quickstart-topics.csv")
    export.export_topic_table(
        summaries,
        models.ExportTarget("csv", output_path),
    )

    dominant_topics = [summary for summary in summaries if summary.is_dominant_topic]
    report_file = write_report(
        total_records=len(records),
        dominant_topics=dominant_topics,
    )
    print("Quickstart SDK")
    print("-------------")
    print(f"Loaded records: {len(records)}")
    print(f"Wrote CSV summary: {output_path}")
    print(f"Wrote tracked report: {report_file}")
    print(f"Dominant-topic rows: {len(dominant_topics)}")
    for summary in dominant_topics[:5]:
        print(
            f"- {summary.geography_value}: {format_topic_name(summary.topic)} "
            f"({summary.complaint_count}/{summary.geography_total_count})"
        )


if __name__ == "__main__":
    main()
