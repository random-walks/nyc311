from __future__ import annotations

from pathlib import Path

from nyc311 import analysis, export, models, samples

ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = ROOT / "artifacts"


def artifact_path(filename: str) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    return ARTIFACTS_DIR / filename


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
    print("Quickstart SDK")
    print("-------------")
    print(f"Loaded records: {len(records)}")
    print(f"Wrote CSV summary: {output_path}")
    print(f"Dominant-topic rows: {len(dominant_topics)}")
    for summary in dominant_topics[:5]:
        print(
            f"- {summary.geography_value}: {summary.topic} "
            f"({summary.complaint_count}/{summary.geography_total_count})"
        )


if __name__ == "__main__":
    main()
