from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from nyc311 import analysis, dataframes, export, models, pipeline

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from examples.utils import (  # noqa: E402
    brooklyn_borough_filter,
    brooklyn_socrata_config,
    output_path,
    print_section,
)


def main() -> None:
    records = pipeline.fetch_service_requests(
        filters=brooklyn_borough_filter(
            start_date="2025-01-01",
            end_date="2025-03-31",
        ),
        socrata_config=brooklyn_socrata_config(page_size=1000, max_pages=5),
    )

    records_df = dataframes.records_to_dataframe(records)
    complaint_distribution = (
        records_df["complaint_type"]
        .value_counts()
        .rename_axis("complaint_type")
        .reset_index(name="count")
    )
    print("Complaint type distribution:")
    print(complaint_distribution.head(10).to_string(index=False))

    print("\nCoverage audit for built-in topic rules:")
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
        if coverage.top_unmatched_descriptors:
            print("  top unmatched descriptors:")
            for descriptor, count in coverage.top_unmatched_descriptors[:3]:
                print(f"    - {descriptor}: {count}")

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
    print("\nCustom rule demo for Water System:")
    print(f"- before custom rules: {before_coverage.coverage_rate:.1%} matched")
    print(f"- after custom rules:  {after_coverage.coverage_rate:.1%} matched")

    noise_assignments = analysis.extract_topics(
        records,
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
    report_card_path = output_path("topic-eda-report.md")
    export.export_report_card(
        {
            "topic_summaries": noise_summaries,
            "resolution_gaps": analysis.analyze_resolution_gaps(
                records,
                [
                    record
                    for record in records
                    if record.resolution_description is not None
                ],
            ),
            "anomalies": anomalies,
        },
        models.ExportTarget("md", report_card_path),
    )
    print_section("Topic EDA")
    print(f"\nWrote report card to: {report_card_path}")


if __name__ == "__main__":
    main()
