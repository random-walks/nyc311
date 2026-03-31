from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys

import nyc311

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from examples.utils import (  # noqa: E402
    brooklyn_borough_filter,
    brooklyn_socrata_config,
    output_path,
    print_counter,
    print_lines,
    print_section,
)


def main() -> None:
    records = nyc311.fetch_service_requests(
        filters=brooklyn_borough_filter(
            start_date="2025-01-01",
            end_date="2025-03-31",
        ),
        socrata_config=brooklyn_socrata_config(page_size=1000, max_pages=5),
        output=output_path("brooklyn-large-sample.csv"),
    )
    complaint_type_counts = Counter(record.complaint_type for record in records)
    district_counts = Counter(record.community_district for record in records)
    records_with_resolution = [
        record for record in records if record.resolution_description is not None
    ]
    resolution_summaries = nyc311.analyze_resolution_gaps(
        records, records_with_resolution
    )

    noise_records = [
        record for record in records if record.complaint_type == "Noise - Residential"
    ]
    assignments = nyc311.extract_topics(
        noise_records,
        nyc311.TopicQuery("Noise - Residential"),
    )
    summaries = nyc311.aggregate_by_geography(
        assignments,
        geography="community_district",
    )

    descriptor_lengths = Counter(len(record.descriptor.split()) for record in records)
    dominant_topics = [row for row in summaries if row.is_dominant_topic]
    target_path = output_path("brooklyn-noise-community-districts.csv")
    nyc311.export_topic_table(summaries, nyc311.ExportTarget("csv", target_path))

    print_section("Brooklyn exploratory data analysis")
    print(f"Loaded records: {len(records)}")
    print_counter("Top complaint types", complaint_type_counts.most_common(5))
    print_counter("Top community districts by record volume", district_counts.most_common(5))
    print_lines(
        "Highest unresolved-share complaint groups",
        [
            f"{summary.geography_value} / {summary.complaint_type}: "
            f"{summary.unresolved_request_count}/{summary.total_request_count} unresolved"
            for summary in resolution_summaries[:5]
        ],
    )
    print(f"Wrote summary to: {target_path}")
    print_counter("Descriptor word-count distribution", sorted(descriptor_lengths.items()))
    print_lines(
        "Dominant Brooklyn noise topics by community district",
        [
            f"{row.geography_value}: {row.topic} "
            f"({row.complaint_count}/{row.geography_total_count})"
            for row in dominant_topics
        ],
    )


if __name__ == "__main__":
    main()
