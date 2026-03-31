"""Helpers for accessing packaged NYC geography resources."""

from __future__ import annotations

import json
from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any
from collections.abc import Iterator

from .catalog import BOUNDARY_LAYER_LOOKUP
from .normalize import normalize_boundary_layer

_RESOURCE_ROOT = files("nyc311.geographies")


def load_boundary_payload(layer: str) -> dict[str, Any]:
    """Load the packaged GeoJSON payload for one canonical boundary layer."""
    normalized_layer = normalize_boundary_layer(layer)
    spec = BOUNDARY_LAYER_LOOKUP[normalized_layer]
    payload = json.loads(
        _RESOURCE_ROOT.joinpath(spec.resource_path).read_text(encoding="utf-8")
    )
    if not isinstance(payload, dict):
        raise ValueError("Packaged boundary payload must be a GeoJSON object.")
    return payload


def load_sample_boundary_values() -> dict[str, tuple[str, ...]]:
    """Load packaged boundary values tied to the sample service-request slice."""
    payload = json.loads(
        _RESOURCE_ROOT.joinpath("data/samples/boundary_values.json").read_text(
            encoding="utf-8"
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("Sample boundary-values payload must be a JSON object.")
    return {
        str(layer): tuple(str(value) for value in values)
        for layer, values in payload.items()
        if isinstance(values, list)
    }


@contextmanager
def sample_service_request_path() -> Iterator[Path]:
    """Yield a local filesystem path for the packaged sample service-request CSV."""
    with as_file(
        _RESOURCE_ROOT.joinpath("data/samples/service_requests_fixture.csv")
    ) as sample_path:
        yield sample_path
