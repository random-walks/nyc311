from __future__ import annotations

from pathlib import Path

from nyc311 import geographies, plotting, samples, spatial

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
    joined = geographies.spatially_enrich_records(records, boundaries=sample_boundaries)

    comparison = (
        joined.dropna(subset=["boundary_geography_value"])
        .groupby(["boundary_geography_value", "complaint_type"])
        .size()
        .rename("count")
        .reset_index()
        .sort_values(["boundary_geography_value", "count"], ascending=[True, False])
    )
    output_csv = artifact_path("spatial-topic-comparison.csv")
    comparison.to_csv(output_csv, index=False)

    figure = plotting.plot_boundary_preview(
        boundaries_gdf,
        points_gdf=records_gdf,
        title="Joined service-request points by community district",
    )
    preview_path = save_figure(figure, "spatial-topic-comparison-preview.png")

    print("Spatial Topic Comparison")
    print("------------------------")
    print(f"Wrote grouped comparison: {output_csv}")
    print(f"Wrote preview map: {preview_path}")
    for row in comparison.head(10).itertuples(index=False):
        print(
            f"- {row.boundary_geography_value}: {row.complaint_type} "
            f"({row.count})"
        )


if __name__ == "__main__":
    main()
