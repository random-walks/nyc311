from __future__ import annotations

import sys
from pathlib import Path

import nyc311

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from examples.utils import (  # noqa: E402
    brooklyn_borough_filter,
    brooklyn_socrata_config,
    output_path,
    print_lines,
    print_section,
)


def main() -> None:
    records = nyc311.fetch_service_requests(
        filters=brooklyn_borough_filter(
            start_date="2025-01-01",
            end_date="2025-01-31",
            complaint_types=("Noise - Residential",),
        ),
        socrata_config=brooklyn_socrata_config(page_size=250, max_pages=1),
    )
    assignments = nyc311.extract_topics(
        records,
        nyc311.TopicQuery("Noise - Residential"),
    )
    summaries = nyc311.aggregate_by_geography(
        assignments,
        geography="community_district",
    )
    target_path = output_path("quickstart-topics.csv")
    nyc311.export_topic_table(
        summaries,
        nyc311.ExportTarget("csv", target_path),
    )

    dominant_topics = [row for row in summaries if row.is_dominant_topic]
    print_section("SDK quickstart")
    print(f"Fetched records: {len(records)}")
    print(f"Wrote {target_path}")
    print(f"Dominant-topic rows: {len(dominant_topics)}")
    print_lines(
        "Dominant topics",
        [
            f"{row.geography_value}: {row.topic} "
            f"({row.complaint_count}/{row.geography_total_count})"
            for row in dominant_topics[:3]
        ],
    )


if __name__ == "__main__":
    main()
