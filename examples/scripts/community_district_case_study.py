from __future__ import annotations

from collections import Counter
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
        output=Path("examples/output/brooklyn-large-sample.csv"),
    )
    complaint_type_counts = Counter(record.complaint_type for record in records)
    district_counts = Counter(record.community_district for record in records)
    records_with_resolution = [
        record for record in records if record.resolution_description is not None
    ]
    resolution_summaries = nyc311.analyze_resolution_gaps(records, records_with_resolution)

    noise_records = [
        record
        for record in records
        if record.complaint_type == "Noise - Residential"
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
    output_path = Path("examples/output/brooklyn-noise-community-districts.csv")
    nyc311.export_topic_table(summaries, nyc311.ExportTarget("csv", output_path))

    print("Brooklyn exploratory data analysis")
    print(f"Loaded records: {len(records)}")
    print("Top complaint types:")
    for complaint_type, count in complaint_type_counts.most_common(5):
        print(f"  {complaint_type}: {count}")
    print("Top community districts by record volume:")
    for geography_value, count in district_counts.most_common(5):
        print(f"  {geography_value}: {count}")
    print("Highest unresolved-share complaint groups:")
    for summary in resolution_summaries[:5]:
        print(
            f"  {summary.geography_value} / {summary.complaint_type}: "
            f"{summary.unresolved_request_count}/{summary.total_request_count} unresolved"
        )
    print(f"Wrote summary to: {output_path}")
    print("Descriptor word-count distribution:")
    for word_count, count in sorted(descriptor_lengths.items()):
        print(f"  {word_count} words: {count} rows")
    print("Dominant Brooklyn noise topics by community district:")
    for row in dominant_topics:
        print(
            f"  {row.geography_value}: {row.topic} "
            f"({row.complaint_count}/{row.geography_total_count})"
        )


if __name__ == "__main__":
    main()
