"""Composable factor pipeline for NYC 311 complaint analysis.

The factor pipeline is an immutable, composable system for computing
domain-specific metrics over geographic units.  Each :class:`Factor`
computes a single value from a :class:`FactorContext`, and a
:class:`Pipeline` executes multiple factors in a single pass over a
sequence of contexts.

Ported from the ``subway-access`` factor architecture and adapted for
311 complaint data, where each context represents an aggregated set of
complaints within a geographic unit and time window.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from nyc311.models import ServiceRequestRecord


@dataclass(frozen=True, slots=True)
class FactorContext:
    """Row-level context for factor computation.

    Each context represents one geographic unit (community district, NTA,
    borough) over one time window.  Factors compute a single value from
    this context.
    """

    geography: str
    geography_value: str
    complaints: tuple[ServiceRequestRecord, ...]
    time_window_start: date
    time_window_end: date
    total_population: int | None = None
    extras: dict[str, Any] | None = None


class Factor(ABC):
    """Abstract base for a single named computation over a FactorContext."""

    name: str
    dtype: Literal["float", "str", "bool", "int"]

    @abstractmethod
    def compute(self, context: FactorContext) -> float | str | bool | int:
        """Return the computed value for *context*."""


class Pipeline:
    """Immutable builder that executes factors over contexts.

    ``Pipeline`` never mutates in place: :meth:`add` returns a **new**
    pipeline with the factor appended.
    """

    __slots__ = ("_factors",)

    def __init__(self, factors: tuple[Factor, ...] = ()) -> None:
        self._factors = factors

    def add(self, factor: Factor) -> Pipeline:
        """Return a new pipeline with ``factor`` appended.

        Args:
            factor: The factor to append. Must define a unique ``name``.

        Returns:
            A new :class:`Pipeline` whose ``factors`` tuple ends with
            ``factor``. The receiver is left unmodified.
        """
        return Pipeline((*self._factors, factor))

    @property
    def factors(self) -> tuple[Factor, ...]:
        """The ordered factors in this pipeline."""
        return self._factors

    def as_factor_factory_estimate(
        self,
        panel: Any,
        *,
        family: str = "did",
        method: str = "twfe",
        outcome: str | None = None,
        **engine_kwargs: Any,
    ) -> Any:
        """Run a factor-factory engine on ``panel`` as a Pipeline continuation.

        Additive bridge: the pipeline itself is not executed here.
        Instead, the call dispatches into
        ``factor_factory.engines.<family>.estimate``, returning a
        factor-factory ``<Family>Results`` object that downstream code
        can chain off.

        Args:
            panel: A :class:`factor_factory.tidy.Panel`. Typically
                produced by
                :meth:`nyc311.temporal.PanelDataset.to_factor_factory_panel`.
            family: Engine-family module name under
                ``factor_factory.engines``. Defaults to ``"did"``.
            method: Registry key for a specific adapter inside the
                family (e.g. ``"twfe"``, ``"cs"``). Defaults to
                ``"twfe"``.
            outcome: Outcome column on the Panel. When ``None``, the
                engine falls back to ``panel.outcome_col``.
            **engine_kwargs: Additional kwargs forwarded to the engine's
                ``estimate`` dispatcher.

        Returns:
            A factor-factory ``<Family>Results`` object.

        Raises:
            ImportError: If factor-factory is not installed or the
                requested engine family's optional dependencies are
                missing.
        """
        from nyc311.factors._factor_factory import dispatch_factor_factory_engine

        return dispatch_factor_factory_engine(
            panel,
            family=family,
            method=method,
            outcome=outcome,
            **engine_kwargs,
        )

    def run(self, contexts: Iterable[FactorContext]) -> PipelineResult:
        """Execute all factors across ``contexts`` and return results.

        Iterates over each context once and evaluates every factor against
        it, producing a columnar :class:`PipelineResult` keyed by factor
        name.

        Args:
            contexts: An iterable of :class:`FactorContext` instances. Each
                context corresponds to one geographic-unit / time-window
                row in the final result.

        Returns:
            A :class:`PipelineResult` whose ``columns`` map factor names to
            value tuples and whose ``geography_ids`` tuple aligns with
            those columns positionally.
        """
        context_list = list(contexts)
        geography_ids: list[str] = []
        columns: dict[str, list[Any]] = {f.name: [] for f in self._factors}

        for ctx in context_list:
            geography_ids.append(ctx.geography_value)
            for factor in self._factors:
                columns[factor.name].append(factor.compute(ctx))

        return PipelineResult(
            columns={name: tuple(values) for name, values in columns.items()},
            geography_ids=tuple(geography_ids),
        )


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Columnar result set produced by :meth:`Pipeline.run`."""

    columns: dict[str, tuple[Any, ...]]
    geography_ids: tuple[str, ...]

    def to_records(self) -> tuple[dict[str, Any], ...]:
        """Convert to a tuple of row dictionaries.

        Returns:
            A tuple where each element is a dict containing
            ``geography_id`` plus one key per factor in the pipeline. The
            row order matches :attr:`geography_ids`.
        """
        records: list[dict[str, Any]] = []
        for i, geography_id in enumerate(self.geography_ids):
            row: dict[str, Any] = {"geography_id": geography_id}
            for col_name, values in self.columns.items():
                row[col_name] = values[i]
            records.append(row)
        return tuple(records)

    def to_dataframe(self) -> Any:
        """Convert to a pandas DataFrame indexed by ``geography_id``.

        Returns:
            A ``pandas.DataFrame`` with one row per geographic unit and
            one column per factor, indexed by ``geography_id``.

        Raises:
            ImportError: If pandas is not installed. Install the optional
                dataframes extra with ``pip install nyc311[dataframes]``.
        """
        try:
            import pandas as pd
        except ImportError as exc:
            message = (
                "pandas is required for to_dataframe(). "
                "Install it with: pip install nyc311[dataframes]"
            )
            raise ImportError(message) from exc

        data: dict[str, Any] = {"geography_id": self.geography_ids, **self.columns}
        return pd.DataFrame(data).set_index("geography_id")
