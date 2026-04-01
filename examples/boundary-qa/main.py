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
    boundaries_gdf = spatial.load_boundaries_geodataframe(sample_boundaries)
    points_gdf = spatial.records_to_geodataframe(records)
    joined = geographies.spatially_enrich_records(records, boundaries=sample_boundaries)

    boundary_summary = boundaries_gdf.assign(
        geometry_type=boundaries_gdf.geometry.geom_type,
    )[["geography", "geography_value", "geometry_type"]]
    summary_path = artifact_path("boundary-summary.csv")
    boundary_summary.to_csv(summary_path, index=False)

    figure = plotting.plot_boundary_preview(
        boundaries_gdf,
        points_gdf=points_gdf,
        title="Community district boundaries and joined points",
    )
    preview_path = save_figure(figure, "boundary-preview.png")

    join_coverage = float(joined["boundary_geography_value"].notna().mean())
    print("Boundary QA")
    print("-----------")
    print(f"Wrote boundary summary: {summary_path}")
    print(f"Wrote preview map: {preview_path}")
    print(f"Join coverage: {join_coverage:.1%}")
    for row in boundary_summary.itertuples(index=False):
        print(f"- {row.geography_value}: {row.geometry_type}")


if __name__ == "__main__":
    main()
