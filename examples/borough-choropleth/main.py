from __future__ import annotations

from pathlib import Path

from nyc311 import analysis, models, plotting, samples, spatial

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
    records = samples.load_sample_service_requests(
        filters=models.ServiceRequestFilter(
            complaint_types=("Noise - Residential",),
        )
    )
    assignments = analysis.extract_topics(
        records,
        models.TopicQuery("Noise - Residential"),
    )
    borough_summaries = analysis.aggregate_by_geography(
        assignments,
        geography="borough",
    )
    borough_map = spatial.summaries_to_geodataframe(
        borough_summaries,
        layer="borough",
    )
    dominant_map = borough_map[borough_map["is_dominant_topic"].fillna(False)].copy()
    if dominant_map.empty:
        raise RuntimeError("The packaged sample slice did not produce a borough map.")

    figure = plotting.plot_boundary_choropleth(
        dominant_map,
        column="topic",
        title="Dominant noise topics by borough (sample data)",
        cmap="tab20",
        categorical=True,
    )
    output_path = save_figure(figure, "borough-dominant-noise-topics.png")

    print("Borough Choropleth")
    print("------------------")
    print(f"Wrote map: {output_path}")
    for row in dominant_map.itertuples(index=False):
        print(f"- {row.geography_value}: {row.topic}")


if __name__ == "__main__":
    main()
