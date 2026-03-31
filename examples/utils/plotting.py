"""Optional matplotlib helpers for example plots."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from .paths import output_path


def require_matplotlib() -> Any:
    """Import matplotlib on demand for plotting examples."""
    try:
        return import_module("matplotlib.pyplot")
    except ImportError as exc:  # pragma: no cover - optional dependency path
        raise ImportError(
            "matplotlib is required for plotting examples. "
            "Install it with `pip install nyc311[plotting]`, "
            "`pip install nyc311[science]`, or `pip install matplotlib`."
        ) from exc


def configure_matplotlib_style() -> Any:
    """Apply a consistent plot style for examples and return pyplot."""
    plt = require_matplotlib()
    plt.style.use("ggplot")
    return plt


def save_current_figure(filename: str, figure: Any | None = None) -> Any:
    """Save a matplotlib figure into the shared examples output directory."""
    plt = require_matplotlib()
    target = output_path(filename)
    active_figure = figure or plt.gcf()
    active_figure.tight_layout()
    active_figure.savefig(target, bbox_inches="tight", dpi=150)
    return target
