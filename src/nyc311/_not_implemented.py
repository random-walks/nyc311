"""Shared placeholder utilities for scaffolded API surfaces."""

from __future__ import annotations

from typing import NoReturn


def planned_surface(name: str) -> NoReturn:
    """Raise a consistent error for scaffolded-but-unbuilt features."""
    raise NotImplementedError(
        f"{name} is part of the planned nyc311 surface but is not implemented yet."
    )
