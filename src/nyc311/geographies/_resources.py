"""Helpers for accessing nyc311 sample geography resources."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path

_RESOURCE_ROOT = files("nyc311.geographies")


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
