from __future__ import annotations

from datetime import date
from pathlib import Path

import nyc311


def main() -> None:
    records = nyc311.fetch_service_requests(
        filters=nyc311.ServiceRequestFilter(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            geography=nyc311.GeographyFilter("borough", nyc311.BOROUGH_BROOKLYN),
            complaint_types=("Noise - Residential",),
        ),
        socrata_config=nyc311.SocrataConfig(page_size=250, max_pages=1),
    )
    assignments = nyc311.extract_topics(
        records,
        nyc311.TopicQuery("Noise - Residential"),
    )
    summaries = nyc311.aggregate_by_geography(
        assignments,
        geography="community_district",
    )
    output_path = Path("examples/output/quickstart-topics.csv")
    nyc311.export_topic_table(
        summaries,
        nyc311.ExportTarget("csv", output_path),
    )

    dominant_topics = [row for row in summaries if row.is_dominant_topic]
    print(f"Fetched records: {len(records)}")
    print(f"Wrote {output_path}")
    print(f"Dominant-topic rows: {len(dominant_topics)}")
    for row in dominant_topics[:3]:
        print(
            f"{row.geography_value}: {row.topic} "
            f"({row.complaint_count}/{row.geography_total_count})"
        )


if __name__ == "__main__":
    main()
