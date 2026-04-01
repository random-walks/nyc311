from __future__ import annotations

from pathlib import Path

from nyc311 import plotting, samples, spatial

ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = ROOT / "artifacts"


def artifact_path(filename: str) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    return ARTIFACTS_DIR / filename


def save_figure(figure: object, filename: str) -> Path:
    output_path = artifact_path(filename)
    figure.tight_layout()
    figure.savefig(output_path, bbox_inches="tight", dpi=150)
    return output_path


def main() -> None:
    records = samples.load_sample_service_requests()
    sample_boundaries = samples.load_sample_boundaries("community_district")
    records_gdf = spatial.records_to_geodataframe(records)
    boundaries_gdf = spatial.load_boundaries_geodataframe(sample_boundaries)
    joined = spatial.spatial_join_records_to_boundaries(records_gdf, boundaries_gdf)

    join_preview = joined[
        [
            "service_request_id",
            "complaint_type",
            "community_district",
            "boundary_geography_value",
            "descriptor",
        ]
    ]
    output_csv = artifact_path("point-boundary-join.csv")
    join_preview.to_csv(output_csv, index=False)

    figure = plotting.plot_boundary_preview(
        boundaries_gdf,
        points_gdf=records_gdf,
        title="Point to boundary join preview",
    )
    preview_path = save_figure(figure, "point-boundary-preview.png")

    matched_rows = int(join_preview["boundary_geography_value"].notna().sum())
    unmatched_rows = len(join_preview) - matched_rows
    print("Point To Boundary Join")
    print("----------------------")
    print(f"Wrote CSV preview: {output_csv}")
    print(f"Wrote map preview: {preview_path}")
    print(f"Matched records: {matched_rows}")
    print(f"Unmatched records: {unmatched_rows}")


if __name__ == "__main__":
    main()
