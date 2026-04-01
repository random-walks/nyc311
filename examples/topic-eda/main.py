from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path

from nyc311 import analysis, dataframes, export, io, models, pipeline, presets

ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / "cache"
ARTIFACTS_DIR = ROOT / "artifacts"


def cache_path(filename: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / filename


def artifact_path(filename: str) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    return ARTIFACTS_DIR / filename


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
        "--app-token",
        default=os.getenv("NYC_OPEN_DATA_APP_TOKEN"),
        help="Optional Socrata app token. Falls back to NYC_OPEN_DATA_APP_TOKEN.",
    )
    return parser


def load_records(refresh: bool, app_token: str | None) -> tuple[list[models.ServiceRequestRecord], str]:
    snapshot_path = cache_path("topic-eda-snapshot.csv")
    if snapshot_path.exists() and not refresh:
        return io.load_service_requests(snapshot_path), "cache"

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
    return records, "live fetch"


def main() -> None:
    args = build_parser().parse_args()
    records, source = load_records(args.refresh, args.app_token)
    if not records:
        raise RuntimeError("The topic EDA slice did not return any records.")

    records_df = dataframes.records_to_dataframe(records)
    complaint_distribution = (
        records_df["complaint_type"]
        .value_counts()
        .rename_axis("complaint_type")
        .reset_index(name="count")
    )

    print("Topic EDA")
    print("---------")
    print(f"Record source: {source}")
    print("Complaint type distribution")
    print(complaint_distribution.head(10).to_string(index=False))

    print("\nCoverage audit for built-in topic rules")
    for complaint_type in models.supported_topic_queries():
        coverage = analysis.analyze_topic_coverage(
            records,
            models.TopicQuery(complaint_type=complaint_type, top_n=10),
        )
        print(
            f"- {coverage.complaint_type}: "
            f"{coverage.matched_records}/{coverage.total_records} matched "
            f"({coverage.coverage_rate:.1%})"
        )
        for descriptor, count in coverage.top_unmatched_descriptors[:3]:
            print(f"  top unmatched -> {descriptor}: {count}")

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
    print("\nCustom rule demo for Water System")
    print(f"- before custom rules: {before_coverage.coverage_rate:.1%} matched")
    print(f"- after custom rules:  {after_coverage.coverage_rate:.1%} matched")

    noise_records = [
        record for record in records if record.complaint_type == "Noise - Residential"
    ]
    if not noise_records:
        raise RuntimeError("The topic EDA slice did not contain Noise - Residential rows.")

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
    report_card_path = artifact_path("topic-eda-report.md")
    export.export_report_card(
        {
            "topic_summaries": noise_summaries,
            "resolution_gaps": analysis.analyze_resolution_gaps(
                records,
                resolution_records,
            ),
            "anomalies": anomalies,
        },
        models.ExportTarget("md", report_card_path),
    )
    print(f"\nWrote report card: {report_card_path}")


if __name__ == "__main__":
    main()
