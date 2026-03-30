from __future__ import annotations

import importlib.metadata

import nyc311 as m


def test_version() -> None:
    assert importlib.metadata.version("nyc311") == m.__version__
