"""Download Socrata 311 slices and packaged boundary layers into ``cache/``."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from urllib.request import urlopen

from nyc311 import geographies, io, models, presets

ALL_BOROUGHS = (
    "BRONX",
    "BROOKLYN",
    "MANHATTAN",
    "QUEENS",
    "STATEN ISLAND",
)
ALL_COMPLAINT_TYPES = models.supported_topic_queries()


def borough_slug(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def borough_cache_dir(cache_root: Path, borough: str) -> Path:
    return Path(cache_root) / "records" / borough_slug(borough)


def parse_borough_list(raw: str | None) -> tuple[str, ...]:
    if raw is None or not raw.strip():
        return ALL_BOROUGHS
    parts = tuple(p.strip().upper() for p in raw.split(",") if p.strip())
    for p in parts:
        if p not in ALL_BOROUGHS:
            raise ValueError(f"Unknown borough {p!r}. Expected one of {ALL_BOROUGHS}.")
    return parts


def parse_complaint_types(raw: str | None) -> tuple[str, ...]:
    if raw is None or not raw.strip():
        return ALL_COMPLAINT_TYPES
    parts = tuple(p.strip() for p in raw.split(",") if p.strip())
    for p in parts:
        if p not in ALL_COMPLAINT_TYPES:
            raise ValueError(
                f"Complaint type {p!r} is not in supported_topic_queries()."
            )
    return parts


def download_all_records(
    cache_root: Path,
    boroughs: tuple[str, ...],
    *,
    refresh: bool,
    app_token: str | None,
    start_date: date,
    end_date: date,
    page_size: int,
    max_records_per_borough: int | None,
) -> dict[str, Path]:
    """One cached CSV per borough (filtered query)."""
    cfg = presets.large_socrata_config(page_size=page_size, app_token=app_token)
    out: dict[str, Path] = {}
    for borough in boroughs:
        filt = models.ServiceRequestFilter(
            start_date=start_date,
            end_date=end_date,
            geography=models.GeographyFilter("borough", borough),
        )
        dest = borough_cache_dir(cache_root, borough)
        dest.mkdir(parents=True, exist_ok=True)
        path = io.cached_fetch(
            cfg,
            filt,
            cache_dir=dest,
            refresh=refresh,
            request_open=urlopen,
            max_records=max_records_per_borough,
        )
        out[borough] = path
    return out


def download_per_type_records(
    cache_root: Path,
    boroughs: tuple[str, ...],
    types: tuple[str, ...],
    *,
    refresh: bool,
    app_token: str | None,
    start_date: date,
    end_date: date,
    page_size: int,
    max_records_per_borough: int | None,
) -> dict[tuple[str, str], Path]:
    """Cached CSV per (borough, complaint type) pair."""
    cfg = presets.large_socrata_config(page_size=page_size, app_token=app_token)
    out: dict[tuple[str, str], Path] = {}
    for borough in boroughs:
        for ctype in types:
            filt = models.ServiceRequestFilter(
                start_date=start_date,
                end_date=end_date,
                geography=models.GeographyFilter("borough", borough),
                complaint_types=(ctype,),
            )
            dest = Path(cache_root) / "records_by_type" / borough_slug(borough)
            dest.mkdir(parents=True, exist_ok=True)
            path = io.cached_fetch(
                cfg,
                filt,
                cache_dir=dest,
                refresh=refresh,
                request_open=urlopen,
                max_records=max_records_per_borough,
            )
            out[(borough, ctype)] = path
    return out


def download_boundary_layers(
    cache_root: Path, *, refresh: bool
) -> dict[str, Path]:
    """Write packaged boundary layers as GeoJSON under ``cache/boundaries/``."""
    root = Path(cache_root) / "boundaries"
    root.mkdir(parents=True, exist_ok=True)
    layers: dict[str, str] = {
        "borough": "borough",
        "community_district": "community_district",
        "council_district": "council_district",
        "neighborhood_tabulation_area": "neighborhood_tabulation_area",
        "zcta": "zcta",
    }
    out: dict[str, Path] = {}
    for key, layer in layers.items():
        path = root / f"{key}.geojson"
        if path.is_file() and not refresh:
            out[key] = path
            continue
        collection = geographies.load_nyc_boundaries(layer)
        payload = geographies.boundaries_to_geojson(collection)
        path.write_text(json.dumps(payload), encoding="utf-8")
        out[key] = path

    tract_path = root / "census_tract.geojson"
    if not tract_path.is_file() or refresh:
        collection = geographies.load_nyc_census_tracts()
        tract_path.write_text(
            json.dumps(geographies.boundaries_to_geojson(collection)),
            encoding="utf-8",
        )
    out["census_tract"] = tract_path
    return out
