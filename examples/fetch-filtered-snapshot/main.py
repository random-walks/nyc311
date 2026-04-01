from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path

from nyc311 import io, models, pipeline, presets

ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / "cache"
ARTIFACTS_DIR = ROOT / "artifacts"
REPORTS_DIR = ROOT / "reports"


def cache_path(filename: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / filename


def artifact_path(filename: str) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    return ARTIFACTS_DIR / filename


def report_path(filename: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR / filename


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch a filtered NYC 311 slice into this example's local cache.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=cache_path("rodent-snapshot.csv"),
        help="Where to store the local CSV snapshot.",
    )
    parser.add_argument(
        "--complaint-type",
        action="append",
        default=[],
        help="Optional complaint type filter. Repeat to include more than one value.",
    )
    parser.add_argument("--start-date", default="2025-01-01")
    parser.add_argument("--end-date", default="2025-01-31")
    parser.add_argument(
        "--geography",
        default="borough",
        choices=("borough", "community_district"),
    )
    parser.add_argument("--geography-value", default=models.BOROUGH_BROOKLYN)
    parser.add_argument("--page-size", type=int, default=500)
    parser.add_argument("--max-pages", type=int, default=1)
    parser.add_argument(
        "--app-token",
        default=os.getenv("NYC_OPEN_DATA_APP_TOKEN"),
        help="Optional Socrata app token. Falls back to NYC_OPEN_DATA_APP_TOKEN.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Ignore any existing cache file and fetch a fresh live slice.",
    )
    parser.add_argument(
        "--publish-report",
        action="store_true",
        help="Write a tracked tearsheet for the current pinned snapshot.",
    )
    return parser


def load_records(
    args: argparse.Namespace,
) -> tuple[list[models.ServiceRequestRecord], str, tuple[str, ...]]:
    output_path = args.output
    complaint_types = tuple(args.complaint_type or ["Rodent"])
    if output_path.exists() and not args.refresh:
        return io.load_service_requests(output_path), "cache", complaint_types

    filters = presets.build_filter(
        start_date=args.start_date,
        end_date=args.end_date,
        geography=args.geography,
        geography_value=args.geography_value,
        complaint_types=complaint_types,
    )
    config = presets.small_socrata_config(
        app_token=args.app_token,
        page_size=args.page_size,
        max_pages=args.max_pages,
    )
    records = pipeline.fetch_service_requests(
        filters=filters,
        socrata_config=config,
        output=output_path,
    )
    return records, "live fetch", complaint_types


def build_next_step_command(
    *,
    snapshot_path: Path,
    complaint_types: tuple[str, ...],
) -> str:
    primary_complaint_type = complaint_types[0]
    return (
        "nyc311 topics "
        f"--source {snapshot_path} "
        f'--complaint-type "{primary_complaint_type}" '
        "--geography community_district "
        "--output artifacts/topic-summary.csv"
    )


def write_metadata_json(metadata: dict[str, object]) -> Path:
    output_path = artifact_path("fetch-metadata.json")
    output_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def write_fetch_summary(
    *,
    metadata: dict[str, object],
    complaint_rows: list[tuple[str, int]],
    next_step_command: str,
) -> Path:
    output_path = artifact_path("fetch-summary.md")
    total_rows = int(metadata["row_count"])
    lines = [
        "# Fetch Summary",
        "",
        "## Snapshot",
        "",
        f"- Source: `{metadata['record_source']}`",
        f"- Output path: `{metadata['output_path']}`",
        f"- Row count: `{total_rows}`",
        f"- Date range: `{metadata['start_date']}` to `{metadata['end_date']}`",
        f"- Geography filter: `{metadata['geography']} = {metadata['geography_value']}`",
        (
            "- Complaint filters: "
            + ", ".join(f"`{value}`" for value in metadata["complaint_types"])
        ),
        "",
        "## Complaint Mix",
        "",
        "| Complaint type | Count | Share |",
        "| --- | --- | --- |",
    ]
    for complaint_type, count in complaint_rows:
        share = 0 if total_rows == 0 else count / total_rows
        lines.append(f"| {complaint_type} | {count} | {share:.1%} |")
    lines.extend(
        [
            "",
            "## Recommended Next Step",
            "",
            "```bash",
            next_step_command,
            "```",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def write_report(
    *,
    metadata: dict[str, object],
    complaint_rows: list[tuple[str, int]],
    next_step_command: str,
) -> Path:
    output_path = report_path("fetch-filtered-snapshot-tearsheet.md")
    total_rows = int(metadata["row_count"])
    top_complaint_type, top_count = complaint_rows[0]
    top_share = 0 if total_rows == 0 else top_count / total_rows
    lines = [
        "# Fetch Filtered Snapshot Tearsheet",
        "",
        "This tearsheet documents the current pinned snapshot for the fetch-first",
        "consumer workflow. Regenerate it only when you intentionally want to",
        "update the tracked snapshot description.",
        "",
        "## Executive Summary",
        "",
        f"- Snapshot source: `{metadata['record_source']}`.",
        f"- Saved rows: `{total_rows}` at `{metadata['output_path']}`.",
        (
            f"- Primary complaint mix leader: `{top_complaint_type}` with `{top_count}` rows "
            f"({top_share:.1%})."
        ),
        (
            f"- Applied filters: `{metadata['geography']} = {metadata['geography_value']}`, "
            f"`{metadata['start_date']}` to `{metadata['end_date']}`, complaint types "
            + ", ".join(f"`{value}`" for value in metadata["complaint_types"])
            + "."
        ),
        "",
        "## Complaint Mix",
        "",
        "| Complaint type | Count | Share |",
        "| --- | --- | --- |",
    ]
    for complaint_type, count in complaint_rows:
        share = 0 if total_rows == 0 else count / total_rows
        lines.append(f"| {complaint_type} | {count} | {share:.1%} |")
    lines.extend(
        [
            "",
            "## Next Step",
            "",
            "```bash",
            next_step_command,
            "```",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    records, source, complaint_types = load_records(args)
    complaint_counts = Counter(record.complaint_type for record in records)
    complaint_rows = complaint_counts.most_common() or [(complaint_types[0], 0)]
    next_step_command = build_next_step_command(
        snapshot_path=args.output,
        complaint_types=complaint_types,
    )
    metadata = {
        "record_source": source,
        "row_count": len(records),
        "output_path": str(args.output),
        "start_date": args.start_date,
        "end_date": args.end_date,
        "geography": args.geography,
        "geography_value": args.geography_value,
        "complaint_types": list(complaint_types),
        "page_size": args.page_size,
        "max_pages": args.max_pages,
        "refresh_requested": args.refresh,
        "publish_report_requested": args.publish_report,
    }
    metadata_path = write_metadata_json(metadata)
    summary_path = write_fetch_summary(
        metadata=metadata,
        complaint_rows=complaint_rows,
        next_step_command=next_step_command,
    )
    report_file: Path | None = None
    if args.publish_report:
        report_file = write_report(
            metadata=metadata,
            complaint_rows=complaint_rows,
            next_step_command=next_step_command,
        )

    print("Fetch Filtered Snapshot")
    print("-----------------------")
    print(f"Record source: {source}")
    print(f"Rows available in memory: {len(records)}")
    print(f"Snapshot path: {args.output}")
    print(f"Wrote fetch metadata: {metadata_path}")
    print(f"Wrote fetch summary: {summary_path}")
    print("Complaint mix")
    for complaint_type, count in complaint_rows[:5]:
        share = 0 if not records else count / len(records)
        print(f"- {complaint_type}: {count} ({share:.1%})")
    print("Recommended next step")
    print(f"- {next_step_command}")
    if report_file is None:
        print("Skipped tracked report generation. Re-run with --publish-report to update reports/.")
    else:
        print(f"Wrote tracked report: {report_file}")


if __name__ == "__main__":
    main()
