"""Thin bridge from :class:`nyc311.factors.Pipeline` to factor-factory engines.

The bridge is additive: :class:`Pipeline` and its factors are unchanged
and continue to work without factor-factory installed. The bridge only
fires when a caller invokes
:meth:`Pipeline.as_factor_factory_estimate`.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import factor_factory.tidy as ff_tidy


_SUPPORTED_FAMILIES: tuple[str, ...] = (
    "did",
    "sdid",
    "mediation",
    "rdd",
    "scm",
    "changepoint",
    "stl",
    "panel_reg",
    "inequality",
    "spatial",
    "reporting_bias",
    "hawkes",
    "survival",
    "event_study",
    "het_te",
    "dml",
    "climate",
    "diffusion",
)


def dispatch_factor_factory_engine(
    panel: ff_tidy.Panel,
    *,
    family: str = "did",
    method: str = "twfe",
    outcome: str | None = None,
    **engine_kwargs: Any,
) -> Any:
    """Call ``factor_factory.engines.<family>.estimate`` on ``panel``.

    This is the chaining target behind
    :meth:`nyc311.factors.Pipeline.as_factor_factory_estimate`. It
    lazily imports the requested engine family so callers don't pay the
    import cost for families they don't use, and it raises a friendly
    :class:`ImportError` when the family's optional dependencies are
    missing.

    Args:
        panel: A :class:`factor_factory.tidy.Panel`. Typically produced
            by :meth:`nyc311.temporal.PanelDataset.to_factor_factory_panel`.
        family: Engine-family module name under
            ``factor_factory.engines``. One of :data:`_SUPPORTED_FAMILIES`.
        method: Registry key for a specific adapter inside the family.
            For example, ``"twfe"`` / ``"cs"`` / ``"sa"`` / ``"bjs"`` for
            ``family="did"``.
        outcome: Outcome column on the Panel. When ``None``, the engine
            falls back to ``panel.outcome_col`` (the primary outcome
            declared in :class:`PanelMetadata`).
        **engine_kwargs: Additional keyword arguments forwarded to the
            engine's ``estimate`` dispatcher.

    Returns:
        The factor-factory ``<Family>Results`` object the engine
        returned. Its :meth:`summary_table` method produces a
        ``pandas.DataFrame`` summary.

    Raises:
        ValueError: If ``family`` is not in :data:`_SUPPORTED_FAMILIES`.
        ImportError: If factor-factory is not installed or the requested
            engine family's optional dependencies are missing.
    """
    if family not in _SUPPORTED_FAMILIES:
        message = (
            f"Unknown factor-factory engine family {family!r}. "
            f"Supported: {_SUPPORTED_FAMILIES}"
        )
        raise ValueError(message)

    module_name = f"factor_factory.engines.{family}"
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        message = (
            f"Could not import {module_name}. Install factor-factory "
            f"with: pip install nyc311 (or pip install factor-factory)."
        )
        raise ImportError(message) from exc

    estimate = module.estimate
    return estimate(
        panel,
        methods=(method,),
        outcome=outcome,
        **engine_kwargs,
    )


__all__ = ["dispatch_factor_factory_engine"]
