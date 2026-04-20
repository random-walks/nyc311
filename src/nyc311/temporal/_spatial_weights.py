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

    Units within ``threshold_meters`` are neighbors, weighted by
    ``1 / distance``. The resulting matrix is symmetric before
    row-standardization.

    Args:
        unit_centroids: Mapping ``{unit_id: (latitude, longitude)}`` of
            unit centroids in WGS84 degrees.
        threshold_meters: Maximum great-circle distance, in meters, for
            two units to be considered neighbors.
        row_standardize: If ``True``, normalize each row of the resulting
            weights matrix to sum to ``1.0``.

    Returns:
        Nested dictionary ``{unit_a: {unit_b: weight}}``. Units with no
        neighbors map to an empty inner dict.
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
    """Convert a weights dict to a :class:`libpysal.weights.W` object.

    Args:
        weights: Nested dictionary ``{unit_a: {unit_b: weight}}`` as
            produced by :func:`build_distance_weights`.

    Returns:
        A ``libpysal.weights.W`` instance suitable for use with PySAL's
        spatial autocorrelation routines.

    Raises:
        ImportError: If libpysal is not installed. Install the optional
            stats extra with ``pip install nyc311[stats]``.
    """
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

    Computes a per-feature centroid as the mean of the exterior-ring
    coordinates. This is approximate but cheap and avoids a hard
    dependency on shapely.

    .. note::

        As of nyc-geo-toolkit v0.4.0,
        :func:`nyc_geo_toolkit.centroids_from_boundaries` is available
        as a shapely-backed, publication-grade centroid helper — it
        returns a :class:`BoundaryCollection` of GeoJSON ``Point``
        features at either the geometric centroid (default) or
        shapely's ``representative_point`` (guaranteed to lie inside
        concave polygons such as NYC's jagged community districts).
        Prefer it when you already have shapely installed and need
        defensible geometry for a published analysis.

        nyc311's helper is intentionally the **shapely-free** path
        (returns a plain ``dict[str, (lat, lon)]`` suitable for
        feeding directly into :func:`build_distance_weights`) and is
        preserved for workflows that need to stay on the lean base
        install. The two helpers return different shapes and slightly
        different numbers; don't swap them mid-analysis.

    Args:
        boundaries: A boundary collection exposing a ``features``
            iterable. Each feature must provide a ``geometry`` mapping
            with ``"type"`` (``"Polygon"`` or ``"MultiPolygon"``) and
            ``"coordinates"``, plus a ``geography_value`` attribute.

    Returns:
        Mapping ``{geography_value: (latitude, longitude)}`` for every
        feature whose exterior ring is non-empty.
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
