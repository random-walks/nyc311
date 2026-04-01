from __future__ import annotations

import argparse
import os
from collections import Counter
from pathlib import Path

from nyc311 import analysis, export, io, models, pipeline, presets

ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / "cache"
ARTIFACTS_DIR = ROOT / "artifacts"


def cache_path(filename: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / filename


def artifact_path(filename: str) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    return ARTIFACTS_DIR / filename


def print_section(title: str) -> None:
    print(title)
    print("-" * len(title))


def print_pairs(title: str, rows: list[tuple[str, int]]) -> None:
    print(title)
    for label, count in rows:
        print(f"- {label}: {count}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a Brooklyn community-district case study with local cache reuse.",
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
    snapshot_path = cache_path("brooklyn-case-study.csv")
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
        raise RuntimeError("The case-study slice did not return any records.")

    complaint_type_counts = Counter(record.complaint_type for record in records)
    district_counts = Counter(record.community_district for record in records)
    resolution_records = [
        record for record in records if record.resolution_description is not None
    ]
    resolution_summaries = analysis.analyze_resolution_gaps(records, resolution_records)

    noise_records = [
        record for record in records if record.complaint_type == "Noise - Residential"
    ]
    if not noise_records:
        raise RuntimeError("The case-study slice did not contain Noise - Residential rows.")

    assignments = analysis.extract_topics(
        noise_records,
        models.TopicQuery("Noise - Residential"),
    )
    summaries = analysis.aggregate_by_geography(
        assignments,
        geography="community_district",
    )
    output_path = artifact_path("brooklyn-noise-community-districts.csv")
    export.export_topic_table(
        summaries,
        models.ExportTarget("csv", output_path),
    )

    dominant_topics = [summary for summary in summaries if summary.is_dominant_topic]
    print_section("Community District Case Study")
    print(f"Record source: {source}")
    print(f"Loaded records: {len(records)}")
    print_pairs("Top complaint types", complaint_type_counts.most_common(5))
    print_pairs("Top districts by volume", district_counts.most_common(5))
    print("Highest unresolved-share complaint groups")
    for summary in resolution_summaries[:5]:
        print(
            f"- {summary.geography_value} / {summary.complaint_type}: "
            f"{summary.unresolved_request_count}/{summary.total_request_count} unresolved"
        )
    print(f"Wrote topic summary: {output_path}")
    print("Dominant Brooklyn noise topics by district")
    for summary in dominant_topics[:10]:
        print(
            f"- {summary.geography_value}: {summary.topic} "
            f"({summary.complaint_count}/{summary.geography_total_count})"
        )


if __name__ == "__main__":
    main()
