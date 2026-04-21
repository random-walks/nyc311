"""Optional geospatial helpers built on top of the typed nyc311 models.

The `nyc311.spatial` module is the GeoDataFrame-flavoured sibling of
`nyc311.geographies` — it loads boundary layers and records as
geopandas frames, spatially joins records to boundaries, and
materialises typed summaries as map-ready GeoDataFrames.

.. note::

   For **polygon-centroid points** (distance-band spatial weights,
   Moran's *I* / LISA, nearest-neighbour joins, choropleth label
   placement), nyc311 deliberately does **not** ship a centroid
   helper in this module. Use upstream instead:

   .. code-block:: python

       from nyc_geo_toolkit import (
           centroids_from_boundaries,
           load_nyc_boundaries,
       )

       cbs = load_nyc_boundaries("community_district")
       # representative=True keeps the point inside the polygon —
       # matters for non-convex NYC shorelines.
       points = centroids_from_boundaries(cbs, representative=True)

   Shipped as a first-class helper in nyc-geo-toolkit v0.4.0 (on
   PyPI as v0.4.1 since 2026-04-21). Requires the ``[spatial]``
   extra on nyc-geo-toolkit for the shapely dependency. See also
   :func:`nyc311.temporal.centroids_from_boundaries`, which returns
   a shapely-free ``dict[str, (lat, lon)]`` suitable for direct
   use with :func:`nyc311.temporal.build_distance_weights`.
"""

from __future__ import annotations

from ._boundaries import load_boundaries_geodataframe
from ._joins import spatial_join_records_to_boundaries
from ._points import records_to_geodataframe
from ._summaries import summaries_to_geodataframe

__all__ = [
    "load_boundaries_geodataframe",
    "records_to_geodataframe",
    "spatial_join_records_to_boundaries",
    "summaries_to_geodataframe",
]
