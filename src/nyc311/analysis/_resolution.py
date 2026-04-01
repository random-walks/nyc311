"""Resolution-gap analysis helpers."""

from __future__ import annotations

from collections import defaultdict

from ..models import ResolutionGapSummary, ServiceRequestRecord


def analyze_resolution_gaps(
    service_requests: list[ServiceRequestRecord],
    resolution_data: list[ServiceRequestRecord],
) -> list[ResolutionGapSummary]:
    """Summarize unresolved complaint share by borough and complaint type."""
    if not service_requests:
        return []

    resolved_request_ids = {
        record.service_request_id
        for record in resolution_data
        if record.resolution_description is not None
    }
    grouped_totals: dict[tuple[str, str], int] = defaultdict(int)
    grouped_resolved: dict[tuple[str, str], int] = defaultdict(int)

    for record in service_requests:
        grouping_key = (record.borough, record.complaint_type)
        grouped_totals[grouping_key] += 1
        if (
            record.resolution_description is not None
            or record.service_request_id in resolved_request_ids
        ):
            grouped_resolved[grouping_key] += 1

    summaries: list[ResolutionGapSummary] = []
    for (borough, complaint_type), total_request_count in sorted(
        grouped_totals.items()
    ):
        resolved_request_count = grouped_resolved[(borough, complaint_type)]
        unresolved_request_count = total_request_count - resolved_request_count
        summaries.append(
            ResolutionGapSummary(
                geography="borough",
                geography_value=borough,
                complaint_type=complaint_type,
                total_request_count=total_request_count,
                resolved_request_count=resolved_request_count,
                unresolved_request_count=unresolved_request_count,
                unresolved_share=unresolved_request_count / total_request_count,
                resolution_rate=resolved_request_count / total_request_count,
            )
        )

    return sorted(
        summaries,
        key=lambda summary: (
            -summary.unresolved_share,
            -summary.total_request_count,
            summary.geography_value,
            summary.complaint_type,
        ),
    )
