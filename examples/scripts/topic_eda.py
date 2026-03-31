from __future__ import annotations

from datetime import date
from pathlib import Path

import nyc311


def main() -> None:
    records = nyc311.fetch_service_requests(
        filters=nyc311.ServiceRequestFilter(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            geography=nyc311.GeographyFilter("borough", nyc311.BOROUGH_BROOKLYN),
        ),
        socrata_config=nyc311.SocrataConfig(page_size=1000, max_pages=5),
    )

    records_df = nyc311.records_to_dataframe(records)
    complaint_distribution = (
        records_df["complaint_type"].value_counts().rename_axis("complaint_type").reset_index(name="count")
    )
    print("Complaint type distribution:")
    print(complaint_distribution.head(10).to_string(index=False))

    print("\nCoverage audit for built-in topic rules:")
    for complaint_type in nyc311.supported_topic_queries():
        coverage = nyc311.analyze_topic_coverage(
            records,
            nyc311.TopicQuery(complaint_type=complaint_type, top_n=10),
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
        nyc311.ServiceRequestRecord(
            service_request_id="demo-1",
            created_date=date(2025, 1, 1),
            complaint_type="Water System",
            descriptor="Low water pressure near hydrant",
            borough=nyc311.BOROUGH_BROOKLYN,
            community_district="01 BROOKLYN",
        ),
        nyc311.ServiceRequestRecord(
            service_request_id="demo-2",
            created_date=date(2025, 1, 2),
            complaint_type="Water System",
            descriptor="Leaking hydrant on corner",
            borough=nyc311.BOROUGH_BROOKLYN,
            community_district="01 BROOKLYN",
        ),
        nyc311.ServiceRequestRecord(
            service_request_id="demo-3",
            created_date=date(2025, 1, 3),
            complaint_type="Water System",
            descriptor="Pressure issue in building basement",
            borough=nyc311.BOROUGH_BROOKLYN,
            community_district="01 BROOKLYN",
        ),
    ]
    before_coverage = nyc311.analyze_topic_coverage(
        synthetic_records,
        nyc311.TopicQuery("Water System", top_n=10),
    )
    after_coverage = nyc311.analyze_topic_coverage(
        synthetic_records,
        nyc311.TopicQuery("Water System", top_n=10),
        custom_rules=custom_rules,
    )
    print("\nCustom rule demo for Water System:")
    print(f"- before custom rules: {before_coverage.coverage_rate:.1%} matched")
    print(f"- after custom rules:  {after_coverage.coverage_rate:.1%} matched")

    noise_assignments = nyc311.extract_topics(
        records,
        nyc311.TopicQuery("Noise - Residential", top_n=10),
    )
    noise_summaries = nyc311.aggregate_by_geography(
        noise_assignments,
        geography="community_district",
    )
    anomalies = nyc311.detect_anomalies(
        noise_summaries,
        nyc311.AnalysisWindow(days=30),
        z_threshold=1.5,
    )
    report_card_path = Path("examples/output/topic-eda-report.md")
    nyc311.export_report_card(
        {
            "topic_summaries": noise_summaries,
            "resolution_gaps": nyc311.analyze_resolution_gaps(
                records,
                [record for record in records if record.resolution_description is not None],
            ),
            "anomalies": anomalies,
        },
        nyc311.ExportTarget("md", report_card_path),
    )
    print(f"\nWrote report card to: {report_card_path}")


if __name__ == "__main__":
    main()
