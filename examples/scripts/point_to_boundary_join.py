from __future__ import annotations

from pathlib import Path
import sys

import nyc311

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from examples.utils import data_path, output_path, print_lines, print_section  # noqa: E402


def main() -> None:
    records = nyc311.load_service_requests(data_path("service_requests_fixture.csv"))
    records_gdf = nyc311.records_to_geodataframe(records)
    boundaries_gdf = nyc311.load_boundaries_geodataframe(
        data_path("community_district_boundaries.geojson")
    )
    joined = nyc311.spatial_join_records_to_boundaries(records_gdf, boundaries_gdf)
    join_preview = joined[
        [
            "service_request_id",
            "complaint_type",
            "community_district",
            "boundary_geography_value",
            "descriptor",
        ]
    ]
    output_csv = output_path("point-boundary-join.csv")
    join_preview.to_csv(output_csv, index=False)

    matched_rows = join_preview["boundary_geography_value"].notna().sum()
    unmatched_rows = len(join_preview) - matched_rows
    print_section("Point-to-boundary join")
    print(f"Wrote join preview to: {output_csv}")
    print(f"Matched records: {matched_rows}")
    print(f"Unmatched records: {unmatched_rows}")
    print_lines(
        "First joined rows",
        [
            f"{row.service_request_id}: {row.community_district} -> "
            f"{row.boundary_geography_value}"
            for row in join_preview.head(5).itertuples(index=False)
        ],
    )


if __name__ == "__main__":
    main()
