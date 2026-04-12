"""Distance-based spatial weights for panel analysis."""

from __future__ import annotations

from typing import Any

from nyc_geo_toolkit import haversine_distance_meters


def build_distance_weights(
    unit_centroids: dict[str, tuple[float, float]],
    *,
    threshold_meters: float = 2000.0,
    row_standardize: bool = True,
) -> dict[str, dict[str, float]]:
    """Build an inverse-distance spatial weights matrix.

    Units within *threshold_meters* are neighbors, weighted by ``1 / distance``.
    The matrix is symmetric.

    Parameters
    ----------
    unit_centroids:
        ``{unit_id: (latitude, longitude)}`` centroids.
    threshold_meters:
        Maximum distance for two units to be neighbors.
    row_standardize:
        If ``True``, normalize each row to sum to ``1.0``.

    Returns
    -------
    dict[str, dict[str, float]]
        Nested dictionary ``{unit_a: {unit_b: weight}}``.
    """
    unit_ids = sorted(unit_centroids)
    raw: dict[str, dict[str, float]] = {uid: {} for uid in unit_ids}

    for i, uid_a in enumerate(unit_ids):
        lat_a, lon_a = unit_centroids[uid_a]
        for uid_b in unit_ids[i + 1 :]:
            lat_b, lon_b = unit_centroids[uid_b]
            dist = haversine_distance_meters(
                latitude_a=lat_a,
                longitude_a=lon_a,
                latitude_b=lat_b,
                longitude_b=lon_b,
            )
            if 0 < dist <= threshold_meters:
                w = 1.0 / dist
                raw[uid_a][uid_b] = w
                raw[uid_b][uid_a] = w

    if row_standardize:
        for uid in unit_ids:
            row_sum = sum(raw[uid].values())
            if row_sum > 0:
                raw[uid] = {nb: w / row_sum for nb, w in raw[uid].items()}

    return raw


def weights_to_pysal(weights: dict[str, dict[str, float]]) -> Any:
    """Convert a weights dict to a :class:`libpysal.weights.W` object."""
    try:
        from libpysal.weights import W
    except ImportError as exc:
        message = (
            "libpysal is required for spatial weights. "
            "Install with: pip install nyc311[stats]"
        )
        raise ImportError(message) from exc

    neighbors = {uid: list(nbrs) for uid, nbrs in weights.items()}
    weight_values = {uid: list(nbrs.values()) for uid, nbrs in weights.items()}
    return W(neighbors, weight_values)


def centroids_from_boundaries(boundaries: Any) -> dict[str, tuple[float, float]]:
    """Extract centroids from a :class:`BoundaryCollection`.

    Computes the centroid as the mean of the exterior ring coordinates for
    each boundary feature.
    """
    centroids: dict[str, tuple[float, float]] = {}
    for feature in boundaries.features:
        coords = feature.geometry.get("coordinates", [])
        if not coords:
            continue
        ring = coords[0] if feature.geometry.get("type") == "Polygon" else coords[0][0]
        if not ring:
            continue
        lons = [pt[0] for pt in ring]
        lats = [pt[1] for pt in ring]
        centroids[feature.geography_value] = (
            sum(lats) / len(lats),
            sum(lons) / len(lons),
        )
    return centroids
