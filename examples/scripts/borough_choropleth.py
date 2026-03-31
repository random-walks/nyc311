from __future__ import annotations

from pathlib import Path
import sys

import nyc311

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from examples.utils import (  # noqa: E402
    data_path,
    merge_summary_map,
    print_lines,
    print_section,
    save_choropleth,
)


def main() -> None:
    records = nyc311.load_service_requests(data_path("service_requests_fixture.csv"))
    assignments = nyc311.extract_topics(
        records,
        nyc311.TopicQuery("Noise - Residential"),
    )
    borough_summaries = nyc311.aggregate_by_geography(assignments, geography="borough")
    borough_map = merge_summary_map(
        borough_summaries,
        boundaries_source=data_path("borough_boundaries.geojson"),
    )
    dominant_borough_map = borough_map[
        borough_map["is_dominant_topic"].fillna(False)
    ].copy()
    map_path = save_choropleth(
        dominant_borough_map,
        column="topic",
        title="Dominant noise topics by borough (demo data)",
        filename="borough-dominant-noise-topics.png",
        cmap="tab20",
        categorical=True,
    )

    print_section("Borough choropleth")
    print(f"Wrote map to: {map_path}")
    print_lines(
        "Dominant topics by borough",
        [
            f"{row.geography_value}: {row.topic}"
            for row in dominant_borough_map.itertuples(index=False)
        ],
    )


if __name__ == "__main__":
    main()
